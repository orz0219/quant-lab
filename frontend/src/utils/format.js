export function fmtNum(v) {
  if (v === null || v === undefined || Number.isNaN(+v)) return '---'
  return Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function fmtMoney(v) { return fmtNum(v) }

export function fmtPct(v) {
  if (v === null || v === undefined || Number.isNaN(+v)) return '---'
  const n = Number(v)
  return (n > 0 ? '+' : '') + n.toFixed(2) + '%'
}

export function fmtPctOnly(v) {
  if (v === null || v === undefined || Number.isNaN(+v)) return '---'
  const n = Number(v)
  return (n > 0 ? '+' : '') + n.toFixed(2) + '%'
}
