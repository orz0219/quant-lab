const CACHE_KEY = 'quantlab_strategy_cache'

export function useStrategyCache() {
  function load() {
    try {
      const raw = localStorage.getItem(CACHE_KEY)
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  }
  function save(strategyKey, params) {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify({ strategyKey, params: params || {} })) } catch {}
  }
  return { load, save }
}
