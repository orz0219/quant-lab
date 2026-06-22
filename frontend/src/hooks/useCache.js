import { ref, watch } from 'vue'

const PREFIX = 'ql_'

/**
 * 通用 localStorage 缓存 hook。
 * 返回一个 ref，值变化时自动持久化到 localStorage。
 */
export function useCache(key, defaultValue) {
  const storageKey = PREFIX + key
  const data = ref(defaultValue)

  try {
    const raw = localStorage.getItem(storageKey)
    if (raw !== null) {
      const parsed = JSON.parse(raw)
      if (parsed !== null && parsed !== undefined) {
        data.value = parsed
      }
    }
  } catch { /* 使用默认值 */ }

  watch(data, (val) => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(val))
    } catch { /* 静默失败 */ }
  })

  return data
}
