/**
 * CSV to JSON Converter for KPI Mart Data
 *
 * Usage:
 *   npx ts-node scripts/convertCsvToJson.ts input.csv output.json
 *
 * Expected CSV format:
 *   date,region,product,segment,kpi,value
 *   2024-01-01,EMEA,Product A,Enterprise,revenue,125000
 *   ...
 *
 * The script will:
 * 1. Read the CSV file
 * 2. Parse each row into a KpiDataRow object
 * 3. Output valid JSON to the specified output file
 */

import * as fs from "fs";
import * as path from "path";

interface KpiDataRow {
  date: string;
  region: string;
  product: string;
  segment?: string;
  kpi: string;
  value: number;
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (const char of line) {
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  result.push(current.trim());

  return result;
}

function convertCsvToJson(inputPath: string, outputPath: string): void {
  console.log(`Reading CSV from: ${inputPath}`);

  const content = fs.readFileSync(inputPath, "utf-8");
  const lines = content.split("\n").filter((line) => line.trim());

  if (lines.length < 2) {
    throw new Error("CSV file must have a header row and at least one data row");
  }

  // Parse header
  const headers = parseCSVLine(lines[0]).map((h) => h.toLowerCase());
  console.log(`Found headers: ${headers.join(", ")}`);

  // Validate required headers
  const requiredHeaders = ["date", "region", "product", "kpi", "value"];
  for (const required of requiredHeaders) {
    if (!headers.includes(required)) {
      throw new Error(`Missing required column: ${required}`);
    }
  }

  // Parse data rows
  const data: KpiDataRow[] = [];
  let errorCount = 0;

  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);

    if (values.length !== headers.length) {
      console.warn(`Skipping row ${i + 1}: column count mismatch`);
      errorCount++;
      continue;
    }

    const row: Record<string, string | number> = {};
    headers.forEach((header, index) => {
      row[header] = values[index];
    });

    // Convert value to number
    const numValue = parseFloat(row.value as string);
    if (isNaN(numValue)) {
      console.warn(`Skipping row ${i + 1}: invalid value "${row.value}"`);
      errorCount++;
      continue;
    }

    const kpiRow: KpiDataRow = {
      date: row.date as string,
      region: row.region as string,
      product: row.product as string,
      kpi: row.kpi as string,
      value: numValue,
    };

    // Add optional segment if present
    if (row.segment && (row.segment as string).trim()) {
      kpiRow.segment = row.segment as string;
    }

    data.push(kpiRow);
  }

  // Write output
  fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));

  console.log(`\nConversion complete!`);
  console.log(`  Rows processed: ${lines.length - 1}`);
  console.log(`  Rows converted: ${data.length}`);
  console.log(`  Errors: ${errorCount}`);
  console.log(`  Output: ${outputPath}`);
}

// Main execution
const args = process.argv.slice(2);

if (args.length < 2) {
  console.log("Usage: npx ts-node scripts/convertCsvToJson.ts <input.csv> <output.json>");
  console.log("\nExample:");
  console.log("  npx ts-node scripts/convertCsvToJson.ts mydata.csv backend/src/data/kpiMart.json");
  process.exit(1);
}

const inputFile = path.resolve(args[0]);
const outputFile = path.resolve(args[1]);

if (!fs.existsSync(inputFile)) {
  console.error(`Error: Input file not found: ${inputFile}`);
  process.exit(1);
}

try {
  convertCsvToJson(inputFile, outputFile);
} catch (error) {
  console.error(`Error: ${error}`);
  process.exit(1);
}
