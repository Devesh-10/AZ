/**
 * Analytics Data Repository
 *
 * DATA PERIMETER: Foundational (Master Data) + KPI Summary Data
 * This repository uses KPI summary data for emissions, energy, waste, water
 * and transaction data for fleet analysis.
 *
 * Used by: Analyst Agent
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================
// MASTER DATA (Foundational) Types
// ============================================

interface SiteRecord {
  SHE_SITE_IDENTIFIER: number;
  SHE_SITE_CODE: string;
  SHE_SITE_NAME: string;
  COUNTRY_CODE: number;
  REPORTING_SCOPE_NAME: string;
  SRC_SYS_NM: string;
}

interface IndicatorRecord {
  SHE_INDICATOR_IDENTIFIER: number;
  SHE_INDICATOR_CODE: string;
  SHE_INDICATOR_NAME: string;
  SHE_INDICATOR_DESCRIPTION?: string;
  UNIT_OF_MEASURE?: string;
}

interface MeasurementTypeRecord {
  MEASUREMENT_TYPE_IDENTIFIER: number;
  MEASUREMENT_TYPE_NAME: string;
  MEASUREMENT_TYPE_DESCRIPTION?: string;
}

// ============================================
// TRANSACTION DATA Types (Fleet)
// ============================================

interface FleetAssetRecord {
  FLEET_ASSET_INVENTORY_IDENTIFIER: number;
  CAMPAIGN_IDENTIFIER: number;
  SHE_SITE_IDENTIFIER: number;
  SHE_INDICATOR_IDENTIFIER: number;
  MEASUREMENT_TYPE_IDENTIFIER: number;
  FLEET_ASSET_TYPE_IDENTIFIER: string;
  FLEET_FUEL_POWERTRAIN_TYPE_IDENTIFIER: string;
  FLEET_ASSET_COUNT: number;
  REPORTING_FREQUENCY_IDENTIFIER: number;
  REPORTING_PERIOD_START_DATE: number;
  SRC_SYS_NM: string;
}

// ============================================
// KPI Summary Data Types
// ============================================

interface GHGEmissionsQuarterlySummary {
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
  [key: string]: string | number;
}

interface EnergyMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_QUARTER_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  SHE_SITE_NAME: string;
  REPORTING_SCOPE_NAME: string;
  ENERGY_SITE_MWH_QUANTITY: number;
  ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY: number;
  ENERGY_IMPORTED_MWH_QUANTITY: number;
  [key: string]: string | number;
}

interface WasteMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  SHE_SITE_NAME: string;
  WASTE_TONNES_SITE_QUANTITY: number;
  WASTE_TONNES_PRODUCT_QUANTITY: number;
  [key: string]: string | number;
}

interface WaterMonthlySummary {
  REPORTING_YEAR_NUMBER: number;
  REPORTING_MONTH_NUMBER: number;
  SHE_SITE_NAME: string;
  GROUNDWATER_MILLION_M3_QUANTITY: number;
  MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY: number;
  [key: string]: string | number;
}

// ============================================
// Repository Class
// ============================================

class AnalyticsDataRepository {
  // Master Data (Foundational)
  private sites: SiteRecord[] = [];
  private indicators: IndicatorRecord[] = [];
  private measurementTypes: MeasurementTypeRecord[] = [];

  // Transaction Data (Fleet only)
  private fleetAssets: FleetAssetRecord[] = [];

  // KPI Summary Data (for emissions, energy, waste, water)
  private ghgEmissionsQuarterly: GHGEmissionsQuarterlySummary[] = [];
  private energyMonthly: EnergyMonthlySummary[] = [];
  private wasteMonthly: WasteMonthlySummary[] = [];
  private waterMonthly: WaterMonthlySummary[] = [];

  constructor() {
    this.loadData();
  }

  private loadData(): void {
    const dataDir = path.join(__dirname, '../data/json');

    // Load Master Data (Foundational)
    try {
      this.sites = this.loadJsonFile(path.join(dataDir, 'masterData/she_site.json')) || [];
      this.indicators = this.loadJsonFile(path.join(dataDir, 'masterData/she_indicator.json')) || [];
      this.measurementTypes = this.loadJsonFile(path.join(dataDir, 'masterData/measurement_type.json')) || [];
    } catch (e) {
      console.warn('[AnalyticsDataRepository] Could not load master data:', e);
    }

    // Load Transaction Data (Fleet)
    try {
      this.fleetAssets = this.loadJsonFile(path.join(dataDir, 'transactionData/fleet_asset_inventory.json')) || [];
    } catch (e) {
      console.warn('[AnalyticsDataRepository] Could not load fleet data:', e);
    }

    // Load KPI Summary Data (has actual values) - use MONTHLY data which has correct fields
    try {
      this.ghgEmissionsQuarterly = this.loadJsonFile(path.join(dataDir, 'kpi/greenhouse_gas_emissions_quarterly_summary.json')) || [];
      this.energyMonthly = this.loadJsonFile(path.join(dataDir, 'kpi/energy_monthly_summary.json')) || [];
      this.wasteMonthly = this.loadJsonFile(path.join(dataDir, 'kpi/waste_monthly_summary.json')) || [];
      this.waterMonthly = this.loadJsonFile(path.join(dataDir, 'kpi/water_monthly_summary.json')) || [];
    } catch (e) {
      console.warn('[AnalyticsDataRepository] Could not load KPI summary data:', e);
    }

    console.log('[AnalyticsDataRepository] Data loaded:');
    console.log(`  Master Data: ${this.sites.length} sites, ${this.indicators.length} indicators`);
    console.log(`  Fleet Data: ${this.fleetAssets.length} fleet assets`);
    console.log(`  KPI Data: ${this.ghgEmissionsQuarterly.length} GHG records, ${this.energyMonthly.length} energy records`);
  }

  private loadJsonFile<T>(filePath: string): T | null {
    try {
      if (fs.existsSync(filePath)) {
        const data = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(data);
      }
    } catch (e) {
      console.warn(`[AnalyticsDataRepository] Could not load ${filePath}:`, e);
    }
    return null;
  }

  // ============================================
  // MASTER DATA Queries
  // ============================================

  getSites(filter?: { siteName?: string; countryCode?: number }): SiteRecord[] {
    let results = this.sites;
    if (filter?.siteName) {
      results = results.filter(s =>
        s.SHE_SITE_NAME.toLowerCase().includes(filter.siteName!.toLowerCase())
      );
    }
    if (filter?.countryCode) {
      results = results.filter(s => s.COUNTRY_CODE === filter.countryCode);
    }
    return results;
  }

  getUniqueSiteNames(): string[] {
    return [...new Set(this.sites.map(s => s.SHE_SITE_NAME))];
  }

  getSiteById(siteId: number): SiteRecord | undefined {
    return this.sites.find(s => s.SHE_SITE_IDENTIFIER === siteId);
  }

  // ============================================
  // FLEET Analytics Queries
  // ============================================

  getFleetInventory(options?: {
    siteId?: number;
    assetType?: string;
    powertrainType?: string;
  }): { assetType: string; powertrainType: string; count: number; siteId: number }[] {
    let records = this.fleetAssets;

    if (options?.siteId) {
      records = records.filter(r => r.SHE_SITE_IDENTIFIER === options.siteId);
    }
    if (options?.assetType) {
      records = records.filter(r => r.FLEET_ASSET_TYPE_IDENTIFIER === options.assetType);
    }
    if (options?.powertrainType) {
      records = records.filter(r => r.FLEET_FUEL_POWERTRAIN_TYPE_IDENTIFIER === options.powertrainType);
    }

    return records.map(r => ({
      assetType: r.FLEET_ASSET_TYPE_IDENTIFIER,
      powertrainType: r.FLEET_FUEL_POWERTRAIN_TYPE_IDENTIFIER,
      count: r.FLEET_ASSET_COUNT,
      siteId: r.SHE_SITE_IDENTIFIER
    }));
  }

  getFleetByPowertrainType(): { powertrainType: string; totalCount: number }[] {
    const byPowertrain = new Map<string, number>();

    this.fleetAssets.forEach(r => {
      const current = byPowertrain.get(r.FLEET_FUEL_POWERTRAIN_TYPE_IDENTIFIER) || 0;
      byPowertrain.set(r.FLEET_FUEL_POWERTRAIN_TYPE_IDENTIFIER, current + r.FLEET_ASSET_COUNT);
    });

    return Array.from(byPowertrain.entries()).map(([powertrainType, totalCount]) => ({
      powertrainType,
      totalCount
    }));
  }

  getEVAnalysis(): {
    totalFleet: number;
    electricVehicles: number;
    hybridVehicles: number;
    conventionalVehicles: number;
    evPercentage: number;
  } {
    const byPowertrain = this.getFleetByPowertrainType();

    let electricVehicles = 0;
    let hybridVehicles = 0;
    let conventionalVehicles = 0;

    byPowertrain.forEach(({ powertrainType, totalCount }) => {
      const type = powertrainType.toLowerCase();
      if (type.includes('electric') || type === 'bev') {
        electricVehicles += totalCount;
      } else if (type.includes('hybrid') || type === 'phev') {
        hybridVehicles += totalCount;
      } else {
        conventionalVehicles += totalCount;
      }
    });

    const totalFleet = electricVehicles + hybridVehicles + conventionalVehicles;
    const evPercentage = totalFleet > 0 ? (electricVehicles / totalFleet) * 100 : 0;

    return {
      totalFleet,
      electricVehicles,
      hybridVehicles,
      conventionalVehicles,
      evPercentage: Math.round(evPercentage * 10) / 10
    };
  }

  // ============================================
  // ENERGY Analytics Queries (using KPI summary)
  // ============================================

  getEnergyConsumptionDetails(options?: {
    siteId?: number;
    energyType?: string;
  }): { siteId: number; energyType: string; value: number; unit: string }[] {
    // Aggregate energy by site from quarterly summary
    const results: { siteId: number; energyType: string; value: number; unit: string }[] = [];

    const bySite = new Map<string, number>();
    this.energyMonthly.forEach(r => {
      const current = bySite.get(r.SHE_SITE_NAME) || 0;
      bySite.set(r.SHE_SITE_NAME, current + (r.ENERGY_SITE_MWH_QUANTITY || 0));
    });

    bySite.forEach((value, siteName) => {
      results.push({
        siteId: 0,
        energyType: siteName,
        value: Math.round(value * 100) / 100,
        unit: 'MWh'
      });
    });

    return results;
  }

  getEnergyByType(): { energyType: string; totalValue: number }[] {
    // Aggregate by energy type from quarterly data
    let totalSite = 0;
    let totalRenewable = 0;
    let totalImported = 0;

    this.energyMonthly.forEach(r => {
      totalSite += r.ENERGY_SITE_MWH_QUANTITY || 0;
      totalRenewable += r.ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY || 0;
      totalImported += r.ENERGY_IMPORTED_MWH_QUANTITY || 0;
    });

    return [
      { energyType: 'Total Site Energy', totalValue: Math.round(totalSite * 100) / 100 },
      { energyType: 'Renewable Energy', totalValue: Math.round(totalRenewable * 100) / 100 },
      { energyType: 'Imported Energy', totalValue: Math.round(totalImported * 100) / 100 }
    ];
  }

  // ============================================
  // EMISSIONS Analytics Queries (using KPI summary)
  // ============================================

  getEmissionsDetails(options?: {
    siteId?: number;
    scopeType?: string;
    emissionSource?: string;
  }): { siteId: number; scopeType: string; emissionSource: string; value: number; unit: string }[] {
    const results: { siteId: number; scopeType: string; emissionSource: string; value: number; unit: string }[] = [];

    // Aggregate by site
    const bySite = new Map<string, { scope1: number; scope2: number }>();

    this.ghgEmissionsQuarterly.forEach(r => {
      const existing = bySite.get(r.SHE_SITE_NAME) || { scope1: 0, scope2: 0 };
      existing.scope1 += r.SCOPE1_TOTAL_TCO2_QUANTITY || 0;
      existing.scope2 += r.SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY || 0;
      bySite.set(r.SHE_SITE_NAME, existing);
    });

    bySite.forEach((values, siteName) => {
      results.push({
        siteId: 0,
        scopeType: 'Scope 1',
        emissionSource: siteName,
        value: Math.round(values.scope1 * 100) / 100,
        unit: 'tCO2e'
      });
      results.push({
        siteId: 0,
        scopeType: 'Scope 2',
        emissionSource: siteName,
        value: Math.round(values.scope2 * 100) / 100,
        unit: 'tCO2e'
      });
    });

    return results;
  }

  getEmissionsByScope(): { scopeType: string; totalValue: number }[] {
    let scope1RoadFleet = 0;
    let scope1FGases = 0;
    let scope1SiteEnergy = 0;
    let scope1Total = 0;
    let scope2MarketBased = 0;
    let scope2LocationBased = 0;

    this.ghgEmissionsQuarterly.forEach(r => {
      scope1RoadFleet += r.SCOPE1_ROAD_FLEET_TCO2_QUANTITY || 0;
      scope1FGases += r.SCOPE1_F_GASES_TCO2_QUANTITY || 0;
      scope1SiteEnergy += r.SCOPE1_SITE_ENERGY_TCO2_QUANTITY || 0;
      scope1Total += r.SCOPE1_TOTAL_TCO2_QUANTITY || 0;
      scope2MarketBased += r.SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY || 0;
      scope2LocationBased += r.SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY || 0;
    });

    return [
      { scopeType: 'Scope 1 Road Fleet', totalValue: Math.round(scope1RoadFleet * 100) / 100 },
      { scopeType: 'Scope 1 F-Gases', totalValue: Math.round(scope1FGases * 100) / 100 },
      { scopeType: 'Scope 1 Site Energy', totalValue: Math.round(scope1SiteEnergy * 100) / 100 },
      { scopeType: 'Scope 1 Total', totalValue: Math.round(scope1Total * 100) / 100 },
      { scopeType: 'Scope 2 Market-Based', totalValue: Math.round(scope2MarketBased * 100) / 100 },
      { scopeType: 'Scope 2 Location-Based', totalValue: Math.round(scope2LocationBased * 100) / 100 }
    ];
  }

  // ============================================
  // WASTE Analytics Queries (using KPI summary)
  // ============================================

  getWasteDetails(options?: {
    siteId?: number;
    wasteType?: string;
  }): { siteId: number; wasteType: string; value: number; unit: string }[] {
    const bySite = new Map<string, number>();

    this.wasteMonthly.forEach(r => {
      const current = bySite.get(r.SHE_SITE_NAME) || 0;
      bySite.set(r.SHE_SITE_NAME, current + (r.WASTE_TONNES_SITE_QUANTITY || 0));
    });

    return Array.from(bySite.entries()).map(([siteName, value]) => ({
      siteId: 0,
      wasteType: siteName,
      value: Math.round(value * 100) / 100,
      unit: 'tonnes'
    }));
  }

  getWasteByType(): { wasteType: string; totalValue: number }[] {
    let totalSite = 0;
    let totalProduct = 0;

    this.wasteMonthly.forEach(r => {
      totalSite += r.WASTE_TONNES_SITE_QUANTITY || 0;
      totalProduct += r.WASTE_TONNES_PRODUCT_QUANTITY || 0;
    });

    return [
      { wasteType: 'Site Waste', totalValue: Math.round(totalSite * 100) / 100 },
      { wasteType: 'Product Waste', totalValue: Math.round(totalProduct * 100) / 100 }
    ];
  }

  // ============================================
  // WATER Analytics Queries (using KPI summary)
  // ============================================

  getWaterUsageDetails(options?: {
    siteId?: number;
    waterSource?: string;
  }): { siteId: number; waterSource: string; value: number; unit: string }[] {
    const bySite = new Map<string, number>();

    this.waterMonthly.forEach(r => {
      const current = bySite.get(r.SHE_SITE_NAME) || 0;
      const total = (r.GROUNDWATER_MILLION_M3_QUANTITY || 0) + (r.MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY || 0);
      bySite.set(r.SHE_SITE_NAME, current + total);
    });

    return Array.from(bySite.entries()).map(([siteName, value]) => ({
      siteId: 0,
      waterSource: siteName,
      value: Math.round(value * 1000000) / 1000000, // Keep precision for small values
      unit: 'Million m³'
    }));
  }

  getWaterBySource(): { waterSource: string; totalValue: number }[] {
    let totalGroundwater = 0;
    let totalMunicipal = 0;

    this.waterMonthly.forEach(r => {
      totalGroundwater += r.GROUNDWATER_MILLION_M3_QUANTITY || 0;
      totalMunicipal += r.MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY || 0;
    });

    return [
      { waterSource: 'Groundwater', totalValue: Math.round(totalGroundwater * 1000000) / 1000000 },
      { waterSource: 'Municipal Supply', totalValue: Math.round(totalMunicipal * 1000000) / 1000000 }
    ];
  }

  // ============================================
  // Cross-Domain Analysis
  // ============================================

  getSitePerformanceSummary(siteId: number): {
    siteName: string | undefined;
    fleetCount: number;
    evCount: number;
    energyRecords: number;
    emissionRecords: number;
    wasteRecords: number;
    waterRecords: number;
  } {
    const site = this.getSiteById(siteId);
    const fleet = this.getFleetInventory({ siteId });

    const totalFleet = fleet.reduce((sum, f) => sum + f.count, 0);
    const evCount = fleet
      .filter(f => f.powertrainType.toLowerCase().includes('electric'))
      .reduce((sum, f) => sum + f.count, 0);

    return {
      siteName: site?.SHE_SITE_NAME,
      fleetCount: totalFleet,
      evCount,
      energyRecords: this.energyMonthly.length,
      emissionRecords: this.ghgEmissionsQuarterly.length,
      wasteRecords: this.wasteMonthly.length,
      waterRecords: this.waterMonthly.length
    };
  }

  // ============================================
  // Data Summary
  // ============================================

  getDataSummary(): {
    masterData: { sites: number; indicators: number; measurementTypes: number };
    transactionData: {
      fleetAssets: number;
      fleetFuelConsumption: number;
      fleetMileage: number;
      energyConsumption: number;
      ghgEmissions: number;
      wasteRecords: number;
      waterUsage: number;
    };
  } {
    return {
      masterData: {
        sites: this.sites.length,
        indicators: this.indicators.length,
        measurementTypes: this.measurementTypes.length
      },
      transactionData: {
        fleetAssets: this.fleetAssets.length,
        fleetFuelConsumption: 0,
        fleetMileage: 0,
        energyConsumption: this.energyMonthly.length,
        ghgEmissions: this.ghgEmissionsQuarterly.length,
        wasteRecords: this.wasteMonthly.length,
        waterUsage: this.waterMonthly.length
      }
    };
  }
}

// Singleton instance
let analyticsRepository: AnalyticsDataRepository | null = null;

export function getAnalyticsDataRepository(): AnalyticsDataRepository {
  if (!analyticsRepository) {
    analyticsRepository = new AnalyticsDataRepository();
  }
  return analyticsRepository;
}

export { AnalyticsDataRepository };
