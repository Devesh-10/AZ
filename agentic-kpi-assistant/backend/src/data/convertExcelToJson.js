/**
 * Script to convert all Excel files in AZ Agents Input Data to JSON
 * Run with: node src/data/convertExcelToJson.js
 */

const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

const basePath = path.join(__dirname, 'AZ Agents Input Data');
const outputPath = path.join(__dirname, 'json');

// Create output directory
if (!fs.existsSync(outputPath)) {
  fs.mkdirSync(outputPath, { recursive: true });
}

const folders = ['KPI', 'Transaction Data', 'Master Data'];

const allData = {
  kpi: {},
  transactionData: {},
  masterData: {}
};

folders.forEach(folder => {
  const folderPath = path.join(basePath, folder);
  const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.xlsx'));

  const outputKey = folder === 'KPI' ? 'kpi' :
                    folder === 'Transaction Data' ? 'transactionData' : 'masterData';

  files.forEach(file => {
    try {
      const wb = XLSX.readFile(path.join(folderPath, file));
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const data = XLSX.utils.sheet_to_json(sheet);

      // Create a clean key name from filename
      const keyName = file.replace('.xlsx', '').toLowerCase().replace(/ /g, '_');

      allData[outputKey][keyName] = data;

      // Also write individual JSON files
      const subDir = path.join(outputPath, outputKey);
      if (!fs.existsSync(subDir)) {
        fs.mkdirSync(subDir, { recursive: true });
      }

      fs.writeFileSync(
        path.join(subDir, keyName + '.json'),
        JSON.stringify(data, null, 2)
      );

      console.log(`Converted: ${folder}/${file} -> ${data.length} rows`);
    } catch(e) {
      console.error(`Error converting ${file}:`, e.message);
    }
  });
});

// Write combined data file
fs.writeFileSync(
  path.join(outputPath, 'allData.json'),
  JSON.stringify(allData, null, 2)
);

console.log('\n✅ All files converted to JSON in:', outputPath);
console.log('Combined data file: allData.json');
