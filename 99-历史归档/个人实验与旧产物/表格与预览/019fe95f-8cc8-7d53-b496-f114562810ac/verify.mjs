import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const input = await FileBlob.load("./开发人员贡献统计表.xlsx");
const workbook = await SpreadsheetFile.importXlsx(input);

for (const name of ["开发人员统计表", "填写说明"]) {
  const blob = await workbook.render({ sheetName: name, autoCrop: "all", scale: 1.5, format: "png" });
  await fs.writeFile(`./preview_${name}.png`, new Uint8Array(await blob.arrayBuffer()));
}

const check = await workbook.inspect({
  kind: "table",
  range: "开发人员统计表!A1:L6",
  include: "values",
  tableMaxRows: 8,
  tableMaxCols: 12,
});
console.log(check.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

const style = await workbook.inspect({
  kind: "computedStyle",
  sheetId: "开发人员统计表",
  range: "A1:H2",
  maxChars: 2500,
});
console.log(style.ndjson);
