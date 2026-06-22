const API_BASE = ''

export async function fetchStocks(keyword) {
  try {
    const url = `${API_BASE}/api/v1/stocks` + (keyword?.trim() ? `?search=${encodeURIComponent(keyword.trim())}` : '')
    const resp = await fetch(url)
    if (!resp.ok) return null
    return await resp.json()
  } catch { return null }
}

export async function fetchKline(tsCode, start, end, cycle) {
  if (!tsCode) return null
  try {
    const { toDateInt } = await import('./date.js')
    const s = start ? toDateInt(start) : ''
    const e = end ? toDateInt(end) : ''
    const tbl = cycle === 'weekly' ? 'weekly' : 'daily'
    const params = new URLSearchParams()
    if (s) params.set('start_date', s)
    if (e) params.set('end_date', e)
    params.set('table', tbl)
    const url = `${API_BASE}/api/v1/stocks/${encodeURIComponent(tsCode)}/kline?${params}`
    const resp = await fetch(url)
    if (!resp.ok) return null
    return await resp.json()
  } catch { return null }
}

export async function generateStrategy(description) {
  if (!description) return null
  try {
    const resp = await fetch(`${API_BASE}/api/v1/strategy/generate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    })
    if (!resp.ok) return { ok: false, message: '生成失败' }
    const json = await resp.json()
    return { ok: true, data: json }
  } catch (err) {
    return { ok: false, message: String(err) }
  }
}

export async function loadIndicatorSettings(userId) {
  const uid = userId || 'default'
  try {
    const r = await fetch(`${API_BASE}/api/v1/settings/indicators?user_id=${encodeURIComponent(uid)}`)
    if (!r.ok) return null
    return await r.json()
  } catch { return null }
}

export async function saveIndicatorSettings(settings, userId) {
  const uid = userId || 'default'
  try {
    const r = await fetch(`${API_BASE}/api/v1/settings/indicators`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: uid, settings }),
    })
    return r.ok
  } catch { return false }
}

function api(method, path, body) {
  return fetch(`${API_BASE}/api/v1/strategies${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  }).then(r => {
    if (!r.ok) return r.json().then(e => { throw new Error(e.detail || '请求失败') })
    return r.json()
  })
}

export async function fetchSectorRS(days = 252, refresh = false) {
  try {
    const params = new URLSearchParams({ days: String(days), refresh: String(refresh) })
    const r = await fetch(`${API_BASE}/api/v1/sectors/rs?${params}`)
    if (!r.ok) return null
    return await r.json()
  } catch { return null }
}

export const strategyApi = {
  list: () => api('GET', '?limit=200'),
  get: (id) => api('GET', `/${id}`),
  create: (data) => api('POST', '', data),
  update: (id, data) => api('PUT', `/${id}`, data),
  delete: (id) => api('DELETE', `/${id}`),
  getVersions: (id) => api('GET', `/${id}/versions`),
}
