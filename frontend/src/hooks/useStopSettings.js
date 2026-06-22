import { ref } from 'vue'

const STOP_CACHE_KEY = 'ql_stop_settings'

const defaultSettings = {
  chkFixedSL: true, stopLoss: 5,
  chkBreakevenSL: false, breakevenStop: 2,
  chkMaSL: false, maStopPeriod: 20,
  chkFixedTP: true, stopProfit: 15,
  chkTrailingTP: false, trailingProfit: 6,
  chkMaTP: false, maProfitPeriod: 20,
}

export function useStopSettings() {
  const settings = ref({ ...defaultSettings })

  function load() {
    try {
      const raw = localStorage.getItem(STOP_CACHE_KEY)
      if (raw) {
        const data = JSON.parse(raw)
        if (data && typeof data === 'object') {
          settings.value = { ...defaultSettings, ...data }
        }
      }
    } catch {}
  }

  function save() {
    try { localStorage.setItem(STOP_CACHE_KEY, JSON.stringify(settings.value)) } catch {}
  }

  function reset() {
    settings.value = { ...defaultSettings }
    save()
  }

  function collect() {
    const s = settings.value
    return {
      fixedSL: s.chkFixedSL ? Number(s.stopLoss) : 0,
      breakevenSL: s.chkBreakevenSL ? Number(s.breakevenStop) : 0,
      maSL: s.chkMaSL ? Number(s.maStopPeriod) : 0,
      fixedTP: s.chkFixedTP ? Number(s.stopProfit) : 0,
      trailingTP: s.chkTrailingTP ? Number(s.trailingProfit) : 0,
      maTP: s.chkMaTP ? Number(s.maProfitPeriod) : 0,
    }
  }

  load()
  return { settings, load, save, reset, collect }
}
