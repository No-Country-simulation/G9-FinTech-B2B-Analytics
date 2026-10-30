function cell(value: string | number) {
  const text = String(value)
  return /[",;\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

// Builds a CSV and hands it to the browser as a download. The BOM makes
// Excel read accents correctly.
export function downloadCsv(
  filename: string,
  headers: string[],
  rows: (string | number)[][]
) {
  const csv = [headers, ...rows].map((row) => row.map(cell).join(",")).join("\n")
  const blob = new Blob(["﻿", csv], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
