/**
 * Manufacturing Data Repository
 *
 * Handles loading and querying manufacturing data including:
 * - Weekly/Monthly KPIs (batch yield, OEE, RFT, cycle time)
 * - Batch records (MES data)
 * - Equipment master data
 * - Materials master data
 */

import * as fs from 'fs';
import * as path from 'path';
import { parse } from 'csv-parse/sync';

// KPI Summary interfaces
export interface KpiWeeklySummary {
  iso_week: number;
  site_id: string;
  production_volume: number;
  batch_count: number;
  batch_yield_avg_pct: number;
  rft_pct: number;
  schedule_adherence_pct: number;
  avg_cycle_time_hr: number;
  deviations_per_100_batches: number;
  alarms_per_1000_hours: number;
  stockouts_count: number;
  oee_packaging_pct: number;
  month: string;
}

export interface KpiMonthlySummary {
  SKU: string;
  month: string;
  site_id: string;
  production_volume: number;
  batch_count: number;
  batch_yield_avg_pct: number;
  rft_pct: number;
  schedule_adherence_pct: number;
  avg_cycle_time_hr: number;
  formulation_lead_time_hr: number;
  deviations_per_100_batches: number;
  alarms_per_1000_hours: number;
  lab_turnaround_median_days: number;
  supplier_otif_pct: number;
  oee_packaging_pct: number;
  OTIF_RAG: string;
  RFT_RAG: string;
  OEE_RAG: string;
}

// Transaction data interfaces
export interface BatchRecord {
  batch_id: string;
  order_id: string;
  material_id: string;
  batch_size: number;
  uom: string;
  route: string;
  actual_start: string;
  actual_end: string;
  cycle_time_hr: number;
  yield_qty: number;
  yield_pct: number;
  status: string;
  deviations_count: number;
  rework_flag: boolean;
  primary_equipment_id: string;
}

export interface BatchStep {
  batch_id: string;
  step_id: string;
  step_code: string;
  step_name: string;
  sequence: number;
  step_start: string;
  step_end: string;
  duration_min: number;
  wait_before_min: number;
  target_temp_C: number;
  target_pH: number;
  equipment_id: string;
}

export interface Equipment {
  equipment_id: string;
  type: string;
  area: string;
  line: string;
  capacity_L: number;
}

export interface Material {
  material_id: string;
  description: string;
  uom: string;
  std_batch_size: number;
  value_stream: string;
  route: string;
  type: string;
}

// Query interfaces
export interface ManufacturingQuery {
  dataType: 'weekly_kpi' | 'monthly_kpi' | 'batches' | 'equipment' | 'materials';
  metrics?: string[];
  filters?: {
    site_id?: string;
    batch_id?: string;
    month?: string;
    iso_week?: number;
    status?: string;
  };
  groupBy?: 'site_id' | 'month' | 'status' | 'equipment';
}

export interface KpiResult {
  kpiName: string;
  breakdownBy?: 'site' | 'month' | 'week' | 'status';
  dataPoints: { label: string; value: number }[];
  explanation?: string;
}

class ManufacturingDataRepository {
  private kpiWeekly: KpiWeeklySummary[] = [];
  private kpiMonthly: KpiMonthlySummary[] = [];
  private batches: BatchRecord[] = [];
  private batchSteps: BatchStep[] = [];
  private equipment: Equipment[] = [];
  private materials: Material[] = [];
  private isLoaded = false;

  constructor() {
    this.loadData();
  }

  private loadData(): void {
    if (this.isLoaded) return;

    // __dirname is /backend/src/dataAccess, data is at /backend/data
    const dataDir = path.join(__dirname, '../../data');
    console.log(`[ManufacturingRepo] Loading data from: ${dataDir}`);

    try {
      // Load KPI Weekly
      const kpiWeeklyPath = path.join(dataDir, 'KPI/kpi_store_weekly.csv');
      if (fs.existsSync(kpiWeeklyPath)) {
        const content = fs.readFileSync(kpiWeeklyPath, 'utf-8');
        this.kpiWeekly = parse(content, { columns: true, skip_empty_lines: true });
        console.log(`[ManufacturingRepo] Loaded ${this.kpiWeekly.length} weekly KPI records`);
      }

      // Load KPI Monthly
      const kpiMonthlyPath = path.join(dataDir, 'KPI/kpi_store_monthly.csv');
      console.log(`[ManufacturingRepo] Checking path: ${kpiMonthlyPath}, exists: ${fs.existsSync(kpiMonthlyPath)}`);
      if (fs.existsSync(kpiMonthlyPath)) {
        const content = fs.readFileSync(kpiMonthlyPath, 'utf-8');
        this.kpiMonthly = parse(content, { columns: true, skip_empty_lines: true });
        const skus = [...new Set(this.kpiMonthly.map(r => r.SKU))];
        console.log(`[ManufacturingRepo] Loaded ${this.kpiMonthly.length} monthly KPI records`);
        console.log(`[ManufacturingRepo] Available SKUs: ${skus.join(', ')}`);
      } else {
        console.error(`[ManufacturingRepo] ERROR: Monthly KPI file not found at ${kpiMonthlyPath}`);
      }

      // Load Batches
      const batchesPath = path.join(dataDir, 'Transactional/mes_pasx_batches.csv');
      if (fs.existsSync(batchesPath)) {
        const content = fs.readFileSync(batchesPath, 'utf-8');
        this.batches = parse(content, { columns: true, skip_empty_lines: true });
        console.log(`[ManufacturingRepo] Loaded ${this.batches.length} batch records`);
      }

      // Load Batch Steps
      const batchStepsPath = path.join(dataDir, 'Transactional/mes_pasx_batch_steps.csv');
      if (fs.existsSync(batchStepsPath)) {
        const content = fs.readFileSync(batchStepsPath, 'utf-8');
        this.batchSteps = parse(content, { columns: true, skip_empty_lines: true });
        console.log(`[ManufacturingRepo] Loaded ${this.batchSteps.length} batch step records`);
      }

      // Load Equipment
      const equipmentPath = path.join(dataDir, 'Master data/equipment_master.csv');
      if (fs.existsSync(equipmentPath)) {
        const content = fs.readFileSync(equipmentPath, 'utf-8');
        this.equipment = parse(content, { columns: true, skip_empty_lines: true });
        console.log(`[ManufacturingRepo] Loaded ${this.equipment.length} equipment records`);
      }

      // Load Materials
      const materialsPath = path.join(dataDir, 'Master data/materials_master.csv');
      if (fs.existsSync(materialsPath)) {
        const content = fs.readFileSync(materialsPath, 'utf-8');
        this.materials = parse(content, { columns: true, skip_empty_lines: true });
        console.log(`[ManufacturingRepo] Loaded ${this.materials.length} material records`);
      }

      this.isLoaded = true;
    } catch (error) {
      console.error('[ManufacturingRepo] Error loading data:', error);
    }
  }

  // Get data summary for supervisor agent
  getDataSummary() {
    return {
      availableMetrics: [
        'batch_yield_avg_pct', 'rft_pct', 'oee_packaging_pct', 'avg_cycle_time_hr',
        'production_volume', 'batch_count', 'deviations_per_100_batches', 'schedule_adherence_pct'
      ],
      tables: [
        { name: 'KPI Weekly', rowCount: this.kpiWeekly.length },
        { name: 'KPI Monthly', rowCount: this.kpiMonthly.length },
        { name: 'Batches', rowCount: this.batches.length },
        { name: 'Equipment', rowCount: this.equipment.length },
        { name: 'Materials', rowCount: this.materials.length },
      ]
    };
  }

  // KPI Summary queries
  getWeeklyKpi(filters?: { site_id?: string; iso_week?: number }): KpiWeeklySummary[] {
    let data = [...this.kpiWeekly];
    if (filters?.site_id) {
      data = data.filter(r => r.site_id === filters.site_id);
    }
    if (filters?.iso_week) {
      data = data.filter(r => Number(r.iso_week) === filters.iso_week);
    }
    return data;
  }

  getMonthlyKpi(filters?: { site_id?: string; month?: string; SKU?: string }): KpiMonthlySummary[] {
    let data = [...this.kpiMonthly];
    if (filters?.site_id) {
      data = data.filter(r => r.site_id === filters.site_id);
    }
    if (filters?.month) {
      data = data.filter(r => r.month === filters.month);
    }
    if (filters?.SKU) {
      data = data.filter(r => r.SKU === filters.SKU);
    }
    return data;
  }

  // Aggregation helpers for KPI Gateway
  getKpiSummary(metric: string): { total: number; average: number; latest: number; count: number } {
    const weeklyValues = this.kpiWeekly
      .map(r => parseFloat(String((r as any)[metric])))
      .filter(v => !isNaN(v));

    if (weeklyValues.length === 0) {
      return { total: 0, average: 0, latest: 0, count: 0 };
    }

    const total = weeklyValues.reduce((a, b) => a + b, 0);
    const average = total / weeklyValues.length;
    const latest = weeklyValues[weeklyValues.length - 1];

    return { total, average, latest, count: weeklyValues.length };
  }

  getKpiByGroup(metric: string, groupBy: 'site_id' | 'month'): { label: string; value: number }[] {
    const grouped: Record<string, number[]> = {};

    for (const row of this.kpiWeekly) {
      const key = String((row as any)[groupBy]);
      const value = parseFloat(String((row as any)[metric]));
      if (!isNaN(value)) {
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(value);
      }
    }

    return Object.entries(grouped).map(([label, values]) => ({
      label,
      value: values.reduce((a, b) => a + b, 0) / values.length
    }));
  }

  // Batch queries for Analyst
  getBatches(filters?: { batch_id?: string; status?: string; material_id?: string }): BatchRecord[] {
    let data = [...this.batches];
    if (filters?.batch_id) {
      data = data.filter(r => r.batch_id === filters.batch_id);
    }
    if (filters?.status) {
      data = data.filter(r => r.status === filters.status);
    }
    if (filters?.material_id) {
      data = data.filter(r => r.material_id === filters.material_id);
    }
    return data;
  }

  getBatchesByStatus(): { status: string; count: number; avgYield: number }[] {
    const grouped: Record<string, { count: number; yields: number[] }> = {};

    for (const batch of this.batches) {
      const status = batch.status || 'Unknown';
      if (!grouped[status]) grouped[status] = { count: 0, yields: [] };
      grouped[status].count++;
      const yieldPct = parseFloat(String(batch.yield_pct));
      if (!isNaN(yieldPct)) grouped[status].yields.push(yieldPct);
    }

    return Object.entries(grouped).map(([status, data]) => ({
      status,
      count: data.count,
      avgYield: data.yields.length > 0 ? data.yields.reduce((a, b) => a + b, 0) / data.yields.length : 0
    }));
  }

  getBatchesByEquipment(): { equipment: string; count: number; avgCycleTime: number }[] {
    const grouped: Record<string, { count: number; cycleTimes: number[] }> = {};

    for (const batch of this.batches) {
      const eq = batch.primary_equipment_id || 'Unknown';
      if (!grouped[eq]) grouped[eq] = { count: 0, cycleTimes: [] };
      grouped[eq].count++;
      const cycleTime = parseFloat(String(batch.cycle_time_hr));
      if (!isNaN(cycleTime)) grouped[eq].cycleTimes.push(cycleTime);
    }

    return Object.entries(grouped).map(([equipment, data]) => ({
      equipment,
      count: data.count,
      avgCycleTime: data.cycleTimes.length > 0 ? data.cycleTimes.reduce((a, b) => a + b, 0) / data.cycleTimes.length : 0
    }));
  }

  // Equipment queries
  getEquipment(filters?: { type?: string; area?: string }): Equipment[] {
    let data = [...this.equipment];
    if (filters?.type) {
      data = data.filter(r => r.type === filters.type);
    }
    if (filters?.area) {
      data = data.filter(r => r.area === filters.area);
    }
    return data;
  }

  // Materials queries
  getMaterials(): Material[] {
    return [...this.materials];
  }

  // Unique values for filtering
  getUniqueSiteIds(): string[] {
    return [...new Set(this.kpiWeekly.map(r => r.site_id))];
  }

  getUniqueMonths(): string[] {
    return [...new Set(this.kpiMonthly.map(r => r.month))].sort();
  }

  // Data availability result with metadata
  getKpiByMonthWithMetadata(
    metric: string,
    requestedMonths?: number,
    skuFilter?: string | null
  ): {
    dataPoints: { label: string; value: number }[];
    metadata: {
      requestedMonths: number | null;
      availableMonths: number;
      allAvailableMonths: string[];
      skuFound: boolean;
      skuFilter: string | null;
      metricFound: boolean;
      metric: string;
      allAvailableSKUs: string[];
    };
  } {
    const allSKUs = [...new Set(this.kpiMonthly.map(r => r.SKU))];
    const allMonths = [...new Set(this.kpiMonthly.map(r => r.month))].sort();

    // Check if metric exists in data
    const sampleRow = this.kpiMonthly[0] as any;
    const metricFound = sampleRow && metric in sampleRow;

    // Apply SKU filter
    let filteredData = this.kpiMonthly;
    const skuFound = !skuFilter || allSKUs.includes(skuFilter);

    if (skuFilter) {
      filteredData = filteredData.filter(row => row.SKU === skuFilter);
    }

    const monthlyData = filteredData
      .map(row => ({
        month: row.month,
        value: parseFloat(String((row as any)[metric]))
      }))
      .filter(r => !isNaN(r.value))
      .sort((a, b) => a.month.localeCompare(b.month));

    // Get unique months for this filter
    const uniqueMonths = [...new Set(monthlyData.map(r => r.month))].sort();
    const availableMonths = uniqueMonths.length;

    // Take last N months (or all if not specified)
    const targetMonths = requestedMonths ? uniqueMonths.slice(-requestedMonths) : uniqueMonths;

    // Get values for each month
    const dataPoints = targetMonths.map(month => {
      const monthRows = monthlyData.filter(r => r.month === month);
      const avgValue = monthRows.reduce((sum, r) => sum + r.value, 0) / monthRows.length;
      return {
        label: month,
        value: Math.round(avgValue * 10) / 10
      };
    });

    return {
      dataPoints,
      metadata: {
        requestedMonths: requestedMonths || null,
        availableMonths,
        allAvailableMonths: uniqueMonths,
        skuFound,
        skuFilter: skuFilter || null,
        metricFound,
        metric,
        allAvailableSKUs: allSKUs
      }
    };
  }

  // Legacy method for backward compatibility
  getKpiByMonth(metric: string, lastNMonths?: number, skuFilter?: string | null): { label: string; value: number }[] {
    return this.getKpiByMonthWithMetadata(metric, lastNMonths, skuFilter).dataPoints;
  }

  getBatchStatuses(): string[] {
    return [...new Set(this.batches.map(r => r.status))];
  }

  // Get batch steps for a specific batch
  getBatchSteps(batchId: string): BatchStep[] {
    return this.batchSteps
      .filter(s => s.batch_id === batchId)
      .sort((a, b) => Number(a.sequence) - Number(b.sequence));
  }

  // Get waiting time between two steps for a batch
  getWaitingTimeBetweenSteps(batchId: string, fromStep: string, toStep: string): { actualDays: number; plannedDays: number } | null {
    const steps = this.getBatchSteps(batchId);
    if (steps.length === 0) return null;

    // Map step names to codes (formulation = HOLD end, packaging = FILL start)
    const stepMapping: Record<string, string[]> = {
      'formulation': ['HOLD', 'HEAT', 'MIX'],
      'packaging': ['FILL', 'PACK'],
      'filtration': ['FLT', 'FILTER'],
      'cooling': ['COOL'],
    };

    const fromCodes = stepMapping[fromStep.toLowerCase()] || [fromStep.toUpperCase()];
    const toCodes = stepMapping[toStep.toLowerCase()] || [toStep.toUpperCase()];

    // Find the from step (last matching step)
    const fromStepData = [...steps].reverse().find(s =>
      fromCodes.some(code => s.step_code.includes(code) || s.step_name.toLowerCase().includes(code.toLowerCase()))
    );

    // Find the to step (first matching step after from step)
    const toStepData = steps.find(s =>
      toCodes.some(code => s.step_code.includes(code) || s.step_name.toLowerCase().includes(code.toLowerCase()))
    );

    if (!fromStepData || !toStepData) return null;

    const fromEnd = new Date(fromStepData.step_end);
    const toStart = new Date(toStepData.step_start);

    // Calculate actual waiting time in days
    const actualMs = toStart.getTime() - fromEnd.getTime();
    const actualDays = Math.round((actualMs / (1000 * 60 * 60 * 24)) * 10) / 10;

    // Planned waiting time (from wait_before_min of the to step)
    const plannedDays = Math.round((Number(toStepData.wait_before_min) / (60 * 24)) * 10) / 10;

    return { actualDays: Math.max(0, actualDays), plannedDays };
  }

  // Get lead time for a batch
  getBatchLeadTime(batchId: string): { actualLeadTimeDays: number; plannedLeadTimeDays: number } | null {
    const steps = this.getBatchSteps(batchId);
    if (steps.length === 0) return null;

    const firstStep = steps[0];
    const lastStep = steps[steps.length - 1];

    const start = new Date(firstStep.step_start);
    const end = new Date(lastStep.step_end);

    const actualMs = end.getTime() - start.getTime();
    const actualLeadTimeDays = Math.round((actualMs / (1000 * 60 * 60 * 24)) * 10) / 10;

    // Calculate planned time (sum of all durations + wait times)
    const plannedMinutes = steps.reduce((sum, s) => sum + Number(s.duration_min) + Number(s.wait_before_min), 0);
    const plannedLeadTimeDays = Math.round((plannedMinutes / (60 * 24)) * 10) / 10;

    return { actualLeadTimeDays, plannedLeadTimeDays };
  }
}

// Singleton instance
let instance: ManufacturingDataRepository | null = null;

export function getManufacturingDataRepository(): ManufacturingDataRepository {
  if (!instance) {
    instance = new ManufacturingDataRepository();
  }
  return instance;
}

// Alias for SA compatibility
export function getSustainabilityDataRepository(): ManufacturingDataRepository {
  return getManufacturingDataRepository();
}
