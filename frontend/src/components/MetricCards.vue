<template>
  <div class="metrics">
    <div class="metric glass"><div class="metric-label">总收益率</div><div class="metric-value">{{ metric.total_return != null ? fmtPctOnly(metric.total_return) : '—' }}</div></div>
    <div class="metric glass"><div class="metric-label">年化收益</div><div :class="['metric-value', (metric.annual_return || 0) >= 0 ? 'ok' : 'warn']">{{ metric.annual_return != null ? fmtPctOnly(metric.annual_return) : '—' }}</div></div>
    <div class="metric glass"><div class="metric-label">最大回撤</div><div class="metric-value warn">{{ metric.max_drawdown != null ? fmtPctOnly(metric.max_drawdown) : '—' }}</div></div>
    <div class="metric glass"><div class="metric-label">夏普比率</div><div class="metric-value">{{ metric.sharpe_ratio != null ? Number(metric.sharpe_ratio).toFixed(2) : '—' }}</div></div>
    <div class="metric glass"><div class="metric-label">胜率</div><div class="metric-value">{{ metric.win_rate != null ? Number(metric.win_rate).toFixed(2) + '%' : '—' }}</div></div>
    <div class="metric glass"><div class="metric-label">交易笔数</div><div class="metric-value">{{ metric.trade_count != null ? String(metric.trade_count) : '—' }}</div></div>
  </div>
</template>

<script setup>
import { fmtPctOnly } from '@/utils/format.js'
defineProps({ metric: { type: Object, default: () => ({}) } })
</script>
