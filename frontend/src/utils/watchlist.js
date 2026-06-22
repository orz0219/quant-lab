const WL_CACHE_KEY = 'quantlab_watchlist'

export function getAll() {
  try {
    const raw = localStorage.getItem(WL_CACHE_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch { return [] }
}

function _save(arr) {
  try { localStorage.setItem(WL_CACHE_KEY, JSON.stringify(arr)) } catch {}
}

export function add(stock) {
  if (!stock || !stock.ts_code) return false
  const arr = getAll()
  for (const s of arr) {
    if (s.ts_code === stock.ts_code) return false
  }
  arr.push({ ts_code: stock.ts_code, name: stock.name || '', industry: stock.industry || '', addedAt: Date.now() })
  _save(arr)
  return true
}

export function remove(ts_code) {
  if (!ts_code) return false
  const arr = getAll()
  const idx = arr.findIndex(s => s.ts_code === ts_code)
  if (idx === -1) return false
  arr.splice(idx, 1)
  _save(arr)
  return true
}

export function has(ts_code) {
  if (!ts_code) return false
  return getAll().some(s => s.ts_code === ts_code)
}

export function clearAll() {
  try { localStorage.removeItem(WL_CACHE_KEY) } catch {}
}

export function count() {
  return getAll().length
}
