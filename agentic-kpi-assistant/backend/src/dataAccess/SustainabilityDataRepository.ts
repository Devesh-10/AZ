/**
 * Sustainability Data Repository
 *
 * Handles loading and querying AstraZeneca sustainability data including:
 * - Energy consumption
 * - Greenhouse gas emissions
 * - Water usage
 * - Waste management
 * - Electric vehicle fleet transition
 */

import * as fs from 'fs';
import * as path from 'path';

// Data types based on regenerated data structure
export interface EnergyMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  SHE_SITE_NAME: string;
  REPORTING_SCOPE_NAME: string;
  ENERGY_SITE_MWH_QUANTITY: number;
  ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY: number;
  ENERGY_RENEWABLE_INDIRECT_MWH_QUANTITY: number;
  ENERGY_INDIRECT_MWH_QUANTITY: number;
  ENERGY_ONSITE_GENERATED_RENEWABLE_SOLAR_MWH_QUANTITY: number;
  ENERGY_ONSITE_GENERATED_NON_RENEWABLE_MWH_QUANTITY: number;
  ENERGY_IMPORTED_RENEWABLE_MWH_QUANTITY: number;
  ENERGY_IMPORTED_MWH_QUANTITY: number;
  SRC_SYS_NM: string;
}

export interface GHGEmissionsQuarterlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  REPORTING_SCOPE_NAME: string;
  SCOPE1_ROAD_FLEET_TCO2_QUANTITY: number;
  SCOPE1_F_GASES_TCO2_QUANTITY: number;
  SCOPE1_SOLVENTS_TCO2_QUANTITY: number;
  SCOPE1_SITE_ENERGY_TCO2_QUANTITY: number;
  SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY: number;
  SCOPE1_TOTAL_TCO2_QUANTITY: number;
  SCOPE2_MARKET_BASED_EV_CHARGING_TCO2_QUANTITY: number;
  SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY: number;
  GROSS_SCOPE1_SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY: number;
  SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY: number;
  SRC_SYS_NM: string;
  [key: string]: string | number;
}

export interface GHGEmissionsMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  REPORTING_SCOPE_NAME: string;
  SCOPE1_F_GASES_TCO2_QUANTITY: number;
  SCOPE1_SOLVENTS_TCO2_QUANTITY: number;
  SCOPE1_SITE_ENERGY_TCO2_QUANTITY: number;
  SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY: number;
  SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY: number;
  SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY: number;
  SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY: number;
  SRC_SYS_NM: string;
  [key: string]: string | number;
}

export interface WasteMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  WASTE_TONNES_SITE_QUANTITY: number;
  WASTE_TONNES_PRODUCT_QUANTITY: number;
  TOTAL_WASTE_TONNES_QUANTITY: number;
  TOTAL_RECYCLED_WASTE_TONNES_QUANTITY: number;
  TOTAL_WASTE_TO_LANDFILL_TONNES_QUANTITY: number;
  TOTAL_HAZARDOUS_WASTE_TONNES_QUANTITY: number;
  TOTAL_NON_HAZARDOUS_WASTE_TONNES_QUANTITY: number;
  SRC_SYS_NM: string;
  [key: string]: string | number;
}

export interface WaterMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  GROUNDWATER_MILLION_M3_QUANTITY: number;
  MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY: number;
  RAINWATER_HARVESTING_MILLION_M3_QUANTITY: number;
  TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY: number;
  DIRECT_FROM_FRESH_SURFACE_MILLION_M3_QUANTITY: number;
  SRC_SYS_NM: string;
  [key: string]: string | number;
}

export interface EVTransitionQuarterlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_MARKET_NAME: string;
  SHE_GEOGRAPHY_NAME: string;
  TOTAL_BEV_COUNT: number;
  TOTAL_FLEET_ASSET_COUNT: number;
  SRC_SYS_NM: string;
  [key: string]: string | number;
}

export interface SheSite {
  SHE_SITE_IDENTIFIER: number;
  SHE_SITE_CODE: string;
  SHE_SITE_NAME: string;
  COUNTRY_CODE: string;
  REPORTING_SCOPE_NAME: string;
  SRC_SYS_NM: string;
}

export interface SheIndicator {
  SHE_INDICATOR_IDENTIFIER: number;
  SHE_INDICATOR_CODE: string;
  SHE_INDICATOR_NAME: string;
  SHE_REFERENCE_CODE: string;
  SHE_REFERENCE_NAME: string;
  SHE_TOPIC_CODE: string;
  [key: string]: string | number;
}

// Query interfaces
export interface SustainabilityQuery {
  dataType: 'energy' | 'ghg_emissions' | 'water' | 'waste' | 'ev_transition';
  metrics?: string[];
  year?: number;
  quarter?: number;
  month?: number;
  siteName?: string;
  groupBy?: 'site' | 'month' | 'quarter' | 'year';
}

export interface SustainabilityResult {
  dataType: string;
  metrics: string[];
  dataPoints: { label: string; value: number; unit: string }[];
  breakdown?: { dimension: string; data: { label: string; value: number }[] };
  summary: string;
}

export class SustainabilityDataRepository {
  private energyMonthly: EnergyMonthlySummary[] = [];
  private energyQuarterly: any[] = [];
  private ghgEmissionsMonthly: GHGEmissionsMonthlySummary[] = [];
  private ghgEmissionsQuarterly: GHGEmissionsQuarterlySummary[] = [];
  private wasteMonthly: WasteMonthlySummary[] = [];
  private waterMonthly: WaterMonthlySummary[] = [];
  private evTransitionQuarterly: EVTransitionQuarterlySummary[] = [];
  private sheSites: SheSite[] = [];
  private sheIndicators: SheIndicator[] = [];

  private isLoaded = false;

  constructor() {
    this.loadData();
  }

  private loadData() {
    const jsonPath = path.join(__dirname, '../data/json');

    try {
      // Load KPI data
      this.energyMonthly = this.loadJsonFile(path.join(jsonPath, 'kpi/energy_monthly_summary.json'));
      this.energyQuarterly = this.loadJsonFile(path.join(jsonPath, 'kpi/energy_quarterly_summary.json'));
      this.ghgEmissionsMonthly = this.loadJsonFile(path.join(jsonPath, 'kpi/greenhouse_gas_emissions_monthly_summary.json'));
      this.ghgEmissionsQuarterly = this.loadJsonFile(path.join(jsonPath, 'kpi/greenhouse_gas_emissions_quarterly_summary.json'));
      this.wasteMonthly = this.loadJsonFile(path.join(jsonPath, 'kpi/waste_monthly_summary.json'));
      this.waterMonthly = this.loadJsonFile(path.join(jsonPath, 'kpi/water_monthly_summary.json'));
      this.evTransitionQuarterly = this.loadJsonFile(path.join(jsonPath, 'kpi/electric_vehicle_transition_quarterly_summary.json'));

      // Load Master data
      this.sheSites = this.loadJsonFile(path.join(jsonPath, 'masterData/she_site.json'));
      this.sheIndicators = this.loadJsonFile(path.join(jsonPath, 'masterData/she_indicator.json'));

      this.isLoaded = true;
      console.log('[SustainabilityDataRepository] Data loaded successfully');
      console.log(`  - Energy Monthly: ${this.energyMonthly.length} rows`);
      console.log(`  - Energy Quarterly: ${this.energyQuarterly.length} rows`);
      console.log(`  - GHG Emissions Monthly: ${this.ghgEmissionsMonthly.length} rows`);
      console.log(`  - GHG Emissions Quarterly: ${this.ghgEmissionsQuarterly.length} rows`);
      console.log(`  - Waste Monthly: ${this.wasteMonthly.length} rows`);
      console.log(`  - Water Monthly: ${this.waterMonthly.length} rows`);
      console.log(`  - EV Transition Quarterly: ${this.evTransitionQuarterly.length} rows`);
    } catch (error) {
      console.error('[SustainabilityDataRepository] Error loading data:', error);
    }
  }

  private loadJsonFile(filePath: string): any[] {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      console.warn(`Could not load ${filePath}`);
      return [];
    }
  }

  // ========== Energy Queries ==========

  getEnergyConsumption(options: {
    year?: number;
    quarter?: number;
    month?: number;
    siteName?: string;
    groupBy?: 'site' | 'month' | 'quarter' | 'year';
  } = {}): SustainabilityResult {
    let data = [...this.energyMonthly];

    // Apply filters
    if (options.year) {
      data = data.filter(d => d.REPORTING_YEAR_NUMBER === options.year);
    }
    if (options.quarter) {
      data = data.filter(d => d.REPORTING_QUARTER_NUMBER === options.quarter);
    }
    if (options.month) {
      data = data.filter(d => d.REPORTING_MONTH_NUMBER === options.month);
    }
    if (options.siteName) {
      data = data.filter(d => d.SHE_SITE_NAME.toLowerCase().includes(options.siteName!.toLowerCase()));
    }

    // Calculate totals
    const totalEnergy = data.reduce((sum, d) => sum + (d.ENERGY_SITE_MWH_QUANTITY || 0), 0);
    const renewableEnergy = data.reduce((sum, d) => sum + (d.ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY || 0), 0);
    // Non-renewable = Total - Renewable (these are mutually exclusive and add up to Total)
    const nonRenewableEnergy = totalEnergy - renewableEnergy;

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'site') {
      const bysite = new Map<string, number>();
      data.forEach(d => {
        const current = bysite.get(d.SHE_SITE_NAME) || 0;
        bysite.set(d.SHE_SITE_NAME, current + (d.ENERGY_SITE_MWH_QUANTITY || 0));
      });
      breakdown = {
        dimension: 'Site',
        data: Array.from(bysite.entries())
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
          .sort((a, b) => b.value - a.value)
      };
    } else if (options.groupBy === 'month') {
      const byMonth = new Map<string, number>();
      data.forEach(d => {
        const key = `${d.REPORTING_YEAR_NUMBER}-${String(d.REPORTING_MONTH_NUMBER).padStart(2, '0')}`;
        const current = byMonth.get(key) || 0;
        byMonth.set(key, current + (d.ENERGY_SITE_MWH_QUANTITY || 0));
      });
      breakdown = {
        dimension: 'Month',
        data: Array.from(byMonth.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
      };
    } else if (options.groupBy === 'quarter') {
      const byQuarter = new Map<string, number>();
      data.forEach(d => {
        const key = `${d.REPORTING_YEAR_NUMBER} Q${d.REPORTING_QUARTER_NUMBER}`;
        const current = byQuarter.get(key) || 0;
        byQuarter.set(key, current + (d.ENERGY_SITE_MWH_QUANTITY || 0));
      });
      breakdown = {
        dimension: 'Quarter',
        data: Array.from(byQuarter.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
      };
    } else if (options.groupBy === 'year') {
      const byYear = new Map<number, number>();
      data.forEach(d => {
        const current = byYear.get(d.REPORTING_YEAR_NUMBER) || 0;
        byYear.set(d.REPORTING_YEAR_NUMBER, current + (d.ENERGY_SITE_MWH_QUANTITY || 0));
      });
      breakdown = {
        dimension: 'Year',
        data: Array.from(byYear.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([label, value]) => ({ label: String(label), value: Math.round(value * 100) / 100 }))
      };
    }

    // Calculate renewable percentage safely
    const renewablePercent = totalEnergy > 0 ? ((renewableEnergy / totalEnergy) * 100) : 0;

    // Return only non-overlapping categories that ADD UP to Total:
    // Total = Renewable + Non-Renewable
    return {
      dataType: 'energy',
      metrics: ['Total Energy (MWh)', 'Renewable Energy (MWh)', 'Non-Renewable Energy (MWh)'],
      dataPoints: [
        { label: 'Renewable Energy', value: Math.round(renewableEnergy * 100) / 100, unit: 'MWh' },
        { label: 'Non-Renewable Energy', value: Math.round(nonRenewableEnergy * 100) / 100, unit: 'MWh' },
        { label: 'Total Energy', value: Math.round(totalEnergy * 100) / 100, unit: 'MWh' }
      ],
      breakdown,
      summary: `Total energy consumption: ${totalEnergy.toLocaleString(undefined, {maximumFractionDigits: 2})} MWh. Renewable: ${renewableEnergy.toLocaleString(undefined, {maximumFractionDigits: 2})} MWh (${renewablePercent.toFixed(1)}%), Non-Renewable: ${nonRenewableEnergy.toLocaleString(undefined, {maximumFractionDigits: 2})} MWh (${(100 - renewablePercent).toFixed(1)}%).`
    };
  }

  // ========== GHG Emissions Queries ==========
  // Uses quarterly data for complete breakdown including Road Fleet

  getGHGEmissions(options: {
    year?: number;
    quarter?: number;
    month?: number;
    siteName?: string;
    scope?: string;
    groupBy?: 'site' | 'month' | 'quarter' | 'year';
  } = {}): SustainabilityResult {
    // Use quarterly data as it has complete Scope 1 breakdown including Road Fleet
    let data = [...this.ghgEmissionsQuarterly];

    if (options.year) {
      data = data.filter(d => d.REPORTING_YEAR_NUMBER === options.year);
    }
    if (options.quarter) {
      data = data.filter(d => d.REPORTING_QUARTER_NUMBER === options.quarter);
    }
    if (options.siteName) {
      data = data.filter(d => d.SHE_SITE_NAME.toLowerCase().includes(options.siteName!.toLowerCase()));
    }

    // Calculate totals from quarterly data
    const scope1FGases = data.reduce((sum, d) => sum + (Number(d.SCOPE1_F_GASES_TCO2_QUANTITY) || 0), 0);
    const scope1Fleet = data.reduce((sum, d) => sum + (Number(d.SCOPE1_ROAD_FLEET_TCO2_QUANTITY) || 0), 0);
    const scope1SiteEnergy = data.reduce((sum, d) => sum + (Number(d.SCOPE1_SITE_ENERGY_TCO2_QUANTITY) || 0), 0);
    const scope1Solvents = data.reduce((sum, d) => sum + (Number(d.SCOPE1_SOLVENTS_TCO2_QUANTITY) || 0), 0);
    const scope1NonEnergy = data.reduce((sum, d) => sum + (Number(d.SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY) || 0), 0);
    const scope1Total = data.reduce((sum, d) => sum + (Number(d.SCOPE1_TOTAL_TCO2_QUANTITY) || 0), 0);
    const scope2Market = data.reduce((sum, d) => sum + (Number(d.SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY) || 0), 0);
    const scope2Location = data.reduce((sum, d) => sum + (Number(d.SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY) || 0), 0);

    // Total emissions = Scope 1 Total + Scope 2 (Market-based is the primary accounting method)
    const totalEmissions = scope1Total + scope2Market;

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'site') {
      const bySite = new Map<string, number>();
      data.forEach(d => {
        const total = (Number(d.SCOPE1_TOTAL_TCO2_QUANTITY) || 0) +
                     (Number(d.SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY) || 0);
        const current = bySite.get(d.SHE_SITE_NAME) || 0;
        bySite.set(d.SHE_SITE_NAME, current + total);
      });
      breakdown = {
        dimension: 'Site',
        data: Array.from(bySite.entries())
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
          .sort((a, b) => b.value - a.value)
      };
    } else if (options.groupBy === 'quarter') {
      const byQuarter = new Map<string, number>();
      data.forEach(d => {
        const key = `${d.REPORTING_YEAR_NUMBER} Q${d.REPORTING_QUARTER_NUMBER}`;
        const total = (Number(d.SCOPE1_TOTAL_TCO2_QUANTITY) || 0) +
                     (Number(d.SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY) || 0);
        const current = byQuarter.get(key) || 0;
        byQuarter.set(key, current + total);
      });
      breakdown = {
        dimension: 'Quarter',
        data: Array.from(byQuarter.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
      };
    } else if (options.groupBy === 'year') {
      const byYear = new Map<number, number>();
      data.forEach(d => {
        const total = (Number(d.SCOPE1_TOTAL_TCO2_QUANTITY) || 0) +
                     (Number(d.SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY) || 0);
        const current = byYear.get(d.REPORTING_YEAR_NUMBER) || 0;
        byYear.set(d.REPORTING_YEAR_NUMBER, current + total);
      });
      breakdown = {
        dimension: 'Year',
        data: Array.from(byYear.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([label, value]) => ({ label: String(label), value: Math.round(value * 100) / 100 }))
      };
    }

    // Return only the primary metrics that add up correctly:
    // Total = Scope 1 Total + Scope 2 Market-Based
    // Note: Location-Based is an alternative accounting method (not added to total)
    // Note: Road Fleet, F-Gases, Site Energy are COMPONENTS of Scope 1 Total (not separate)
    return {
      dataType: 'ghg_emissions',
      metrics: ['Total Emissions (tCO2)', 'Scope 1 Total (tCO2)', 'Scope 2 Market-Based (tCO2)'],
      dataPoints: [
        { label: 'Scope 1 Total', value: Math.round(scope1Total * 100) / 100, unit: 'tCO2' },
        { label: 'Scope 2 Market-Based', value: Math.round(scope2Market * 100) / 100, unit: 'tCO2' },
        { label: 'Total Emissions (Scope 1+2)', value: Math.round(totalEmissions * 100) / 100, unit: 'tCO2' }
      ],
      breakdown,
      summary: `Total GHG emissions: ${totalEmissions.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2 (Scope 1: ${scope1Total.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2, Scope 2 Market-based: ${scope2Market.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2). Scope 1 breakdown: Road Fleet ${scope1Fleet.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2 (${scope1Total > 0 ? ((scope1Fleet / scope1Total) * 100).toFixed(1) : 0}%), F-Gases ${scope1FGases.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2, Site Energy ${scope1SiteEnergy.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2. Note: Scope 2 Location-Based would be ${scope2Location.toLocaleString(undefined, {maximumFractionDigits: 2})} tCO2 (alternative accounting method).`
    };
  }

  // ========== Water Usage Queries ==========

  getWaterUsage(options: {
    year?: number;
    quarter?: number;
    month?: number;
    siteName?: string;
    groupBy?: 'site' | 'month' | 'quarter' | 'year';
  } = {}): SustainabilityResult {
    let data = [...this.waterMonthly];

    if (options.year) {
      data = data.filter(d => d.REPORTING_YEAR_NUMBER === options.year);
    }
    if (options.quarter) {
      data = data.filter(d => d.REPORTING_QUARTER_NUMBER === options.quarter);
    }
    if (options.month) {
      data = data.filter(d => d.REPORTING_MONTH_NUMBER === options.month);
    }
    if (options.siteName) {
      data = data.filter(d => d.SHE_SITE_NAME.toLowerCase().includes(options.siteName!.toLowerCase()));
    }

    const groundwater = data.reduce((sum, d) => sum + (Number(d.GROUNDWATER_MILLION_M3_QUANTITY) || 0), 0);
    const municipal = data.reduce((sum, d) => sum + (Number(d.MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY) || 0), 0);
    const rainwater = data.reduce((sum, d) => sum + (Number(d.RAINWATER_HARVESTING_MILLION_M3_QUANTITY) || 0), 0);
    const surface = data.reduce((sum, d) => sum + (Number(d.DIRECT_FROM_FRESH_SURFACE_MILLION_M3_QUANTITY) || 0), 0);
    const totalWater = data.reduce((sum, d) => sum + (Number(d.TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) || 0), 0);

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'site') {
      const bySite = new Map<string, number>();
      data.forEach(d => {
        const current = bySite.get(d.SHE_SITE_NAME) || 0;
        bySite.set(d.SHE_SITE_NAME, current + (Number(d.TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) || 0));
      });
      breakdown = {
        dimension: 'Site',
        data: Array.from(bySite.entries())
          .map(([label, value]) => ({ label, value: Math.round(value * 10000) / 10000 }))
          .sort((a, b) => b.value - a.value)
      };
    } else if (options.groupBy === 'month') {
      const byMonth = new Map<string, number>();
      data.forEach(d => {
        const key = `${d.REPORTING_YEAR_NUMBER}-${String(d.REPORTING_MONTH_NUMBER).padStart(2, '0')}`;
        const current = byMonth.get(key) || 0;
        byMonth.set(key, current + (Number(d.TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) || 0));
      });
      breakdown = {
        dimension: 'Month',
        data: Array.from(byMonth.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([label, value]) => ({ label, value: Math.round(value * 10000) / 10000 }))
      };
    } else if (options.groupBy === 'year') {
      const byYear = new Map<number, number>();
      data.forEach(d => {
        const current = byYear.get(d.REPORTING_YEAR_NUMBER) || 0;
        byYear.set(d.REPORTING_YEAR_NUMBER, current + (Number(d.TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) || 0));
      });
      breakdown = {
        dimension: 'Year',
        data: Array.from(byYear.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([label, value]) => ({ label: String(label), value: Math.round(value * 10000) / 10000 }))
      };
    }

    return {
      dataType: 'water',
      metrics: ['Total Water (Million m³)', 'Groundwater (Million m³)', 'Municipal Supply (Million m³)', 'Rainwater (Million m³)'],
      dataPoints: [
        { label: 'Total Water Withdrawn', value: Math.round(totalWater * 10000) / 10000, unit: 'Million m³' },
        { label: 'Groundwater', value: Math.round(groundwater * 10000) / 10000, unit: 'Million m³' },
        { label: 'Municipal Supply', value: Math.round(municipal * 10000) / 10000, unit: 'Million m³' },
        { label: 'Rainwater Harvesting', value: Math.round(rainwater * 10000) / 10000, unit: 'Million m³' },
        { label: 'Surface Water', value: Math.round(surface * 10000) / 10000, unit: 'Million m³' }
      ],
      breakdown,
      summary: `Total water withdrawn: ${totalWater.toFixed(4)} Million m³. Sources: Municipal ${totalWater > 0 ? ((municipal / totalWater) * 100).toFixed(1) : 0}%, Groundwater ${totalWater > 0 ? ((groundwater / totalWater) * 100).toFixed(1) : 0}%, Rainwater ${totalWater > 0 ? ((rainwater / totalWater) * 100).toFixed(1) : 0}%`
    };
  }

  // ========== Waste Queries ==========

  getWaste(options: {
    year?: number;
    quarter?: number;
    month?: number;
    siteName?: string;
    groupBy?: 'site' | 'month' | 'quarter' | 'year';
  } = {}): SustainabilityResult {
    let data = [...this.wasteMonthly];

    if (options.year) {
      data = data.filter(d => d.REPORTING_YEAR_NUMBER === options.year);
    }
    if (options.quarter) {
      data = data.filter(d => d.REPORTING_QUARTER_NUMBER === options.quarter);
    }
    if (options.month) {
      data = data.filter(d => d.REPORTING_MONTH_NUMBER === options.month);
    }
    if (options.siteName) {
      data = data.filter(d => d.SHE_SITE_NAME.toLowerCase().includes(options.siteName!.toLowerCase()));
    }

    const siteWaste = data.reduce((sum, d) => sum + (Number(d.WASTE_TONNES_SITE_QUANTITY) || 0), 0);
    const productWaste = data.reduce((sum, d) => sum + (Number(d.WASTE_TONNES_PRODUCT_QUANTITY) || 0), 0);
    const totalWaste = data.reduce((sum, d) => sum + (Number(d.TOTAL_WASTE_TONNES_QUANTITY) || 0), 0);
    const recycledWaste = data.reduce((sum, d) => sum + (Number(d.TOTAL_RECYCLED_WASTE_TONNES_QUANTITY) || 0), 0);
    const landfillWaste = data.reduce((sum, d) => sum + (Number(d.TOTAL_WASTE_TO_LANDFILL_TONNES_QUANTITY) || 0), 0);
    const hazardousWaste = data.reduce((sum, d) => sum + (Number(d.TOTAL_HAZARDOUS_WASTE_TONNES_QUANTITY) || 0), 0);
    const nonHazardousWaste = data.reduce((sum, d) => sum + (Number(d.TOTAL_NON_HAZARDOUS_WASTE_TONNES_QUANTITY) || 0), 0);

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'site') {
      const bySite = new Map<string, number>();
      data.forEach(d => {
        const current = bySite.get(d.SHE_SITE_NAME) || 0;
        bySite.set(d.SHE_SITE_NAME, current + (Number(d.TOTAL_WASTE_TONNES_QUANTITY) || 0));
      });
      breakdown = {
        dimension: 'Site',
        data: Array.from(bySite.entries())
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
          .sort((a, b) => b.value - a.value)
      };
    } else if (options.groupBy === 'month') {
      const byMonth = new Map<string, number>();
      data.forEach(d => {
        const key = `${d.REPORTING_YEAR_NUMBER}-${String(d.REPORTING_MONTH_NUMBER).padStart(2, '0')}`;
        const current = byMonth.get(key) || 0;
        byMonth.set(key, current + (Number(d.TOTAL_WASTE_TONNES_QUANTITY) || 0));
      });
      breakdown = {
        dimension: 'Month',
        data: Array.from(byMonth.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
      };
    } else if (options.groupBy === 'year') {
      const byYear = new Map<number, number>();
      data.forEach(d => {
        const current = byYear.get(d.REPORTING_YEAR_NUMBER) || 0;
        byYear.set(d.REPORTING_YEAR_NUMBER, current + (Number(d.TOTAL_WASTE_TONNES_QUANTITY) || 0));
      });
      breakdown = {
        dimension: 'Year',
        data: Array.from(byYear.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([label, value]) => ({ label: String(label), value: Math.round(value * 100) / 100 }))
      };
    }

    const recycleRate = totalWaste > 0 ? ((recycledWaste / totalWaste) * 100) : 0;

    return {
      dataType: 'waste',
      metrics: ['Total Waste (Tonnes)', 'Recycled Waste (Tonnes)', 'Landfill Waste (Tonnes)', 'Hazardous Waste (Tonnes)'],
      dataPoints: [
        { label: 'Total Waste', value: Math.round(totalWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Site Waste', value: Math.round(siteWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Product Waste', value: Math.round(productWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Recycled Waste', value: Math.round(recycledWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Landfill Waste', value: Math.round(landfillWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Hazardous Waste', value: Math.round(hazardousWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Non-Hazardous Waste', value: Math.round(nonHazardousWaste * 100) / 100, unit: 'Tonnes' }
      ],
      breakdown,
      summary: `Total waste: ${totalWaste.toLocaleString(undefined, {maximumFractionDigits: 2})} Tonnes. Recycling rate: ${recycleRate.toFixed(1)}%. Hazardous waste: ${totalWaste > 0 ? ((hazardousWaste / totalWaste) * 100).toFixed(1) : 0}% of total.`
    };
  }

  // ========== EV Transition Queries ==========

  getEVTransition(options: {
    year?: number;
    quarter?: number;
    market?: string;
    geography?: string;
    groupBy?: 'market' | 'geography' | 'quarter' | 'year';
  } = {}): SustainabilityResult {
    let data = [...this.evTransitionQuarterly];

    if (options.year) {
      data = data.filter(d => d.REPORTING_YEAR_NUMBER === options.year);
    }
    if (options.quarter) {
      data = data.filter(d => d.REPORTING_QUARTER_NUMBER === options.quarter);
    }
    if (options.market) {
      data = data.filter(d => d.SHE_MARKET_NAME.toLowerCase().includes(options.market!.toLowerCase()));
    }
    if (options.geography) {
      data = data.filter(d => d.SHE_GEOGRAPHY_NAME.toLowerCase().includes(options.geography!.toLowerCase()));
    }

    const totalBEV = data.reduce((sum, d) => sum + (Number(d.TOTAL_BEV_COUNT) || 0), 0);
    const totalFleet = data.reduce((sum, d) => sum + (Number(d.TOTAL_FLEET_ASSET_COUNT) || 0), 0);
    const bevPercentage = totalFleet > 0 ? (totalBEV / totalFleet) * 100 : 0;

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'market') {
      const byMarket = new Map<string, { bev: number; fleet: number }>();
      data.forEach(d => {
        const current = byMarket.get(d.SHE_MARKET_NAME) || { bev: 0, fleet: 0 };
        byMarket.set(d.SHE_MARKET_NAME, {
          bev: current.bev + (Number(d.TOTAL_BEV_COUNT) || 0),
          fleet: current.fleet + (Number(d.TOTAL_FLEET_ASSET_COUNT) || 0)
        });
      });
      breakdown = {
        dimension: 'Market',
        data: Array.from(byMarket.entries())
          .map(([label, { bev, fleet }]) => ({
            label,
            value: fleet > 0 ? Math.round((bev / fleet) * 1000) / 10 : 0
          }))
          .sort((a, b) => b.value - a.value)
      };
    } else if (options.groupBy === 'geography') {
      const byGeo = new Map<string, { bev: number; fleet: number }>();
      data.forEach(d => {
        const current = byGeo.get(d.SHE_GEOGRAPHY_NAME) || { bev: 0, fleet: 0 };
        byGeo.set(d.SHE_GEOGRAPHY_NAME, {
          bev: current.bev + (Number(d.TOTAL_BEV_COUNT) || 0),
          fleet: current.fleet + (Number(d.TOTAL_FLEET_ASSET_COUNT) || 0)
        });
      });
      breakdown = {
        dimension: 'Geography',
        data: Array.from(byGeo.entries())
          .map(([label, { bev, fleet }]) => ({
            label,
            value: fleet > 0 ? Math.round((bev / fleet) * 1000) / 10 : 0
          }))
          .sort((a, b) => b.value - a.value)
      };
    } else if (options.groupBy === 'year') {
      const byYear = new Map<number, { bev: number; fleet: number }>();
      data.forEach(d => {
        const current = byYear.get(d.REPORTING_YEAR_NUMBER) || { bev: 0, fleet: 0 };
        byYear.set(d.REPORTING_YEAR_NUMBER, {
          bev: current.bev + (Number(d.TOTAL_BEV_COUNT) || 0),
          fleet: current.fleet + (Number(d.TOTAL_FLEET_ASSET_COUNT) || 0)
        });
      });
      breakdown = {
        dimension: 'Year',
        data: Array.from(byYear.entries())
          .sort((a, b) => a[0] - b[0])
          .map(([label, { bev, fleet }]) => ({
            label: String(label),
            value: fleet > 0 ? Math.round((bev / fleet) * 1000) / 10 : 0
          }))
      };
    }

    return {
      dataType: 'ev_transition',
      metrics: ['Total BEV Count', 'Total Fleet Count', 'BEV Percentage'],
      dataPoints: [
        { label: 'Battery Electric Vehicles', value: totalBEV, unit: 'vehicles' },
        { label: 'Total Fleet', value: totalFleet, unit: 'vehicles' },
        { label: 'BEV Percentage', value: Math.round(bevPercentage * 10) / 10, unit: '%' }
      ],
      breakdown,
      summary: `EV Transition: ${totalBEV.toLocaleString()} BEVs out of ${totalFleet.toLocaleString()} total fleet vehicles (${bevPercentage.toFixed(1)}% electrified)`
    };
  }

  // ========== Metadata Queries ==========

  getAvailableSites(): string[] {
    const sites = new Set<string>();
    this.energyMonthly.forEach(d => sites.add(d.SHE_SITE_NAME));
    this.ghgEmissionsQuarterly.forEach(d => sites.add(d.SHE_SITE_NAME));
    this.waterMonthly.forEach(d => sites.add(d.SHE_SITE_NAME));
    this.wasteMonthly.forEach(d => sites.add(d.SHE_SITE_NAME));
    return [...sites].sort();
  }

  getAvailableYears(): number[] {
    const years = new Set<number>();
    this.energyMonthly.forEach(d => years.add(d.REPORTING_YEAR_NUMBER));
    this.ghgEmissionsQuarterly.forEach(d => years.add(d.REPORTING_YEAR_NUMBER));
    return [...years].sort();
  }

  getAvailableMarkets(): string[] {
    const markets = new Set<string>();
    this.evTransitionQuarterly.forEach(d => markets.add(d.SHE_MARKET_NAME));
    return [...markets].sort();
  }

  getAvailableGeographies(): string[] {
    const geos = new Set<string>();
    this.evTransitionQuarterly.forEach(d => geos.add(d.SHE_GEOGRAPHY_NAME));
    return [...geos].sort();
  }

  getDataSummary(): {
    tables: { name: string; rowCount: number; description: string }[];
    availableMetrics: string[];
    availableSites: string[];
    availableYears: number[];
  } {
    return {
      tables: [
        { name: 'Energy Monthly Summary', rowCount: this.energyMonthly.length, description: 'Monthly energy consumption by site' },
        { name: 'Energy Quarterly Summary', rowCount: this.energyQuarterly.length, description: 'Quarterly energy aggregates' },
        { name: 'GHG Emissions Monthly', rowCount: this.ghgEmissionsMonthly.length, description: 'Monthly greenhouse gas emissions by site (excluding road fleet)' },
        { name: 'GHG Emissions Quarterly', rowCount: this.ghgEmissionsQuarterly.length, description: 'Quarterly GHG with complete Scope 1 breakdown including road fleet' },
        { name: 'Waste Monthly', rowCount: this.wasteMonthly.length, description: 'Monthly waste generation by site' },
        { name: 'Water Monthly', rowCount: this.waterMonthly.length, description: 'Monthly water usage by site' },
        { name: 'EV Transition Quarterly', rowCount: this.evTransitionQuarterly.length, description: 'Electric vehicle fleet transition progress' }
      ],
      availableMetrics: [
        'Energy Consumption (MWh)',
        'Renewable Energy (MWh)',
        'GHG Emissions - Scope 1 (tCO2)',
        'GHG Emissions - Scope 2 (tCO2)',
        'Water Usage (Million m³)',
        'Waste Generated (Tonnes)',
        'Recycling Rate (%)',
        'BEV Count',
        'Fleet Electrification %'
      ],
      availableSites: this.getAvailableSites(),
      availableYears: this.getAvailableYears()
    };
  }

  // Generic query method for AI agent
  query(naturalLanguageHint: string): any {
    const hint = naturalLanguageHint.toLowerCase();

    if (hint.includes('energy')) {
      return this.getEnergyConsumption();
    } else if (hint.includes('emission') || hint.includes('ghg') || hint.includes('carbon') || hint.includes('co2')) {
      return this.getGHGEmissions();
    } else if (hint.includes('water')) {
      return this.getWaterUsage();
    } else if (hint.includes('waste') || hint.includes('recycl')) {
      return this.getWaste();
    } else if (hint.includes('ev') || hint.includes('electric') || hint.includes('vehicle') || hint.includes('fleet')) {
      return this.getEVTransition();
    } else {
      return this.getDataSummary();
    }
  }
}

// Singleton instance
let instance: SustainabilityDataRepository | null = null;

export function getSustainabilityDataRepository(): SustainabilityDataRepository {
  if (!instance) {
    instance = new SustainabilityDataRepository();
  }
  return instance;
}
