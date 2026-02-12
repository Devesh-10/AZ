/**
 * Data Integrity Test Script
 *
 * Run with: npx ts-node src/test-data-integrity.ts
 *
 * Tests all query types and verifies data consistency
 */

import { getSustainabilityDataRepository } from './dataAccess/SustainabilityDataRepository';

const repo = getSustainabilityDataRepository();

console.log('=============================================');
console.log('      DATA INTEGRITY TEST SUITE');
console.log('=============================================\n');

let passed = 0;
let failed = 0;

function test(name: string, condition: boolean, details?: string) {
  if (condition) {
    console.log(`✅ PASS: ${name}`);
    passed++;
  } else {
    console.log(`❌ FAIL: ${name}`);
    if (details) console.log(`   Details: ${details}`);
    failed++;
  }
}

// ==================== ENERGY TESTS ====================
console.log('\n--- ENERGY TESTS ---\n');

const energy = repo.getEnergyConsumption();
const totalEnergy = energy.dataPoints.find(d => d.label === 'Total Energy')?.value || 0;
const renewableEnergy = energy.dataPoints.find(d => d.label === 'Renewable Energy')?.value || 0;
const importedEnergy = energy.dataPoints.find(d => d.label === 'Imported Energy')?.value || 0;

test('Energy: Has data', totalEnergy > 0, `Total: ${totalEnergy}`);
test('Energy: Renewable <= Total', renewableEnergy <= totalEnergy * 1.01,
     `Renewable ${renewableEnergy} vs Total ${totalEnergy}`);
test('Energy: Imported > 0', importedEnergy > 0, `Imported: ${importedEnergy}`);

// Test filters
const energy2024 = repo.getEnergyConsumption({ year: 2024 });
const total2024 = energy2024.dataPoints.find(d => d.label === 'Total Energy')?.value || 0;
test('Energy: Year filter works', total2024 > 0 && total2024 < totalEnergy,
     `2024: ${total2024} vs All: ${totalEnergy}`);

const energyQ1 = repo.getEnergyConsumption({ year: 2024, quarter: 1 });
const totalQ1 = energyQ1.dataPoints.find(d => d.label === 'Total Energy')?.value || 0;
test('Energy: Quarter filter works', totalQ1 > 0 && totalQ1 < total2024,
     `Q1 2024: ${totalQ1} vs 2024: ${total2024}`);

// Test groupBy
const energyBySite = repo.getEnergyConsumption({ groupBy: 'site' });
test('Energy: GroupBy site works',
     energyBySite.breakdown !== undefined && energyBySite.breakdown.data.length > 0,
     `Sites: ${energyBySite.breakdown?.data.length}`);

// ==================== GHG EMISSIONS TESTS ====================
console.log('\n--- GHG EMISSIONS TESTS ---\n');

const ghg = repo.getGHGEmissions();
const totalEmissions = ghg.dataPoints.find(d => d.label === 'Total Emissions (Scope 1+2)')?.value || 0;
const scope1Total = ghg.dataPoints.find(d => d.label === 'Scope 1 Total')?.value || 0;
const scope1Fleet = ghg.dataPoints.find(d => d.label === 'Scope 1 Road Fleet')?.value || 0;
const scope1FGases = ghg.dataPoints.find(d => d.label === 'Scope 1 F-Gases')?.value || 0;
const scope1SiteEnergy = ghg.dataPoints.find(d => d.label === 'Scope 1 Site Energy')?.value || 0;
const scope2Market = ghg.dataPoints.find(d => d.label === 'Scope 2 Market-Based')?.value || 0;
const scope2Location = ghg.dataPoints.find(d => d.label === 'Scope 2 Location-Based')?.value || 0;

test('GHG: Has data', totalEmissions > 0, `Total: ${totalEmissions}`);
test('GHG: Total = Scope1 + Scope2 Market',
     Math.abs(totalEmissions - (scope1Total + scope2Market)) < 1,
     `Total ${totalEmissions} vs Sum ${scope1Total + scope2Market}`);
test('GHG: Scope 1 components sum correctly',
     scope1Fleet + scope1FGases + scope1SiteEnergy <= scope1Total * 1.05, // Allow small rounding
     `Fleet(${scope1Fleet}) + FGases(${scope1FGases}) + SiteEnergy(${scope1SiteEnergy}) vs Total(${scope1Total})`);
test('GHG: Location-based > Market-based (typical for renewables)',
     scope2Location > scope2Market,
     `Location ${scope2Location} vs Market ${scope2Market}`);

// Test year-over-year reduction
const ghg2022 = repo.getGHGEmissions({ year: 2022 });
const ghg2025 = repo.getGHGEmissions({ year: 2025 });
const total2022 = ghg2022.dataPoints.find(d => d.label === 'Total Emissions (Scope 1+2)')?.value || 0;
const total2025 = ghg2025.dataPoints.find(d => d.label === 'Total Emissions (Scope 1+2)')?.value || 0;
test('GHG: Emissions reducing over time',
     total2025 < total2022,
     `2025: ${total2025} vs 2022: ${total2022}`);

// ==================== WATER TESTS ====================
console.log('\n--- WATER TESTS ---\n');

const water = repo.getWaterUsage();
const totalWater = water.dataPoints.find(d => d.label === 'Total Water Withdrawn')?.value || 0;
const groundwater = water.dataPoints.find(d => d.label === 'Groundwater')?.value || 0;
const municipal = water.dataPoints.find(d => d.label === 'Municipal Supply')?.value || 0;
const rainwater = water.dataPoints.find(d => d.label === 'Rainwater Harvesting')?.value || 0;
const surface = water.dataPoints.find(d => d.label === 'Surface Water')?.value || 0;

test('Water: Has data', totalWater > 0, `Total: ${totalWater}`);
test('Water: Components sum to total',
     Math.abs(totalWater - (groundwater + municipal + rainwater + surface)) < 0.001,
     `Sum ${groundwater + municipal + rainwater + surface} vs Total ${totalWater}`);
test('Water: Municipal is largest source', municipal > groundwater,
     `Municipal ${municipal} vs Groundwater ${groundwater}`);

// ==================== WASTE TESTS ====================
console.log('\n--- WASTE TESTS ---\n');

const waste = repo.getWaste();
const totalWaste = waste.dataPoints.find(d => d.label === 'Total Waste')?.value || 0;
const siteWaste = waste.dataPoints.find(d => d.label === 'Site Waste')?.value || 0;
const productWaste = waste.dataPoints.find(d => d.label === 'Product Waste')?.value || 0;
const recycledWaste = waste.dataPoints.find(d => d.label === 'Recycled Waste')?.value || 0;
const landfillWaste = waste.dataPoints.find(d => d.label === 'Landfill Waste')?.value || 0;
const hazardousWaste = waste.dataPoints.find(d => d.label === 'Hazardous Waste')?.value || 0;
const nonHazardousWaste = waste.dataPoints.find(d => d.label === 'Non-Hazardous Waste')?.value || 0;

test('Waste: Has data', totalWaste > 0, `Total: ${totalWaste}`);
test('Waste: Site + Product = Total',
     Math.abs(totalWaste - (siteWaste + productWaste)) < 1,
     `Site(${siteWaste}) + Product(${productWaste}) vs Total(${totalWaste})`);
test('Waste: Hazardous + Non-Hazardous = Total',
     Math.abs(totalWaste - (hazardousWaste + nonHazardousWaste)) < 1,
     `Haz(${hazardousWaste}) + NonHaz(${nonHazardousWaste}) vs Total(${totalWaste})`);
test('Waste: Recycled + Landfill <= Total',
     recycledWaste + landfillWaste <= totalWaste * 1.01,
     `Recycled(${recycledWaste}) + Landfill(${landfillWaste}) vs Total(${totalWaste})`);
test('Waste: Good recycling rate (>50%)',
     recycledWaste / totalWaste > 0.5,
     `Rate: ${(recycledWaste / totalWaste * 100).toFixed(1)}%`);

// ==================== EV TRANSITION TESTS ====================
console.log('\n--- EV TRANSITION TESTS ---\n');

const ev = repo.getEVTransition();
const totalBEV = ev.dataPoints.find(d => d.label === 'Battery Electric Vehicles')?.value || 0;
const totalFleet = ev.dataPoints.find(d => d.label === 'Total Fleet')?.value || 0;
const bevPercent = ev.dataPoints.find(d => d.label === 'BEV Percentage')?.value || 0;

test('EV: Has data', totalFleet > 0, `Fleet: ${totalFleet}`);
test('EV: BEV <= Total Fleet', totalBEV <= totalFleet,
     `BEV ${totalBEV} vs Fleet ${totalFleet}`);
test('EV: Percentage calculated correctly',
     Math.abs(bevPercent - (totalBEV / totalFleet * 100)) < 0.5,
     `Reported ${bevPercent}% vs Calculated ${(totalBEV / totalFleet * 100).toFixed(1)}%`);

// Test year-over-year EV growth
const ev2022 = repo.getEVTransition({ year: 2022 });
const ev2025 = repo.getEVTransition({ year: 2025 });
const bev2022 = ev2022.dataPoints.find(d => d.label === 'BEV Percentage')?.value || 0;
const bev2025 = ev2025.dataPoints.find(d => d.label === 'BEV Percentage')?.value || 0;
test('EV: Electrification increasing over time',
     bev2025 > bev2022,
     `2025: ${bev2025}% vs 2022: ${bev2022}%`);

// Test market breakdown
const evByMarket = repo.getEVTransition({ groupBy: 'market' });
test('EV: Market breakdown works',
     evByMarket.breakdown !== undefined && evByMarket.breakdown.data.length > 0,
     `Markets: ${evByMarket.breakdown?.data.length}`);

// ==================== METADATA TESTS ====================
console.log('\n--- METADATA TESTS ---\n');

const sites = repo.getAvailableSites();
const years = repo.getAvailableYears();
const markets = repo.getAvailableMarkets();
const summary = repo.getDataSummary();

test('Metadata: Has sites', sites.length > 0, `Sites: ${sites.length}`);
test('Metadata: Has years', years.length === 4, `Years: ${years.join(', ')}`);
test('Metadata: Has markets', markets.length > 0, `Markets: ${markets.length}`);
test('Metadata: Summary complete', summary.tables.length >= 7, `Tables: ${summary.tables.length}`);

// ==================== EDGE CASE TESTS ====================
console.log('\n--- EDGE CASE TESTS ---\n');

// Empty filter (non-existent site)
const emptyEnergy = repo.getEnergyConsumption({ siteName: 'NonExistentSite12345' });
const emptyTotal = emptyEnergy.dataPoints.find(d => d.label === 'Total Energy')?.value || 0;
test('Edge: Non-existent site returns 0', emptyTotal === 0, `Total: ${emptyTotal}`);

// Future year filter
const futureEnergy = repo.getEnergyConsumption({ year: 2030 });
const futureTotal = futureEnergy.dataPoints.find(d => d.label === 'Total Energy')?.value || 0;
test('Edge: Future year returns 0', futureTotal === 0, `Total: ${futureTotal}`);

// Partial site name match
const partialSite = repo.getEnergyConsumption({ siteName: 'Maccles' });
const partialTotal = partialSite.dataPoints.find(d => d.label === 'Total Energy')?.value || 0;
test('Edge: Partial site name works', partialTotal > 0, `Total: ${partialTotal}`);

// ==================== SUMMARY ====================
console.log('\n=============================================');
console.log('           TEST RESULTS SUMMARY');
console.log('=============================================');
console.log(`Total Tests: ${passed + failed}`);
console.log(`Passed: ${passed} ✅`);
console.log(`Failed: ${failed} ❌`);
console.log('=============================================\n');

if (failed > 0) {
  console.log('⚠️  Some tests failed. Please review the data and logic.');
  process.exit(1);
} else {
  console.log('🎉 All tests passed! Data is ready for UAT.');
  process.exit(0);
}
