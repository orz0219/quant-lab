<template>
  <div class="panel">
    <div class="panel-title"><span class="dot dot-red"></span>止损设置</div>
    <div class="sl-field">
      <label class="sl-row">
        <input type="checkbox" class="sl-chk" :checked="settings.chkFixedSL" @change="update('chkFixedSL', $event.target.checked)" />
        <span class="sl-label">固定止损</span>
        <input class="sl-input" type="number" step="0.5" :value="settings.stopLoss" :disabled="!settings.chkFixedSL" @change="update('stopLoss', $event.target.value)" />
        <span class="sl-unit">%</span>
      </label>
      <label class="sl-row">
        <input type="checkbox" class="sl-chk" :checked="settings.chkBreakevenSL" @change="update('chkBreakevenSL', $event.target.checked)" />
        <span class="sl-label">保本止损</span>
        <input class="sl-input" type="number" step="0.1" :value="settings.breakevenStop" :disabled="!settings.chkBreakevenSL" @change="update('breakevenStop', $event.target.value)" />
        <span class="sl-unit">点</span>
      </label>
      <label class="sl-row">
        <input type="checkbox" class="sl-chk" :checked="settings.chkMaSL" @change="update('chkMaSL', $event.target.checked)" />
        <span class="sl-label">下破均线止损</span>
        <span class="sl-ma">MA</span>
        <input class="sl-input" type="number" :value="settings.maStopPeriod" :disabled="!settings.chkMaSL" @change="update('maStopPeriod', $event.target.value)" />
      </label>
    </div>
  </div>
  <div class="panel">
    <div class="panel-title"><span class="dot dot-green"></span>止盈设置</div>
    <div class="sl-field">
      <label class="sl-row">
        <input type="checkbox" class="sl-chk" :checked="settings.chkFixedTP" @change="update('chkFixedTP', $event.target.checked)" />
        <span class="sl-label">固定止盈</span>
        <input class="sl-input" type="number" step="0.5" :value="settings.stopProfit" :disabled="!settings.chkFixedTP" @change="update('stopProfit', $event.target.value)" />
        <span class="sl-unit">%</span>
      </label>
      <label class="sl-row">
        <input type="checkbox" class="sl-chk" :checked="settings.chkTrailingTP" @change="update('chkTrailingTP', $event.target.checked)" />
        <span class="sl-label">移动止盈</span>
        <input class="sl-input" type="number" step="0.5" :value="settings.trailingProfit" :disabled="!settings.chkTrailingTP" @change="update('trailingProfit', $event.target.value)" />
        <span class="sl-unit">%</span>
      </label>
      <label class="sl-row">
        <input type="checkbox" class="sl-chk" :checked="settings.chkMaTP" @change="update('chkMaTP', $event.target.checked)" />
        <span class="sl-label">下破均线止盈</span>
        <span class="sl-ma">MA</span>
        <input class="sl-input" type="number" :value="settings.maProfitPeriod" :disabled="!settings.chkMaTP" @change="update('maProfitPeriod', $event.target.value)" />
      </label>
    </div>
  </div>
</template>

<script setup>
defineProps({ settings: { type: Object, required: true } })
const emit = defineEmits(['update'])
function update(key, value) { emit('update', key, value) }
</script>
