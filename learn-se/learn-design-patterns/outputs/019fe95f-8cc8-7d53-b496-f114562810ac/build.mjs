import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = ".";
const workbook = Workbook.create();

// ---------- 主表：空白模板 ----------
const sheet = workbook.worksheets.add("开发人员统计表");
sheet.showGridLines = false;

const headers = [
  "序号",
  "开发者",
  "角色",
  "负责模块/任务",
  "工作量（人天）",
  "贡献度评分（0-100分）",
  "贡献占比（%）",
  "开发开销（元）",
  "评价",
  "建议工资（元/月）",
  "开资理由",
  "备注",
];

const lastRow = 21; // 1 行表头 + 20 行空白
sheet.getRange("A1:L1").values = [headers];

// 表格对象：自带表头与筛选
const table = sheet.tables.add("A1:L21", true, "开发人员表");
table.showHeaders = true;

// 表头样式
sheet.getRange("A1:L1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF", size: 11 },
  horizontalAlignment: "Center",
  verticalAlignment: "Center",
};
sheet.getRange("A1:L1").format.rowHeight = 30;

// 数据区格式
sheet.getRange("A2:L21").format = {
  verticalAlignment: "Center",
  horizontalAlignment: "Left",
};
sheet.getRange("A2:A21").format = { horizontalAlignment: "Center", numberFormat: "0" };
sheet.getRange("B2:C21").format = { horizontalAlignment: "Center" };
sheet.getRange("E2:E21").format = { horizontalAlignment: "Center", numberFormat: "0.0" };
sheet.getRange("F2:F21").format = { horizontalAlignment: "Center", numberFormat: "0" };
sheet.getRange("G2:G21").format = { horizontalAlignment: "Center", numberFormat: "0.0%" };
sheet.getRange("H2:H21").format = { horizontalAlignment: "Right", numberFormat: "\"¥\"#,##0" };
sheet.getRange("J2:J21").format = { horizontalAlignment: "Right", numberFormat: "\"¥\"#,##0" };
sheet.getRange("I2:I21").format = { wrapText: true };
sheet.getRange("K2:K21").format = { wrapText: true };
sheet.getRange("L2:L21").format = { wrapText: true };

// 列宽
const widths = {
  A: 6, B: 14, C: 14, D: 26, E: 12, F: 16, G: 12, H: 14, I: 30, J: 15, K: 40, L: 16,
};
for (const [col, w] of Object.entries(widths)) {
  sheet.getRange(`${col}1:${col}21`).format.columnWidth = w;
}

// 冻结表头 + 贡献度评分校验
sheet.freezePanes.freezeRows(1);
sheet.dataValidations.add({
  range: "F2:F21",
  rule: { type: "whole", operator: "between", formula1: 0, formula2: 100 },
});

// ---------- 填写说明 ----------
const guide = workbook.worksheets.add("填写说明");
guide.showGridLines = false;
guide.getRange("A1:B1").values = [["列名", "填写说明"]];
guide.getRange("A1:B1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "Center",
  verticalAlignment: "Center",
};

const guideRows = [
  ["序号", "按 1、2、3… 依次编号，可留空由自己编号。"],
  ["开发者", "填写开发人员姓名或 ID。"],
  ["角色", "例如：开发、测试、架构、文档、项目管理。"],
  ["负责模块/任务", "填写该开发者负责的功能模块或具体任务。"],
  ["工作量（人天）", "按人天填写，如 5 表示 5 个工作日。"],
  ["贡献度评分（0-100分）", "对该开发者贡献的主观量化评分，0–100 分。"],
  ["贡献占比（%）", "该开发者工作量占项目总工作量的比例，可直接填百分比。"],
  ["开发开销（元）", "项目为该开发者支付的实际成本，单位元。"],
  ["评价", "一句话总结，如代码质量、主动性、协作、交付情况等。"],
  ["建议工资（元/月）", "建议的月薪，单位元/月。"],
  ["开资理由", "建议工资的依据，如能力水平、市场行情、项目贡献、任职表现等。"],
  ["备注", "其他需要补充说明的信息。"],
];
guide.getRange("A2:B13").values = guideRows;
guide.getRange("A2:B13").format = { verticalAlignment: "Center", wrapText: true };
guide.getRange("A2:A13").format = { horizontalAlignment: "Center", font: { bold: true } };
guide.getRange("A1:B1").format.rowHeight = 26;
guide.getRange("A2:B13").format.rowHeight = 30;
guide.getRange("A:A").format.columnWidth = 24;
guide.getRange("B:B").format.columnWidth = 70;
guide.getRange("A1:B13").format.borders = { preset: "all", style: "thin", color: "#D9D9D9" };
guide.freezePanes.freezeRows(1);

// ---------- 导出 ----------
await fs.mkdir(outputDir, { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(`${outputDir}/开发人员贡献统计表.xlsx`);
console.log("done");
