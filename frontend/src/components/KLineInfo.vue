<template>
  <div class="kline-info">
    <div class="ki-body">
      <div class="ki-row"><span class="ki-item" style="font-weight:600;"><span class="ki-val" style="color:var(--text);">{{ data?.trade_date || '—' }}</span></span></div>
      <div class="ki-row">
        <span class="ki-item"><span class="ki-label">开盘</span><span class="ki-val">{{ fmt(data?.open) }}</span></span>
        <span class="ki-item"><span class="ki-label">收盘</span><span class="ki-val">{{ fmt(data?.close) }}</span></span>
        <span class="ki-item"><span class="ki-label">最高</span><span class="ki-val">{{ fmt(data?.high) }}</span></span>
        <span class="ki-item"><span class="ki-label">最低</span><span class="ki-val">{{ fmt(data?.low) }}</span></span>
        <span class="ki-item"><span class="ki-label">涨幅</span><span class="ki-val" :style="{ color: chgColor }">{{ chgText }}</span></span>
      </div>
      <div class="ki-row"><span class="ki-item"><span class="ki-label">成交量</span><span class="ki-val">{{ volText }}</span></span></div>
      <div class="ki-row">
        <span v-for="ma in maValues" :key="ma.label" class="ki-item">
          <span class="ki-label" :style="{ color: ma.color }">{{ ma.label }}</span><span class="ki-val">{{ ma.value }}</span>
        </span>
      </div>
    </div>
    <div v-if="showGear" class="ki-gear-wrap">
      <span class="ki-gear" @click="$emit('openSettings')">⚙ 设置</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { fmtNum } from '@/utils/format.js'
const props = defineProps({ data: { type: Object, default: null }, prevClose: { type: Number, default: null }, maValues: { type: Array, default: () => [] }, showGear: { type: Boolean, default: true } })
defineEmits(['openSettings'])
const fmt = (v) => v != null ? fmtNum(v) : '—'
const chgText = computed(() => {
  if (!props.data || props.prevClose == null || props.prevClose <= 0) return '—'
  const pct = ((Number(props.data.close) - props.prevClose) / props.prevClose) * 100
  return (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%'
})
const chgColor = computed(() => {
  if (!props.data || props.prevClose == null) return ''
  return Number(props.data.close) >= props.prevClose ? '#EC4899' : '#22D3EE'
})
const volText = computed(() => props.data?.vol != null ? fmtNum(Number(props.data.vol)) : '—')
</script>
