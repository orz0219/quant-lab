<template>
  <div class="screener-empty">
    <div class="screener-empty-icon">{{ icon }}</div>
    <div class="screener-empty-title">{{ title }}</div>
    <div v-if="desc" class="screener-empty-desc muted small" v-html="desc"></div>
  </div>
</template>

<script setup>
defineProps({ icon: { type: String, default: '📊' }, title: { type: String, default: '暂无数据' }, desc: { type: String, default: '' } })
</script>
