<template>
  <div class="combobox" :class="{ 'has-value': modelValue }">
    <input type="text" :value="displayValue" @input="onInput" @focus="onFocus" @blur="onBlur" @keydown="onKeydown" placeholder="输入代码或名称" autocomplete="off" />
    <button type="button" class="combobox-clear" @mousedown.prevent @click="onClear">×</button>
    <ul class="combobox-list" :class="{ open: listOpen }" ref="listRef">
      <li v-for="(item, idx) in matches" :key="item.ts_code" :class="{ selected: idx === selectedIdx }" @mousedown.prevent="selectItem(item)">
        <span class="c">{{ item.ts_code }}</span><span class="sep">|</span><span>{{ item.name || '---' }}</span>
      </li>
      <li v-if="!matches.length" class="empty">{{ emptyText }}</li>
    </ul>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { fetchStocks } from '@/utils/request.js'
const props = defineProps({ modelValue: { type: String, default: '' }, stockName: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue', 'select'])
const displayValue = ref(props.modelValue)
const matches = ref([])
const listOpen = ref(false)
const selectedIdx = ref(-1)
const emptyText = ref('')
const listRef = ref(null)
let pendingToken = null
watch(() => props.modelValue, (v) => { displayValue.value = v })
function onInput(e) { displayValue.value = e.target.value; emit('update:modelValue', e.target.value); search(e.target.value) }
async function search(keyword) {
  const kw = (keyword || '').trim()
  const token = Symbol(); pendingToken = token
  if (!kw) { matches.value = []; return }
  const json = await fetchStocks(kw)
  if (pendingToken !== token) return
  matches.value = json?.items || []
  emptyText.value = `未找到匹配股票（关键字：${kw}）`
  selectedIdx.value = -1; listOpen.value = true
}
function onFocus() {
  const val = displayValue.value || ''
  // 兼容 "code | name" 格式，取 code 部分搜索
  const keyword = val.split('|')[0].trim()
  search(keyword)
}
function onBlur() { setTimeout(() => { listOpen.value = false }, 120) }
function onClear() { displayValue.value = ''; emit('update:modelValue', ''); emit('select', { code: '', name: '', industry: '' }); listOpen.value = false }
function selectItem(item) { displayValue.value = item.name ? `${item.ts_code} | ${item.name}` : item.ts_code; listOpen.value = false; emit('select', { code: item.ts_code, name: item.name || '', industry: item.industry || '' }) }
function onKeydown(e) {
  const items = listRef.value?.querySelectorAll('li:not(.empty)') || []
  if (e.key === 'ArrowDown') { if (!listOpen.value && displayValue.value) search(displayValue.value); selectedIdx.value = Math.min(items.length - 1, selectedIdx.value + 1); e.preventDefault() }
  else if (e.key === 'ArrowUp') { selectedIdx.value = Math.max(0, selectedIdx.value - 1); e.preventDefault() }
  else if (e.key === 'Enter') { if (selectedIdx.value >= 0 && selectedIdx.value < matches.value.length) selectItem(matches.value[selectedIdx.value]); listOpen.value = false; e.preventDefault() }
  else if (e.key === 'Escape') { listOpen.value = false }
}
</script>
