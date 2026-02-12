/**
 * Data Configuration
 *
 * This file provides documentation and utilities for configuring your KPI data source.
 *
 * QUICK START:
 * 1. The default data is in backend/src/data/kpiMart.json
 * 2. Replace it with your own data following the schema below
 * 3. Redeploy the Lambda
 *
 * DATA SCHEMA:
 * Each row in kpiMart.json should have:
 * {
 *   "date": "YYYY-MM-DD",    // Required: Date of the measurement
 *   "region": "string",       // Required: Geographic region
 *   "product": "string",      // Required: Product name/category
 *   "segment": "string",      // Optional: Customer segment
 *   "kpi": "string",          // Required: KPI name (e.g., "revenue", "cost")
 *   "value": number           // Required: Numeric value
 * }
 *
 * SUPPORTED KPI NAMES (can be extended):
 * - revenue: Total revenue in currency units
 * - cost: Total costs in currency units
 * - margin_pct: Profit margin as percentage
 * - units_sold: Number of units sold
 * - customer_count: Number of customers
 *
 * SUPPORTED DIMENSIONS:
 * - date: Time dimension (supports groupBy: "date" or "month")
 * - region: Geographic dimension
 * - product: Product dimension
 * - segment: Customer segment dimension
 *
 * EXAMPLE CONVERSION FROM CSV:
 * If you have a CSV file, use the script at scripts/convertCsvToJson.ts
 * Run: npx ts-node scripts/convertCsvToJson.ts input.csv output.json
 */

export const DATA_CONFIG = {
  // Path to KPI data (relative to backend/src/)
  kpiMartPath: "./data/kpiMart.json",

  // Path to knowledge graph metadata
  knowledgeGraphPath: "./data/knowledgeGraph.json",

  // Supported KPI names - add your custom KPIs here
  supportedKpis: [
    "revenue",
    "cost",
    "margin_pct",
    "units_sold",
    "customer_count",
  ],

  // Supported dimensions for filtering/grouping
  supportedDimensions: ["date", "month", "region", "product", "segment"],

  // Date format expected in the data
  dateFormat: "YYYY-MM-DD",
};

/**
 * Validates that a data row has all required fields
 */
export function validateDataRow(row: Record<string, unknown>): boolean {
  const requiredFields = ["date", "region", "product", "kpi", "value"];

  for (const field of requiredFields) {
    if (!(field in row)) {
      console.error(`Missing required field: ${field}`);
      return false;
    }
  }

  if (typeof row.value !== "number") {
    console.error(`'value' must be a number, got: ${typeof row.value}`);
    return false;
  }

  return true;
}

/**
 * Summarizes the loaded data for debugging
 */
export function summarizeData(data: Record<string, unknown>[]): void {
  const kpis = new Set<string>();
  const regions = new Set<string>();
  const products = new Set<string>();
  const dates = new Set<string>();

  for (const row of data) {
    kpis.add(row.kpi as string);
    regions.add(row.region as string);
    products.add(row.product as string);
    dates.add(row.date as string);
  }

  console.log("=== Data Summary ===");
  console.log(`Total rows: ${data.length}`);
  console.log(`KPIs: ${Array.from(kpis).join(", ")}`);
  console.log(`Regions: ${Array.from(regions).join(", ")}`);
  console.log(`Products: ${Array.from(products).join(", ")}`);
  console.log(`Date range: ${Math.min(...Array.from(dates).map(d => new Date(d).getTime()))} to ${Math.max(...Array.from(dates).map(d => new Date(d).getTime()))}`);
  console.log("====================");
}
