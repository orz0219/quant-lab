<template>
  <div class="screener-item">
    <div class="screener-item-header">
      <div>
        <span class="screener-item-code">{{ stock.ts_code }}</span>
        <span class="screener-item-name"> {{ stock.name }}</span>
      </div>
      <span v-if="stock.industry" class="screener-item-industry">{{ stock.industry }}</span>
    </div>
    <div v-if="stock.signal_date" style="margin-top:6px;font-size:13px;color:var(--muted);">
      信号日: <span style="color:var(--text);">{{ stock.signal_date }}</span>
      <span v-if="stock.signal_price" style="margin-left:12px;">信号价: <span style="color:var(--text);">{{ fmtNum(stock.signal_price) }}</span></span>
    </div>
  </div>
</template>

<script setup>
import { fmtNum } from '@/utils/format.js'
defineProps({ stock: { type: Object, required: true } })
</script>
