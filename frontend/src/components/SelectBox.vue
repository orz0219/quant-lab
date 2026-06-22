<template>
  <div class="sel-wrap" ref="wrapRef">
    <div class="sel-trigger" :class="{ open: open }" @click="toggle">
      <span :class="['sel-label', { muted: !selectedLabel }]">{{ selectedLabel || placeholder }}</span>
      <span class="sel-arrow">▼</span>
    </div>
    <ul v-if="open" class="sel-list" :style="listStyle">
      <li
        v-for="(opt, idx) in options"
        :key="opt.value"
        :class="['sel-option', { active: opt.value === modelValue, highlighted: highlightIdx === idx }]"
        @mousedown.prevent="select(opt)"
        @mouseenter="highlightIdx = idx"
      >{{ opt.label }}</li>
      <li v-if="!options.length" class="sel-empty">暂无选项</li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '请选择' },
})

const emit = defineEmits(['update:modelValue', 'change'])

const open = ref(false)
const highlightIdx = ref(-1)
const wrapRef = ref(null)
const listStyle = ref({})

function toggle() {
  if (open.value) {
    close()
  } else {
    openList()
  }
}

function openList() {
  open.value = true
  highlightIdx.value = props.options.findIndex(o => o.value === props.modelValue)
  // 计算下拉列表位置
  if (wrapRef.value) {
    const rect = wrapRef.value.getBoundingClientRect()
    const spaceBelow = window.innerHeight - rect.bottom - 8
    const spaceAbove = rect.top - 8
    if (spaceBelow < 200 && spaceAbove > spaceBelow) {
      listStyle.value = {
        bottom: 'calc(100% + 6px)',
        top: 'auto',
        maxHeight: Math.min(240, spaceAbove - 10) + 'px',
      }
    } else {
      listStyle.value = {
        top: 'calc(100% + 6px)',
        bottom: 'auto',
        maxHeight: Math.min(240, spaceBelow - 10) + 'px',
      }
    }
  }
}

function close() { open.value = false; highlightIdx.value = -1 }

function select(opt) {
  emit('update:modelValue', opt.value)
  emit('change', opt.value)
  close()
}

function onClickOutside(e) {
  if (wrapRef.value && !wrapRef.value.contains(e.target)) close()
}

const selectedLabel = computed(() => {
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt ? opt.label : ''
})

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
.sel-wrap { position: relative; }
.sel-trigger {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; font-size: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
  user-select: none;
}
.sel-trigger:hover,
.sel-trigger.open { background-color: rgba(34,211,238,0.04); border-color: rgba(34,211,238,0.35); }
.sel-label { color: var(--text); }
.sel-label.muted { color: var(--muted); }
.sel-arrow { font-size: 10px; color: var(--muted); margin-left: 8px; transition: transform .2s; }
.sel-trigger.open .sel-arrow { transform: rotate(180deg); }
.sel-list {
  position: absolute; left: 0; right: 0;
  margin: 0; padding: 6px; list-style: none;
  background: rgba(6,10,24,0.97);
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  overflow-y: auto;
  z-index: 40;
  box-shadow: 0 20px 60px -20px rgba(0,0,0,0.6);
}
.sel-option {
  padding: 8px 10px; border-radius: 8px; font-size: 13px;
  cursor: pointer; color: var(--text);
  transition: background .12s;
}
.sel-option:hover,
.sel-option.highlighted { background: rgba(34,211,238,0.08); }
.sel-option.active { color: var(--cyan); font-weight: 600; background: rgba(34,211,238,0.06); }
.sel-empty { padding: 10px; text-align: center; color: var(--muted); font-size: 13px; }
</style>
