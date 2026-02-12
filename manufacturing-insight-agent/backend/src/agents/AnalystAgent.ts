/**
 * ANALYST AGENT - MANUFACTURING DATA ANALYSIS
 *
 * Handles COMPLEX queries requiring:
 * - Root cause analysis
 * - Recommendations for improvement
 * - Trend interpretation
 * - Equipment comparison
 *
 * Uses external prompt file: prompts/analyst_agent.md
 */

import { AnalystResult, KpiResult } from "../types";
import { callClaudeForText } from "../core/bedrockClient";
import { logAgentStep } from "../core/telemetryStore";
import { getManufacturingDataRepository } from "../dataAccess/ManufacturingDataRepository";
import { getConversationHistory } from "./SupervisorAgent";
import { loadPrompt, injectVariables, PROMPTS } from "../prompts";

export interface AnalystAgentResult {
  analystResult: AnalystResult;
  generatedSql: string;
}

type QuestionIntent =
  | 'YIELD_ANALYSIS'
  | 'EQUIPMENT_ANALYSIS'
  | 'QUALITY_ISSUES'
  | 'TREND_ANALYSIS'
  | 'IMPROVEMENT_RECO'
  | 'ROOT_CAUSE'
  | 'GENERAL_OVERVIEW';

interface QuestionClassification {
  intent: QuestionIntent;
  focusAreas: string[];
}

function classifyQuestion(userQuery: string, conversationHistory: { role: string; content: string }[]): QuestionClassification {
  const lowerQuery = userQuery.toLowerCase();
  const hasHistory = conversationHistory.length > 0;
  const previousTopics = conversationHistory.map(h => h.content.toLowerCase()).join(' ');

  if (/\b(improve|recommend|fix|should we|what can we do|how do we|how can we)\b/.test(lowerQuery)) {
    const focusAreas: string[] = [];
    if (lowerQuery.includes('yield') || previousTopics.includes('yield')) focusAreas.push('yield');
    if (lowerQuery.includes('oee') || previousTopics.includes('oee')) focusAreas.push('oee');
    if (lowerQuery.includes('rft') || previousTopics.includes('rft')) focusAreas.push('rft');
    if (lowerQuery.includes('quality') || lowerQuery.includes('reject') || previousTopics.includes('reject')) focusAreas.push('quality');
    return { intent: 'IMPROVEMENT_RECO', focusAreas: focusAreas.length > 0 ? focusAreas : ['yield', 'quality'] };
  }

  if (/\b(why|cause|reason|root cause)\b/.test(lowerQuery)) {
    const focusAreas: string[] = [];
    if (lowerQuery.includes('yield') || lowerQuery.includes('low')) focusAreas.push('yield');
    if (lowerQuery.includes('reject') || lowerQuery.includes('fail')) focusAreas.push('quality');
    if (lowerQuery.includes('deviation')) focusAreas.push('deviations');
    if (lowerQuery.includes('rft')) focusAreas.push('rft');
    return { intent: 'ROOT_CAUSE', focusAreas: focusAreas.length > 0 ? focusAreas : ['yield'] };
  }

  if (/\byield\b/.test(lowerQuery)) {
    return { intent: 'YIELD_ANALYSIS', focusAreas: ['yield'] };
  }

  if (/\b(equipment|machine|reactor|vial|tab|coat)\b/.test(lowerQuery)) {
    return { intent: 'EQUIPMENT_ANALYSIS', focusAreas: ['equipment'] };
  }

  if (/\b(reject|deviation|quality|rework|quarantine|rft)\b/.test(lowerQuery)) {
    return { intent: 'QUALITY_ISSUES', focusAreas: ['quality', 'deviations'] };
  }

  if (/\b(trend|over time|week|month|compare|historical)\b/.test(lowerQuery)) {
    return { intent: 'TREND_ANALYSIS', focusAreas: ['trends'] };
  }

  if (hasHistory && userQuery.length < 50) {
    if (previousTopics.includes('yield')) return { intent: 'IMPROVEMENT_RECO', focusAreas: ['yield'] };
    if (previousTopics.includes('oee')) return { intent: 'IMPROVEMENT_RECO', focusAreas: ['oee'] };
    if (previousTopics.includes('reject') || previousTopics.includes('quality')) {
      return { intent: 'IMPROVEMENT_RECO', focusAreas: ['quality'] };
    }
  }

  return { intent: 'GENERAL_OVERVIEW', focusAreas: ['overview'] };
}

export async function analyzeComplexQuery(
  sessionId: string,
  userQuery: string
): Promise<AnalystAgentResult> {
  const repo = getManufacturingDataRepository();
  const conversationHistory = getConversationHistory(sessionId);
  const classification = classifyQuestion(userQuery, conversationHistory);

  await logAgentStep({
    sessionId,
    agentName: "Analyst",
    inputSummary: userQuery,
    outputSummary: `Question classified as: ${classification.intent}`,
    reasoningSummary: `Focus areas: ${classification.focusAreas.join(', ')}`,
    status: "success",
  });

  // Get all batch data
  const allBatches = repo.getBatches();
  const totalBatches = allBatches.length;

  // Calculate statistics
  const avgYield = allBatches.reduce((sum, b) => sum + Number(b.yield_pct), 0) / totalBatches;
  const releasedBatches = allBatches.filter(b => b.status === 'Released');
  const rejectedBatches = allBatches.filter(b => b.status === 'Rejected');
  const quarantinedBatches = allBatches.filter(b => b.status === 'Quarantined');
  const lowYieldBatches = allBatches.filter(b => Number(b.yield_pct) < 95);
  const batchesWithDeviations = allBatches.filter(b => Number(b.deviations_count) > 0);

  // Equipment statistics
  const equipmentStats: Record<string, { count: number; avgYield: number; rejectCount: number; deviations: number; yields: number[] }> = {};
  allBatches.forEach(b => {
    const eq = b.primary_equipment_id || 'Unknown';
    if (!equipmentStats[eq]) equipmentStats[eq] = { count: 0, avgYield: 0, rejectCount: 0, deviations: 0, yields: [] };
    equipmentStats[eq].count++;
    equipmentStats[eq].yields.push(Number(b.yield_pct));
    equipmentStats[eq].deviations += Number(b.deviations_count) || 0;
    if (b.status === 'Rejected') equipmentStats[eq].rejectCount++;
  });
  Object.keys(equipmentStats).forEach(eq => {
    const yields = equipmentStats[eq].yields;
    equipmentStats[eq].avgYield = yields.reduce((a, b) => a + b, 0) / yields.length;
  });

  const sortedByYield = Object.entries(equipmentStats).sort((a, b) => a[1].avgYield - b[1].avgYield);
  const worstEquipment = sortedByYield.slice(0, 3);
  const bestEquipment = sortedByYield.slice(-3).reverse();

  let analysisContext = "";
  let supportingResults: KpiResult[] = [];
  let generatedSql = "";

  switch (classification.intent) {
    case 'YIELD_ANALYSIS':
    case 'ROOT_CAUSE': {
      analysisContext = `
YIELD ANALYSIS DATA:
- Overall Average Yield: ${avgYield.toFixed(1)}% (Target: 98%)
- Gap to Target: ${(98 - avgYield).toFixed(1)}%
- Low Yield Batches (<95%): ${lowYieldBatches.length} out of ${totalBatches} (${((lowYieldBatches.length/totalBatches)*100).toFixed(1)}%)

Equipment Contributing to Low Yield:
${worstEquipment.map(([eq, stats]) =>
  `- ${eq}: ${stats.avgYield.toFixed(1)}% yield, ${stats.count} batches, ${stats.rejectCount} rejections`
).join('\n')}

Best Performing Equipment:
${bestEquipment.map(([eq, stats]) =>
  `- ${eq}: ${stats.avgYield.toFixed(1)}% yield, ${stats.count} batches`
).join('\n')}

Root Cause Indicators:
- ${rejectedBatches.length} batches rejected (${((rejectedBatches.length/totalBatches)*100).toFixed(1)}%)
- ${batchesWithDeviations.length} batches had deviations
- Equipment ${worstEquipment[0]?.[0]} shows lowest yield at ${worstEquipment[0]?.[1].avgYield.toFixed(1)}%`;

      // TABLE: Show key metrics summary with Overall first
      supportingResults = [{
        kpiName: "yield_summary",
        breakdownBy: "status",
        dataPoints: [
          { label: "Overall Yield", value: Math.round(avgYield * 10) / 10 },
          { label: "Target", value: 98 },
          { label: "Gap to Target", value: Math.round((98 - avgYield) * 10) / 10 },
          { label: "Low Yield Batches", value: lowYieldBatches.length },
          { label: "Rejected Batches", value: rejectedBatches.length },
        ],
        explanation: "Yield performance summary"
      }];

      generatedSql = `-- Yield Analysis
SELECT
    'Overall' as category,
    COUNT(*) as total_batches,
    AVG(yield_pct) as avg_yield,
    SUM(CASE WHEN yield_pct < 95 THEN 1 ELSE 0 END) as low_yield_count,
    SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END) as rejected_count
FROM MES_PASX_BATCHES;`;
      break;
    }

    case 'QUALITY_ISSUES': {
      const deviationsByEquipment: Record<string, number> = {};
      batchesWithDeviations.forEach(b => {
        const eq = b.primary_equipment_id || 'Unknown';
        deviationsByEquipment[eq] = (deviationsByEquipment[eq] || 0) + Number(b.deviations_count);
      });

      analysisContext = `
QUALITY ANALYSIS DATA:
- Total Batches: ${totalBatches}
- Released: ${releasedBatches.length} (${((releasedBatches.length/totalBatches)*100).toFixed(1)}%)
- Rejected: ${rejectedBatches.length} (${((rejectedBatches.length/totalBatches)*100).toFixed(1)}%)
- Quarantined: ${quarantinedBatches.length} (${((quarantinedBatches.length/totalBatches)*100).toFixed(1)}%)
- Batches with Deviations: ${batchesWithDeviations.length}

Rejected Batch Details:
${rejectedBatches.slice(0, 5).map(b =>
  `- ${b.batch_id}: Yield ${Number(b.yield_pct).toFixed(1)}%, Equipment: ${b.primary_equipment_id}, Deviations: ${b.deviations_count}`
).join('\n')}

Equipment with Most Deviations:
${Object.entries(deviationsByEquipment)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 5)
  .map(([eq, count]) => `- ${eq}: ${count} deviations`)
  .join('\n')}`;

      // TABLE: Batch status with counts and percentages
      supportingResults = [{
        kpiName: "batch_quality_status",
        breakdownBy: "status",
        dataPoints: [
          { label: "Total Batches", value: totalBatches },
          { label: "Released", value: releasedBatches.length },
          { label: "Quarantined", value: quarantinedBatches.length },
          { label: "Rejected", value: rejectedBatches.length },
          { label: "With Deviations", value: batchesWithDeviations.length },
        ],
        explanation: "Batch quality distribution"
      }];

      generatedSql = `-- Quality Analysis
SELECT status, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM MES_PASX_BATCHES), 1) as percentage,
       AVG(yield_pct) as avg_yield
FROM MES_PASX_BATCHES
GROUP BY status
ORDER BY count DESC;`;
      break;
    }

    case 'EQUIPMENT_ANALYSIS': {
      analysisContext = `
EQUIPMENT PERFORMANCE ANALYSIS:

Equipment Ranking by Yield (worst to best):
${Object.entries(equipmentStats)
  .sort((a, b) => a[1].avgYield - b[1].avgYield)
  .map(([eq, stats]) =>
    `- ${eq}: ${stats.avgYield.toFixed(1)}% yield, ${stats.count} batches, ${stats.rejectCount} rejections`
  ).join('\n')}

Performance Gap Analysis:
- Best equipment (${bestEquipment[0]?.[0]}): ${bestEquipment[0]?.[1].avgYield.toFixed(1)}% yield
- Worst equipment (${worstEquipment[0]?.[0]}): ${worstEquipment[0]?.[1].avgYield.toFixed(1)}% yield
- Gap: ${(bestEquipment[0]?.[1].avgYield - worstEquipment[0]?.[1].avgYield).toFixed(1)}%`;

      // TABLE: Equipment with batch count, yield, and rejections
      supportingResults = [{
        kpiName: "equipment_performance",
        breakdownBy: "equipment",
        dataPoints: [
          { label: "OVERALL AVG", value: Math.round(avgYield * 10) / 10 },
          ...Object.entries(equipmentStats)
            .sort((a, b) => b[1].avgYield - a[1].avgYield)
            .map(([eq, stats]) => ({
              label: `${eq} (${stats.count} batches)`,
              value: Math.round(stats.avgYield * 10) / 10
            }))
        ],
        explanation: "Equipment yield comparison"
      }];

      generatedSql = `-- Equipment Analysis
SELECT primary_equipment_id,
       COUNT(*) as batch_count,
       ROUND(AVG(yield_pct), 1) as avg_yield,
       SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END) as rejections
FROM MES_PASX_BATCHES
GROUP BY primary_equipment_id
ORDER BY avg_yield DESC;`;
      break;
    }

    case 'IMPROVEMENT_RECO': {
      analysisContext = `
IMPROVEMENT OPPORTUNITIES:

Current Performance vs Targets:
- Yield: ${avgYield.toFixed(1)}% (Target: 98%, Gap: ${(98 - avgYield).toFixed(1)}%)
- Rejection Rate: ${((rejectedBatches.length/totalBatches)*100).toFixed(1)}% (Target: <1%)
- Batches Needing Attention: ${lowYieldBatches.length} low-yield + ${quarantinedBatches.length} quarantined

Priority Actions:
1. Equipment ${worstEquipment[0]?.[0]} - ${worstEquipment[0]?.[1].avgYield.toFixed(1)}% yield (${worstEquipment[0]?.[1].count} batches)
   → Improvement potential: ${(98 - worstEquipment[0]?.[1].avgYield).toFixed(1)}%

2. Equipment ${worstEquipment[1]?.[0]} - ${worstEquipment[1]?.[1].avgYield.toFixed(1)}% yield (${worstEquipment[1]?.[1].count} batches)
   → Improvement potential: ${(98 - worstEquipment[1]?.[1].avgYield).toFixed(1)}%

3. Deviation Reduction - ${batchesWithDeviations.length} batches had deviations

Quick Wins:
- Focus maintenance on ${worstEquipment[0]?.[0]} - biggest impact
- Review ${rejectedBatches.length} rejected batches for common patterns
- Address ${quarantinedBatches.length} quarantined batches in queue`;

      // TABLE: Improvement priorities with current vs target
      supportingResults = [{
        kpiName: "improvement_priorities",
        breakdownBy: "status",
        dataPoints: [
          { label: "Current Yield", value: Math.round(avgYield * 10) / 10 },
          { label: "Target Yield", value: 98 },
          { label: "Gap to Close", value: Math.round((98 - avgYield) * 10) / 10 },
          { label: "Rejection Rate %", value: Math.round((rejectedBatches.length/totalBatches) * 1000) / 10 },
          { label: "Batches to Review", value: lowYieldBatches.length + quarantinedBatches.length },
        ],
        explanation: "Improvement opportunities summary"
      }];

      generatedSql = `-- Improvement Analysis
SELECT
    'Current Performance' as metric,
    ROUND(AVG(yield_pct), 1) as value,
    98 as target,
    ROUND(98 - AVG(yield_pct), 1) as gap
FROM MES_PASX_BATCHES;`;
      break;
    }

    case 'TREND_ANALYSIS': {
      const weeklyKpi = repo.getWeeklyKpi();
      const recentWeeks = weeklyKpi.slice(-10);
      const avgWeeklyYield = weeklyKpi.reduce((sum, w) => sum + Number(w.batch_yield_avg_pct), 0) / weeklyKpi.length;

      analysisContext = `
TREND ANALYSIS:

Recent Weekly Performance:
${recentWeeks.map(w =>
  `- Week ${w.iso_week}: Yield ${Number(w.batch_yield_avg_pct).toFixed(1)}%, RFT ${Number(w.rft_pct).toFixed(1)}%, OEE ${Number(w.oee_packaging_pct).toFixed(1)}%`
).join('\n')}

Trend Summary:
- Weeks analyzed: ${weeklyKpi.length}
- Yield range: ${Math.min(...weeklyKpi.map(w => Number(w.batch_yield_avg_pct))).toFixed(1)}% - ${Math.max(...weeklyKpi.map(w => Number(w.batch_yield_avg_pct))).toFixed(1)}%
- Average weekly yield: ${avgWeeklyYield.toFixed(1)}%`;

      // TABLE: Weekly trend data
      supportingResults = [{
        kpiName: "weekly_trend",
        breakdownBy: "month",
        dataPoints: [
          { label: "Avg Weekly Yield", value: Math.round(avgWeeklyYield * 10) / 10 },
          { label: "Min Yield", value: Math.round(Math.min(...weeklyKpi.map(w => Number(w.batch_yield_avg_pct))) * 10) / 10 },
          { label: "Max Yield", value: Math.round(Math.max(...weeklyKpi.map(w => Number(w.batch_yield_avg_pct))) * 10) / 10 },
          { label: "Weeks Analyzed", value: weeklyKpi.length },
        ],
        explanation: "Weekly yield trend summary"
      }];

      generatedSql = `-- Trend Analysis
SELECT iso_week,
       ROUND(batch_yield_avg_pct, 1) as yield,
       ROUND(rft_pct, 1) as rft,
       ROUND(oee_packaging_pct, 1) as oee
FROM KPI_STORE_WEEKLY
ORDER BY iso_week DESC
LIMIT 10;`;
      break;
    }

    default: {
      analysisContext = `
MANUFACTURING OVERVIEW:

Batch Summary:
- Total: ${totalBatches} batches
- Released: ${releasedBatches.length} (${((releasedBatches.length/totalBatches)*100).toFixed(1)}%)
- Quarantined: ${quarantinedBatches.length} (${((quarantinedBatches.length/totalBatches)*100).toFixed(1)}%)
- Rejected: ${rejectedBatches.length} (${((rejectedBatches.length/totalBatches)*100).toFixed(1)}%)

Key Metrics:
- Average Yield: ${avgYield.toFixed(1)}% (Target: 98%)
- Low Yield Batches (<95%): ${lowYieldBatches.length}
- Batches with Deviations: ${batchesWithDeviations.length}`;

      // TABLE: Overview summary
      supportingResults = [{
        kpiName: "manufacturing_overview",
        breakdownBy: "status",
        dataPoints: [
          { label: "Total Batches", value: totalBatches },
          { label: "Overall Yield %", value: Math.round(avgYield * 10) / 10 },
          { label: "Released", value: releasedBatches.length },
          { label: "Quarantined", value: quarantinedBatches.length },
          { label: "Rejected", value: rejectedBatches.length },
        ],
        explanation: "Manufacturing overview"
      }];

      generatedSql = `-- Overview
SELECT
    COUNT(*) as total_batches,
    ROUND(AVG(yield_pct), 1) as avg_yield,
    SUM(CASE WHEN status='Released' THEN 1 ELSE 0 END) as released,
    SUM(CASE WHEN status='Quarantined' THEN 1 ELSE 0 END) as quarantined,
    SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END) as rejected
FROM MES_PASX_BATCHES;`;
    }
  }

  const conversationContext = conversationHistory.length > 0
    ? conversationHistory.slice(-3).map(h => `${h.role}: ${h.content.substring(0, 150)}`).join('\n')
    : "New conversation";

  await logAgentStep({
    sessionId,
    agentName: "Analyst",
    inputSummary: `Analyzing ${classification.intent}`,
    outputSummary: `Data prepared for ${classification.focusAreas.join(', ')}`,
    reasoningSummary: "Retrieved targeted data for analysis.",
    status: "success",
  });

  // Build narrative prompt from template or use inline fallback
  const promptTemplate = loadPrompt(PROMPTS.ANALYST);
  const narrativePrompt = promptTemplate
    ? injectVariables(promptTemplate, {
        USER_QUESTION: userQuery,
        CONVERSATION_HISTORY: conversationContext,
        BATCH_SUMMARY: `Total: ${totalBatches}, Released: ${releasedBatches.length}, Rejected: ${rejectedBatches.length}, Quarantined: ${quarantinedBatches.length}`,
        EQUIPMENT_STATS: worstEquipment.map(([eq, stats]) => `${eq}: ${stats.avgYield.toFixed(1)}% yield`).join(', '),
        QUALITY_METRICS: `Avg Yield: ${avgYield.toFixed(1)}%, Low Yield Batches: ${lowYieldBatches.length}, Deviations: ${batchesWithDeviations.length}`,
      }) + `\n\nDATA FOR YOUR ANALYSIS:\n${analysisContext}`
    : `You are a Manufacturing Operations Expert at AstraZeneca. Answer this question directly.

USER QUESTION: ${userQuery}

CONVERSATION CONTEXT:
${conversationContext}

DATA FOR YOUR ANALYSIS:
${analysisContext}

INSTRUCTIONS:
1. Answer the user's question DIRECTLY using the data above
2. Be specific - cite actual numbers (batches, percentages, equipment names)
3. If asked for improvements, give 2-3 ACTIONABLE recommendations
4. Keep response under 120 words
5. Do NOT include tables (they are added separately)
6. Focus on insights, not just restating numbers`;

  let narrative: string;
  try {
    narrative = await callClaudeForText(narrativePrompt, "Generate analysis");
  } catch {
    const fallbackNarratives: Record<QuestionIntent, string> = {
      'YIELD_ANALYSIS': `Current yield is ${avgYield.toFixed(1)}% against a 98% target (gap: ${(98-avgYield).toFixed(1)}%). ${lowYieldBatches.length} batches are below 95% yield. Equipment ${worstEquipment[0]?.[0]} shows the lowest yield at ${worstEquipment[0]?.[1].avgYield.toFixed(1)}%. Focus maintenance on underperforming equipment to close the gap.`,
      'ROOT_CAUSE': `Root cause analysis: ${rejectedBatches.length} rejected batches (${((rejectedBatches.length/totalBatches)*100).toFixed(1)}%). Key contributor: Equipment ${worstEquipment[0]?.[0]} at ${worstEquipment[0]?.[1].avgYield.toFixed(1)}% yield. ${batchesWithDeviations.length} batches had deviations. Recommend: equipment maintenance and deviation reduction.`,
      'QUALITY_ISSUES': `Quality overview: ${releasedBatches.length} Released (${((releasedBatches.length/totalBatches)*100).toFixed(1)}%), ${quarantinedBatches.length} Quarantined (${((quarantinedBatches.length/totalBatches)*100).toFixed(1)}%), ${rejectedBatches.length} Rejected (${((rejectedBatches.length/totalBatches)*100).toFixed(1)}%). Focus on reviewing quarantined batches and reducing deviation sources.`,
      'EQUIPMENT_ANALYSIS': `Equipment comparison: ${bestEquipment[0]?.[0]} leads with ${bestEquipment[0]?.[1].avgYield.toFixed(1)}% yield. ${worstEquipment[0]?.[0]} needs attention at ${worstEquipment[0]?.[1].avgYield.toFixed(1)}%. The ${(bestEquipment[0]?.[1].avgYield - worstEquipment[0]?.[1].avgYield).toFixed(1)}% gap represents improvement potential.`,
      'TREND_ANALYSIS': `Weekly yield ranges from ${Math.min(...repo.getWeeklyKpi().map(w => Number(w.batch_yield_avg_pct))).toFixed(1)}% to ${Math.max(...repo.getWeeklyKpi().map(w => Number(w.batch_yield_avg_pct))).toFixed(1)}%. Current average is ${avgYield.toFixed(1)}% against 98% target.`,
      'IMPROVEMENT_RECO': `To improve yield from ${avgYield.toFixed(1)}% to 98%: 1) Focus on ${worstEquipment[0]?.[0]} - ${worstEquipment[0]?.[1].count} batches at ${worstEquipment[0]?.[1].avgYield.toFixed(1)}% yield. 2) Address ${batchesWithDeviations.length} deviation sources. 3) Review ${quarantinedBatches.length} quarantined batches.`,
      'GENERAL_OVERVIEW': `Manufacturing overview: ${totalBatches} total batches, ${((releasedBatches.length/totalBatches)*100).toFixed(1)}% release rate. Average yield ${avgYield.toFixed(1)}% (target 98%). ${rejectedBatches.length} rejections and ${quarantinedBatches.length} in quarantine.`
    };
    narrative = fallbackNarratives[classification.intent];
  }

  await logAgentStep({
    sessionId,
    agentName: "Analyst",
    inputSummary: `Generated ${classification.intent} response`,
    outputSummary: narrative.substring(0, 80) + "...",
    reasoningSummary: "Analysis complete with actionable insights.",
    status: "success",
  });

  // Build insights - these should be key takeaways
  const insights: string[] = [];
  insights.push(`Overall yield: ${avgYield.toFixed(1)}% (Target: 98%)`);
  if (worstEquipment[0]) {
    insights.push(`${worstEquipment[0][0]} has lowest yield at ${worstEquipment[0][1].avgYield.toFixed(1)}%`);
  }
  if (rejectedBatches.length > 0) {
    insights.push(`${rejectedBatches.length} batches rejected (${((rejectedBatches.length/totalBatches)*100).toFixed(1)}%)`);
  }
  if (lowYieldBatches.length > 0) {
    insights.push(`${lowYieldBatches.length} batches below 95% yield threshold`);
  }

  return {
    analystResult: {
      narrative: narrative.trim(),
      supportingKpiResults: supportingResults,
      insights: insights.slice(0, 4),
    },
    generatedSql: `-- ${classification.intent} Analysis\n${generatedSql}`,
  };
}
