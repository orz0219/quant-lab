<template>
  <div class="table-wrap">
    <table class="trades-table">
      <thead><tr><th>开仓日</th><th>平仓日</th><th>方向</th><th>开仓价</th><th>平仓价</th><th>盈亏</th><th>盈亏 %</th><th>持仓天数</th></tr></thead>
      <tbody>
        <tr v-if="!trades.length"><td colspan="8" class="muted" style="text-align:center;padding:24px;">暂无交易记录</td></tr>
        <tr v-for="(t, i) in trades" :key="i">
          <td>{{ t.open_date || '---' }}</td>
          <td>{{ t.close_date || '---' }}</td>
          <td :class="(t.side || 'long') === 'short' ? 'tag-short' : 'tag-long'">{{ (t.side || 'long') === 'short' ? '做空' : '做多' }}</td>
          <td>{{ fmtNum(t.open_price) }}</td>
          <td>{{ fmtNum(t.close_price) }}</td>
          <td :style="{ color: (t.pnl || 0) >= 0 ? '#EC4899' : '#22D3EE' }">{{ t.pnl != null ? fmtNum(t.pnl) : '---' }}</td>
          <td :style="{ color: (t.pnl_pct || 0) >= 0 ? '#EC4899' : '#22D3EE' }">{{ fmtPct(t.pnl_pct) }}</td>
          <td>{{ t.hold_days != null ? t.hold_days + ' 天' : '---' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { fmtNum, fmtPct } from '@/utils/format.js'
defineProps({ trades: { type: Array, default: () => [] } })
</script>
