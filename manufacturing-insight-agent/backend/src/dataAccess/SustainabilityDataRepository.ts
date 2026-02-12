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

// Data types based on your Excel structure
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

export interface GHGEmissionsMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  REPORTING_SCOPE_NAME: string;
  SCOPE1_F_GASES_TCO2_QUANTITY: number;
  SCOPE1_ROAD_FLEET_TCO2_QUANTITY: number;
  SCOPE2_MARKET_BASED_TCO2_QUANTITY: number;
  SCOPE2_LOCATION_BASED_TCO2_QUANTITY: number;
  [key: string]: string | number;
}

export interface WasteMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  WASTE_TONNES_SITE_QUANTITY: number;
  WASTE_TONNES_PRODUCT_QUANTITY: number;
  [key: string]: string | number;
}

export interface WaterMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_SITE_NAME: string;
  GROUNDWATER_MILLION_M3_QUANTITY: number;
  MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY: number;
  [key: string]: string | number;
}

export interface EVTransitionQuarterlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  SHE_MARKET_NAME: string;
  SHE_GEOGRAPHY_NAME: string;
  TOTAL_BEV_COUNT: number;
  TOTAL_FLEET_ASSET_COUNT: number;
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
  private ghgEmissionsQuarterly: any[] = [];
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
      console.log(`  - GHG Emissions Monthly: ${this.ghgEmissionsMonthly.length} rows`);
      console.log(`  - Waste Monthly: ${this.wasteMonthly.length} rows`);
      console.log(`  - Water Monthly: ${this.waterMonthly.length} rows`);
      console.log(`  - EV Transition Quarterly: ${this.evTransitionQuarterly.length} rows`);
      console.log(`  - Sites: ${this.sheSites.length} rows`);
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
    const importedEnergy = data.reduce((sum, d) => sum + (d.ENERGY_IMPORTED_MWH_QUANTITY || 0), 0);

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'site') {
      const bysite = new Map<string, number>();
      data.forEach(d => {
        const current = bysite.get(d.SHE_SITE_NAME) || 0;
        bysite.set(d.SHE_SITE_NAME, current + (d.ENERGY_SITE_MWH_QUANTITY || 0));
      });
      breakdown = {
        dimension: 'Site',
        data: Array.from(bysite.entries()).map(([label, value]) => ({ label, value }))
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
          .map(([label, value]) => ({ label, value }))
      };
    }

    return {
      dataType: 'energy',
      metrics: ['Total Energy (MWh)', 'Renewable Energy (MWh)', 'Imported Energy (MWh)'],
      dataPoints: [
        { label: 'Total Energy', value: Math.round(totalEnergy * 100) / 100, unit: 'MWh' },
        { label: 'Renewable Energy', value: Math.round(renewableEnergy * 100) / 100, unit: 'MWh' },
        { label: 'Imported Energy', value: Math.round(importedEnergy * 100) / 100, unit: 'MWh' }
      ],
      breakdown,
      summary: `Total energy consumption: ${totalEnergy.toFixed(2)} MWh, of which ${renewableEnergy.toFixed(2)} MWh is renewable (${((renewableEnergy/totalEnergy)*100).toFixed(1)}%)`
    };
  }

  // ========== GHG Emissions Queries ==========

  getGHGEmissions(options: {
    year?: number;
    quarter?: number;
    month?: number;
    siteName?: string;
    scope?: string;
    groupBy?: 'site' | 'month' | 'quarter' | 'year';
  } = {}): SustainabilityResult {
    let data = [...this.ghgEmissionsMonthly];

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
    if (options.scope) {
      data = data.filter(d => d.REPORTING_SCOPE_NAME.toLowerCase().includes(options.scope!.toLowerCase()));
    }

    const scope1FGases = data.reduce((sum, d) => sum + (Number(d.SCOPE1_F_GASES_TCO2_QUANTITY) || 0), 0);
    const scope1Fleet = data.reduce((sum, d) => sum + (Number(d.SCOPE1_ROAD_FLEET_TCO2_QUANTITY) || 0), 0);
    const scope2Market = data.reduce((sum, d) => sum + (Number(d.SCOPE2_MARKET_BASED_TCO2_QUANTITY) || 0), 0);
    const scope2Location = data.reduce((sum, d) => sum + (Number(d.SCOPE2_LOCATION_BASED_TCO2_QUANTITY) || 0), 0);

    let breakdown: { dimension: string; data: { label: string; value: number }[] } | undefined;

    if (options.groupBy === 'site') {
      const bySite = new Map<string, number>();
      data.forEach(d => {
        const total = (Number(d.SCOPE1_F_GASES_TCO2_QUANTITY) || 0) +
                     (Number(d.SCOPE1_ROAD_FLEET_TCO2_QUANTITY) || 0) +
                     (Number(d.SCOPE2_MARKET_BASED_TCO2_QUANTITY) || 0);
        const current = bySite.get(d.SHE_SITE_NAME) || 0;
        bySite.set(d.SHE_SITE_NAME, current + total);
      });
      breakdown = {
        dimension: 'Site',
        data: Array.from(bySite.entries()).map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
      };
    }

    const totalEmissions = scope1FGases + scope1Fleet + scope2Market;

    return {
      dataType: 'ghg_emissions',
      metrics: ['Scope 1 F-Gases (tCO2)', 'Scope 1 Road Fleet (tCO2)', 'Scope 2 Market-Based (tCO2)', 'Scope 2 Location-Based (tCO2)'],
      dataPoints: [
        { label: 'Scope 1 F-Gases', value: Math.round(scope1FGases * 100) / 100, unit: 'tCO2' },
        { label: 'Scope 1 Road Fleet', value: Math.round(scope1Fleet * 100) / 100, unit: 'tCO2' },
        { label: 'Scope 2 Market-Based', value: Math.round(scope2Market * 100) / 100, unit: 'tCO2' },
        { label: 'Scope 2 Location-Based', value: Math.round(scope2Location * 100) / 100, unit: 'tCO2' }
      ],
      breakdown,
      summary: `Total GHG emissions: ${totalEmissions.toFixed(2)} tCO2 (Scope 1: ${(scope1FGases + scope1Fleet).toFixed(2)} tCO2, Scope 2 Market-based: ${scope2Market.toFixed(2)} tCO2)`
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
    const totalWater = groundwater + municipal;

    return {
      dataType: 'water',
      metrics: ['Groundwater (Million m³)', 'Municipal Supply (Million m³)'],
      dataPoints: [
        { label: 'Groundwater', value: Math.round(groundwater * 1000) / 1000, unit: 'Million m³' },
        { label: 'Municipal Supply', value: Math.round(municipal * 1000) / 1000, unit: 'Million m³' },
        { label: 'Total Water', value: Math.round(totalWater * 1000) / 1000, unit: 'Million m³' }
      ],
      summary: `Total water usage: ${totalWater.toFixed(4)} Million m³ (Groundwater: ${groundwater.toFixed(4)}, Municipal: ${municipal.toFixed(4)})`
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

    return {
      dataType: 'waste',
      metrics: ['Site Waste (Tonnes)', 'Product Waste (Tonnes)'],
      dataPoints: [
        { label: 'Site Waste', value: Math.round(siteWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Product Waste', value: Math.round(productWaste * 100) / 100, unit: 'Tonnes' },
        { label: 'Total Waste', value: Math.round((siteWaste + productWaste) * 100) / 100, unit: 'Tonnes' }
      ],
      summary: `Total waste: ${(siteWaste + productWaste).toFixed(2)} Tonnes (Site: ${siteWaste.toFixed(2)}, Product: ${productWaste.toFixed(2)})`
    };
  }

  // ========== EV Transition Queries ==========

  getEVTransition(options: {
    year?: number;
    quarter?: number;
    market?: string;
    geography?: string;
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

    return {
      dataType: 'ev_transition',
      metrics: ['Total BEV Count', 'Total Fleet Count', 'BEV Percentage'],
      dataPoints: [
        { label: 'Battery Electric Vehicles', value: totalBEV, unit: 'vehicles' },
        { label: 'Total Fleet', value: totalFleet, unit: 'vehicles' },
        { label: 'BEV Percentage', value: Math.round(bevPercentage * 10) / 10, unit: '%' }
      ],
      summary: `EV Transition: ${totalBEV} BEVs out of ${totalFleet} total fleet vehicles (${bevPercentage.toFixed(1)}% electrified)`
    };
  }

  // ========== Metadata Queries ==========

  getAvailableSites(): string[] {
    return [...new Set(this.sheSites.map(s => s.SHE_SITE_NAME))].sort();
  }

  getAvailableYears(): number[] {
    const years = new Set<number>();
    this.energyMonthly.forEach(d => years.add(d.REPORTING_YEAR_NUMBER));
    this.ghgEmissionsMonthly.forEach(d => years.add(d.REPORTING_YEAR_NUMBER));
    return [...years].sort();
  }

  getDataSummary(): {
    tables: { name: string; rowCount: number; description: string }[];
    availableMetrics: string[];
  } {
    return {
      tables: [
        { name: 'Energy Monthly Summary', rowCount: this.energyMonthly.length, description: 'Monthly energy consumption by site' },
        { name: 'Energy Quarterly Summary', rowCount: this.energyQuarterly.length, description: 'Quarterly energy aggregates' },
        { name: 'GHG Emissions Monthly', rowCount: this.ghgEmissionsMonthly.length, description: 'Monthly greenhouse gas emissions by site and scope' },
        { name: 'GHG Emissions Quarterly', rowCount: this.ghgEmissionsQuarterly.length, description: 'Quarterly GHG aggregates' },
        { name: 'Waste Monthly', rowCount: this.wasteMonthly.length, description: 'Monthly waste generation by site' },
        { name: 'Water Monthly', rowCount: this.waterMonthly.length, description: 'Monthly water usage by site' },
        { name: 'EV Transition Quarterly', rowCount: this.evTransitionQuarterly.length, description: 'Electric vehicle fleet transition progress' },
        { name: 'Sites', rowCount: this.sheSites.length, description: 'Site master data' },
        { name: 'Indicators', rowCount: this.sheIndicators.length, description: 'KPI indicator definitions' }
      ],
      availableMetrics: [
        'Energy Consumption (MWh)',
        'Renewable Energy (MWh)',
        'GHG Emissions - Scope 1 (tCO2)',
        'GHG Emissions - Scope 2 (tCO2)',
        'Water Usage (Million m³)',
        'Waste Generated (Tonnes)',
        'BEV Count',
        'Fleet Electrification %'
      ]
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
    } else if (hint.includes('waste')) {
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
