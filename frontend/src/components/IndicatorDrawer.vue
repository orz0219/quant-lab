<template>
  <Teleport to="body">
    <div :class="['drawer-overlay', { open: visible }]" @click="close"></div>
    <div :class="['drawer', { open: visible, closing }]">
      <div class="drawer-head">
        <span class="drawer-title">指标设置</span>
        <button class="drawer-close" @click="close">✕</button>
      </div>
      <div class="drawer-body">
        <div class="ds-section-label">— K线设置 —</div>
        <div class="ds-row">
          <span class="ds-label">是否显示</span>
          <label class="ds-toggle">
            <input type="checkbox" :checked="showKline" @change="$emit('update:showKline', $event.target.checked)" />
            <span class="ds-toggle-slider"></span>
          </label>
        </div>
        <div class="ds-row">
          <span class="ds-label">上涨颜色</span>
          <input type="color" :value="upColor" @input="$emit('update:upColor', $event.target.value)" class="ds-color" />
        </div>
        <div class="ds-row">
          <span class="ds-label">下跌颜色</span>
          <input type="color" :value="downColor" @input="$emit('update:downColor', $event.target.value)" class="ds-color" />
        </div>
        <div class="ds-divider-dash"></div>
        <div class="ds-section-label">— 成交量设置 —</div>
        <div class="ds-row">
          <span class="ds-label">是否显示</span>
          <label class="ds-toggle">
            <input type="checkbox" :checked="showVolume" @change="$emit('update:showVolume', $event.target.checked)" />
            <span class="ds-toggle-slider"></span>
          </label>
        </div>
        <div class="ds-divider-dash"></div>
        <div class="ds-section-label">— MA 设置 —</div>
        <div class="ds-row">
          <span class="ds-label">是否显示</span>
          <label class="ds-toggle">
            <input type="checkbox" :checked="showMA" @change="$emit('update:showMA', $event.target.checked)" />
            <span class="ds-toggle-slider"></span>
          </label>
        </div>
        <div class="ds-ma-list">
          <div
            v-for="(ma, idx) in maList" :key="idx"
            :class="['ds-ma-item', { 'ds-dragging': dragIdx === idx }]"
            draggable="true"
            @dragstart="onDragStart($event, idx)"
            @dragover="onDragOver($event, idx)"
            @dragend="onDragEnd"
          >
            <span class="ds-ma-grip">⠿</span>
            <input class="ds-ma-period" type="number" min="1" max="250" :value="ma.period" @change="updateMA(idx, 'period', $event.target.value)" />
            <input class="ds-color" type="color" :value="ma.color" @input="updateMA(idx, 'color', $event.target.value)" />
            <button class="ds-ma-del" @click="removeMA(idx)">✕</button>
          </div>
        </div>
        <button class="ds-ma-add" @click="addMA">＋ 添加 MA</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({ visible: Boolean, showKline: { type: Boolean, default: true }, showVolume: { type: Boolean, default: true }, showMA: { type: Boolean, default: true }, upColor: { type: String, default: '#EC4899' }, downColor: { type: String, default: '#22D3EE' }, maList: { type: Array, default: () => [{ period: 5, color: '#A855F7' }, { period: 20, color: '#FBBF24' }] } })
const emit = defineEmits(['close', 'update:showKline', 'update:showVolume', 'update:showMA', 'update:upColor', 'update:downColor', 'update:maList'])
const closing = ref(false)
const dragIdx = ref(-1)

function close() { closing.value = true; setTimeout(() => { closing.value = false; emit('close') }, 250) }

function addMA() { emit('update:maList', [...props.maList, { period: 10, color: '#22C55E' }]) }
function removeMA(idx) { emit('update:maList', props.maList.filter((_, i) => i !== idx)) }
function updateMA(idx, field, value) { emit('update:maList', props.maList.map((m, i) => i === idx ? { ...m, [field]: field === 'period' ? Number(value) : value } : m)) }

// ---------- MA 拖拽排序 ----------

function onDragStart(e, idx) {
  dragIdx.value = idx
  e.dataTransfer.effectAllowed = 'move'
}
function onDragOver(e, idx) {
  e.preventDefault()
  if (dragIdx.value < 0 || dragIdx.value === idx) return
  const list = [...props.maList]
  const [item] = list.splice(dragIdx.value, 1)
  list.splice(idx, 0, item)
  emit('update:maList', list)
  dragIdx.value = idx
}
function onDragEnd() {
  dragIdx.value = -1
}
</script>
