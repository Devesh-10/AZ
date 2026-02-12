import * as fs from "fs";
import * as path from "path";
import { parse } from "csv-parse/sync";

const DATA_DIR = path.join(__dirname, "../../data");

export interface DataTable {
  name: string;
  category: string;
  data: any[];
  columns: string[];
}

// Cache for loaded data
const dataCache: Map<string, DataTable> = new Map();

function loadCSV(filePath: string): any[] {
  const content = fs.readFileSync(filePath, "utf-8");
  return parse(content, {
    columns: true,
    skip_empty_lines: true,
  });
}

function loadAllData(): void {
  const categories = ["Analytical", "KPI", "Master data", "Transactional"];

  for (const category of categories) {
    const categoryPath = path.join(DATA_DIR, category);
    if (!fs.existsSync(categoryPath)) continue;

    const files = fs.readdirSync(categoryPath).filter((f) => f.endsWith(".csv"));

    for (const file of files) {
      const tableName = file.replace(".csv", "").toUpperCase();
      const filePath = path.join(categoryPath, file);
      const data = loadCSV(filePath);
      const columns = data.length > 0 ? Object.keys(data[0]) : [];

      dataCache.set(tableName, {
        name: tableName,
        category,
        data,
        columns,
      });

      console.log(`Loaded ${tableName}: ${data.length} rows`);
    }
  }
}

// Load data on startup
loadAllData();

export function getAvailableTables(): string[] {
  return Array.from(dataCache.keys());
}

export function getTableInfo(): { name: string; category: string; rowCount: number; columns: string[] }[] {
  return Array.from(dataCache.values()).map((t) => ({
    name: t.name,
    category: t.category,
    rowCount: t.data.length,
    columns: t.columns,
  }));
}

export function getTableData(tableName: string): any[] | null {
  const table = dataCache.get(tableName.toUpperCase());
  return table ? table.data : null;
}

export function getTableColumns(tableName: string): string[] | null {
  const table = dataCache.get(tableName.toUpperCase());
  return table ? table.columns : null;
}

export function queryTable(
  tableName: string,
  filters?: Record<string, any>,
  limit?: number
): any[] | null {
  const data = getTableData(tableName);
  if (!data) return null;

  let result = [...data];

  // Apply filters
  if (filters) {
    result = result.filter((row) => {
      return Object.entries(filters).every(([key, value]) => {
        const rowValue = row[key];
        if (typeof value === "string" && value.includes("*")) {
          const regex = new RegExp(value.replace(/\*/g, ".*"), "i");
          return regex.test(rowValue);
        }
        return String(rowValue).toLowerCase() === String(value).toLowerCase();
      });
    });
  }

  // Apply limit
  if (limit && limit > 0) {
    result = result.slice(0, limit);
  }

  return result;
}

export function aggregateTable(
  tableName: string,
  groupBy: string,
  aggregations: { field: string; operation: "sum" | "avg" | "count" | "min" | "max" }[]
): any[] | null {
  const data = getTableData(tableName);
  if (!data) return null;

  // Group data
  const groups: Map<string, any[]> = new Map();
  for (const row of data) {
    const key = row[groupBy];
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(row);
  }

  // Aggregate
  const result: any[] = [];
  for (const [key, rows] of groups) {
    const aggregated: any = { [groupBy]: key };

    for (const { field, operation } of aggregations) {
      const values = rows.map((r) => parseFloat(r[field])).filter((v) => !isNaN(v));

      switch (operation) {
        case "sum":
          aggregated[`${field}_sum`] = values.reduce((a, b) => a + b, 0);
          break;
        case "avg":
          aggregated[`${field}_avg`] = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
          break;
        case "count":
          aggregated[`${field}_count`] = values.length;
          break;
        case "min":
          aggregated[`${field}_min`] = Math.min(...values);
          break;
        case "max":
          aggregated[`${field}_max`] = Math.max(...values);
          break;
      }
    }

    result.push(aggregated);
  }

  return result;
}
