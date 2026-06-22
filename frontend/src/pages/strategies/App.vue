<template>
  <div>
    <div class="bg-aurora"></div>
    <div class="bg-grid"></div>
    <Nav active="strategies" />
    <main class="workspace-single">
      <section class="headline center">
        <h1 class="head-title">策略库：<span class="grad-text">写策略</span></h1>
        <p class="head-sub">用自然语言描述 + 编辑你的思路，把策略保存到策略库。</p>
      </section>
      <section class="strategy-editor glass">
        <div class="card-head"><div class="card-title"><span class="title-dot"></span>策略编辑器</div><div class="muted small">当前仅前端演示 UI，暂未接入后端保存接口</div></div>
        <div class="editor-grid">
          <div class="editor-left">
            <div class="field"><label>策略名称</label><input type="text" v-model="form.name" placeholder="给策略起个名字" /></div>
            <div class="field"><label>标签</label><input type="text" v-model="form.tags" placeholder="用逗号分隔" /></div>
            <div class="field"><label>用自然语言描述你的思路</label><textarea v-model="form.desc" rows="5" placeholder="例如：当 5 日均线从下方穿过 20 日均线买入..."></textarea></div>
            <div style="display:flex;gap:8px;">
              <button class="btn-gradient" style="flex:2" @click="saveStrategy">保存到策略库</button>
              <button class="btn-ghost" style="flex:1" @click="clearForm">清空</button>
            </div>
          </div>
          <div class="editor-right">
            <div class="field">
              <label>自定义参数</label>
              <div class="params-list">
                <div v-for="(param, idx) in customParams" :key="idx" class="param-row">
                  <span class="param-grip">⠿</span>
                  <input class="param-label" type="text" placeholder="参数名" v-model="param.key" />
                  <input class="param-default" type="number" step="any" placeholder="默认值" v-model.number="param.defaultValue" />
                  <button class="param-del" @click="removeParam(idx)">×</button>
                </div>
              </div>
              <button class="btn-ghost small" @click="addParam" style="padding:6px 14px;font-size:13px;margin-top:6px;">+ 添加参数</button>
            </div>
            <div class="field">
              <div class="field-header">
                <label>策略代码</label>
                <button class="btn-ghost small code-copy-btn" @click="copyCode">复制全部</button>
              </div>
              <div class="code-editor-wrap">
                <pre class="code-highlight" aria-hidden="true"><code v-html="highlightedCode"></code></pre>
                <textarea v-model="form.code" rows="10" class="code-edit" spellcheck="false" @scroll="syncScroll"></textarea>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section class="strategy-table-section glass">
        <div class="card-head"><div class="card-title"><span class="title-dot cyan"></span>我的策略库</div><div class="muted small">共 {{ strategyList.length }} 条</div></div>
        <DataTable :columns="columns" :rows="strategyList">
          <template #cell-name="{ row }">
            <div class="strategy-name" :title="row.name">{{ row.name || '—' }}</div>
          </template>
          <template #cell-tags="{ row }">
            <div v-if="row.tags" class="strategy-tags">
              <span v-for="tag in row.tags.split(',').filter(Boolean)" :key="tag" class="strategy-tag">{{ tag.trim() }}</span>
            </div>
            <span v-else class="muted">—</span>
          </template>
          <template #cell-description="{ row }">
            <div class="strategy-desc" :title="row.description || ''">{{ row.description ? row.description.slice(0, 20) + (row.description.length > 20 ? '...' : '') : '—' }}</div>
          </template>
          <template #cell-version="{ row }">
            <span class="version-badge">v{{ row.version }}</span>
          </template>
          <template #cell-actions="{ row }">
            <div class="action-cell">
              <button class="strategy-edit-btn" @click="editStrategy(row)">编辑</button>
              <button class="strategy-edit-btn" @click="openVersions(row)">版本</button>
            </div>
          </template>
        </DataTable>
      </section>
    </main>

    <!-- 版本历史弹窗 -->
    <Teleport to="body">
      <div v-if="versionsModalVisible" class="version-overlay" @click.self="closeVersions">
        <div class="version-box">
          <div class="version-head">
            <span class="version-title">版本历史：{{ currentVersionName }}</span>
            <button class="version-close" @click="closeVersions">×</button>
          </div>
          <div class="version-body">
            <div v-if="!versionList.length" class="version-empty">暂无历史版本</div>
            <div v-for="v in versionList" :key="v.version" class="version-item">
              <div class="version-meta">
                <span class="version-number">v{{ v.version }}</span>
                <span class="version-time">{{ v.saved_at ? v.saved_at.replace('T', ' ').slice(0, 19) : '—' }}</span>
              </div>
              <div v-if="v.description" class="version-desc">{{ v.description }}</div>
              <pre v-if="v.code" class="version-code">{{ v.code.slice(0, 200) }}{{ v.code.length > 200 ? '...' : '' }}</pre>
            </div>
          </div>
          <div class="version-footer">
            <button class="btn-primary" @click="closeVersions">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 复制成功提示 -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="toastVisible" class="toast-notification">{{ toastMessage }}</div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Nav from '@/components/Nav.vue'
import DataTable from '@/components/DataTable.vue'
import { strategyApi } from '@/utils/request.js'

const form = reactive({ name: '', tags: '', desc: '', code: '' })
const highlightedCode = computed(() => highlightJS(form.code))
const customParams = ref([])
const strategyList = ref([])
const editingId = ref(null)

const columns = [
  { key: 'name', label: '策略名称', width: '22%' },
  { key: 'tags', label: '标签', width: '16%' },
  { key: 'description', label: '策略思路' },
  { key: 'version', label: '版本', width: '70px' },
  { key: 'actions', label: '操作', width: '150px' },
]

// 版本弹窗状态
const versionsModalVisible = ref(false)
const versionList = ref([])
const currentVersionName = ref('')

const toastVisible = ref(false)
const toastMessage = ref('')
let toastTimer = null
function showToast(msg) {
  toastMessage.value = msg
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2000)
}

function addParam() { customParams.value.push({ key: '', defaultValue: 0 }) }
function removeParam(idx) { customParams.value.splice(idx, 1) }
function clearForm() { form.name = ''; form.tags = ''; form.desc = ''; form.code = ''; customParams.value = []; editingId.value = null }

async function loadList() {
  try { const res = await strategyApi.list(); strategyList.value = res.items || [] } catch { strategyList.value = [] }
}

async function saveStrategy() {
  const data = { name: form.name, description: form.desc, tags: form.tags, code: form.code, params_schema: {} }
  if (customParams.value.length) {
    const props = {}
    customParams.value.forEach(p => { if (p.key) props[p.key] = { type: 'number', default: p.defaultValue ?? 0, label: p.key } })
    data.params_schema = { type: 'object', properties: props }
  }
  try {
    if (editingId.value) await strategyApi.update(editingId.value, data)
    else await strategyApi.create(data)
    clearForm(); await loadList()
  } catch (e) { alert('保存失败: ' + e.message) }
}

async function editStrategy(s) {
  try {
    const item = await strategyApi.get(s.id)
    editingId.value = item.id; form.name = item.name || ''; form.tags = item.tags || ''; form.desc = item.description || ''; form.code = item.code || ''
    customParams.value = []
    const ps = item.params_schema?.properties || {}
    Object.keys(ps).forEach(k => customParams.value.push({ key: k, defaultValue: ps[k].default ?? 0 }))
  } catch (e) { alert('获取策略失败: ' + e.message) }
}

async function deleteStrategy(id) { if (!confirm('确定删除？')) return; try { await strategyApi.delete(id); await loadList() } catch (e) { alert('删除失败: ' + e.message) } }

async function openVersions(s) {
  currentVersionName.value = s.name
  try {
    const res = await strategyApi.getVersions(s.id)
    versionList.value = res.items || []
  } catch { versionList.value = [] }
  versionsModalVisible.value = true
}

function closeVersions() {
  versionsModalVisible.value = false
}

function copyCode() {
  const text = form.code
  if (!text) return showToast('代码为空')
  navigator.clipboard.writeText(text).then(() => {
    showToast('已复制到剪贴板')
  }).catch(() => {
    // fallback: select textarea and exec copy
    const ta = document.querySelector('.code-edit')
    if (ta) { ta.select(); document.execCommand('copy'); showToast('已复制到剪贴板') }
  })
}

function syncScroll(e) {
  const pre = e.target.parentElement.querySelector('.code-highlight')
  if (pre) { pre.scrollTop = e.target.scrollTop; pre.scrollLeft = e.target.scrollLeft }
}

function highlightJS(code) {
  if (!code) return ''
  return code
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(
      /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|`(?:[^`\\]|\\.)*`|'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|\b(await|break|case|catch|class|const|continue|debugger|default|delete|do|else|export|extends|finally|for|function|if|import|in|instanceof|let|new|of|return|static|super|switch|this|throw|try|typeof|var|void|while|with|yield)\b|\b(Array|Boolean|Date|Error|Function|JSON|Map|Math|Number|Object|Promise|RegExp|Set|String|Symbol|TypeError|console)\b|\b(\d+\.?\d*)\b/g,
      (m, strOrComment, keyword, builtin, number) => {
        if (strOrComment) {
          if (strOrComment.startsWith('//') || strOrComment.startsWith('/*')) return `<span class="hl-comment">${m}</span>`
          return `<span class="hl-string">${m}</span>`
        }
        if (keyword) return `<span class="hl-keyword">${m}</span>`
        if (builtin) return `<span class="hl-builtin">${m}</span>`
        if (number) return `<span class="hl-number">${m}</span>`
        return m
      }
    )
}

onMounted(loadList)
</script>

<style scoped>
.action-cell { display: flex; gap: 4px; flex-wrap: nowrap; }
.strategy-desc { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.code-copy-btn {
  font-size: 12px;
  padding: 2px 10px;
  cursor: pointer;
}

/* ── 代码编辑器 overlay ── */
.code-editor-wrap {
  position: relative;
  min-height: 200px;
}
.code-editor-wrap .code-highlight,
.code-editor-wrap .code-edit {
  font-family: "SF Mono", Consolas, Menlo, monospace;
  font-size: 13px;
  line-height: 1.5;
  padding: 10px 12px;
  margin: 0;
  width: 100%;
  min-height: 200px;
  border-radius: 10px;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
  tab-size: 2;
  box-sizing: border-box;
}
.code-editor-wrap .code-highlight {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: auto;
  border: 1px solid transparent;
  background: rgba(10, 18, 40, 0.85);
  color: #E2E8F0;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.10) transparent;
}
.code-editor-wrap .code-highlight::-webkit-scrollbar { width: 4px; }
.code-editor-wrap .code-highlight::-webkit-scrollbar-track { background: transparent; }
.code-editor-wrap .code-highlight::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 10px; }
.code-editor-wrap .code-highlight::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.20); }
.code-editor-wrap .code-edit {
  position: relative;
  z-index: 1;
  background: transparent !important;
  color: transparent;
  caret-color: #E2E8F0;
  resize: vertical;
  border: 1px solid var(--border);
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.10) transparent;
}
.code-editor-wrap .code-edit::-webkit-scrollbar { width: 4px; }
.code-editor-wrap .code-edit::-webkit-scrollbar-track { background: transparent; }
.code-editor-wrap .code-edit::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 10px; }
.code-editor-wrap .code-edit::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.20); }

/* 语法高亮颜色（:deep 穿透 scoped 到 v-html 内容） */
:deep(.hl-keyword) { color: #FF79C6; }
:deep(.hl-string)  { color: #F1FA8C; }
:deep(.hl-number)  { color: #BD93F9; }
:deep(.hl-comment) { color: #6272A4; font-style: italic; }
:deep(.hl-builtin) { color: #8BE9FD; }

.version-badge {
  display: inline-block; font-size: 12px; padding: 2px 8px;
  border-radius: 999px; background: rgba(168,85,247,0.12); color: #C084FC;
  font-family: "SF Mono", Consolas, monospace;
}

/* 版本弹窗 */
.version-overlay {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
}
.version-box {
  background: #0A1330; border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px; width: 90%; max-width: 620px;
  display: flex; flex-direction: column; max-height: 80vh;
}
.version-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px 0;
}
.version-title { font-weight: 600; font-size: 16px; color: #E2E8F0; }
.version-close {
  background: none; border: none; color: var(--muted); font-size: 22px;
  cursor: pointer; padding: 0 4px; line-height: 1;
}
.version-close:hover { color: var(--text); }
.version-body {
  flex: 1; overflow-y: auto; padding: 16px 24px;
}
.version-empty {
  text-align: center; padding: 32px 0; color: var(--muted); font-size: 14px;
}
.version-item {
  padding: 14px; margin-bottom: 10px; border-radius: 10px;
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
}
.version-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.version-number {
  font-weight: 600; font-size: 14px; color: var(--cyan);
  font-family: "SF Mono", Consolas, monospace;
}
.version-time { font-size: 12px; color: var(--muted); }
.version-desc { font-size: 13px; color: var(--muted); margin-bottom: 6px; }
.version-code {
  font-family: "SF Mono", Consolas, Menlo, monospace; font-size: 12px;
  color: #B9E6FF; background: #050A18; border-radius: 6px;
  padding: 10px; margin: 0; white-space: pre-wrap; line-height: 1.5;
  max-height: 100px; overflow: hidden;
}
.version-footer {
  padding: 0 24px 20px; display: flex; justify-content: center;
}

/* Toast 通知 */
.toast-notification {
  position: fixed;
  top: 76px;
  right: 20px;
  background: rgba(6, 16, 31, 0.92);
  border: 1px solid rgba(34, 211, 238, 0.35);
  backdrop-filter: blur(12px);
  padding: 10px 20px;
  border-radius: 10px;
  color: #E2E8F0;
  font-size: 14px;
  z-index: 999999;
  pointer-events: none;
}
.toast-fade-enter-active {
  transition: all .25s ease-out;
}
.toast-fade-leave-active {
  transition: all .2s ease-in;
}
.toast-fade-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>