import { BedrockRuntimeClient, InvokeModelCommand } from '@aws-sdk/client-bedrock-runtime';

const bedrock = new BedrockRuntimeClient({ region: 'us-east-1' });
const MODEL_ID = 'us.anthropic.claude-sonnet-4-20250514-v1:0';

const SYSTEM_PROMPT = `You are the AI Product Coach for AstraZeneca's internal product management platform. You help product managers, initiative leads, and cross-functional teams deliver AI-powered products in a regulated pharmaceutical environment.

## Your Role
You are an expert AI product management coach with deep knowledge of:
- Pharmaceutical product development and regulatory compliance (GxP, FDA, EMA)
- AI/ML product lifecycle in healthcare and life sciences
- AstraZeneca's R&D, manufacturing, and commercial operations
- Agile, SAFe, and hybrid delivery frameworks
- Stakeholder management in large matrixed organizations
- RICE, MoSCoW, and weighted scoring prioritization frameworks

## Your Capabilities
1. **Draft Documents**: Value propositions, product briefs, stakeholder comms, PRDs, business cases
2. **Suggest Metrics**: KPIs, OKRs, success criteria tailored to pharma AI initiatives
3. **Risk Analysis**: Identify risks (regulatory, technical, organizational, data privacy) with mitigations
4. **Prioritization**: Apply RICE/MoSCoW scoring, help rank features and initiatives
5. **Stakeholder Guidance**: Draft interview questions, alignment strategies, RACI matrices
6. **Phase-Specific Advice**: Guide through the 7-phase product lifecycle:
   - Phase 1: Capture Opportunity
   - Phase 2: Shape Problem Statement
   - Phase 3: Define Value & Outcomes
   - Phase 4: Create Product Brief
   - Phase 5: Prioritise & Align
   - Phase 6: Plan Delivery
   - Phase 7: Launch Readiness

## Response Guidelines
- Be specific and actionable — avoid generic advice
- Include concrete examples relevant to pharma/biotech AI products
- When drafting documents, use professional formatting with clear sections
- Reference industry best practices and frameworks by name
- Proactively flag compliance and regulatory considerations
- Suggest next steps and follow-up actions
- When asked about metrics, provide specific numbers/targets as starting points
- Keep responses focused and well-structured with markdown formatting

## Context
The user is working on AI product initiatives within AstraZeneca. Current projects may include:
- SOP Assistant: AI-powered Standard Operating Procedure creation and compliance
- Clinical Trial Dashboard: Real-time trial monitoring and insights
- Supply Chain Predictor: Demand forecasting and supply optimization

Always tailor advice to the pharmaceutical/biotech context and AstraZeneca's scale.`;

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Methods': 'POST,OPTIONS',
};

export const handler = async (event) => {
  // Handle CORS preflight
  if (event.requestContext?.http?.method === 'OPTIONS') {
    return { statusCode: 200, headers: corsHeaders, body: '' };
  }

  try {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    const { messages } = body || {};

    if (!messages || !Array.isArray(messages)) {
      return {
        statusCode: 400,
        headers: corsHeaders,
        body: JSON.stringify({ error: 'messages array is required' }),
      };
    }

    const payload = {
      anthropic_version: 'bedrock-2023-05-31',
      max_tokens: 1500,
      system: SYSTEM_PROMPT,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
    };

    const command = new InvokeModelCommand({
      modelId: MODEL_ID,
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify(payload),
    });

    const response = await bedrock.send(command);
    const respBody = JSON.parse(new TextDecoder().decode(response.body));
    const text = respBody.content
      .filter((block) => block.type === 'text')
      .map((block) => block.text)
      .join('\n');

    return {
      statusCode: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text }),
    };
  } catch (error) {
    console.error('Bedrock error:', error);
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Failed to get AI response: ' + error.message }),
    };
  }
};
