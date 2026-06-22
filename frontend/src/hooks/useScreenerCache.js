const CACHE_KEY = 'screener_results_cache'

export function useScreenerCache() {
  function load() {
    try {
      const raw = localStorage.getItem(CACHE_KEY)
      if (!raw) return null
      const data = JSON.parse(raw)
      if (!data.hits || !Array.isArray(data.hits)) return null
      return data
    } catch { return null }
  }
  function save(hits, totalScanned) {
    try {
      const now = new Date()
      const pad2 = (n) => n < 10 ? '0' + n : '' + n
      const dateStr = now.getFullYear() + '年' + pad2(now.getMonth() + 1) + '月' + pad2(now.getDate()) + '日'
      const timeStr = pad2(now.getHours()) + ':' + pad2(now.getMinutes()) + ':' + pad2(now.getSeconds())
      localStorage.setItem(CACHE_KEY, JSON.stringify({ hits, totalScanned, hitCount: hits.length, cachedAt: Date.now(), cachedAtDisplay: dateStr + ' ' + timeStr }))
    } catch {}
  }
  function clear() {
    try { localStorage.removeItem(CACHE_KEY) } catch {}
  }
  return { load, save, clear }
}
