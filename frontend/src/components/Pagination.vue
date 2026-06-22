<template>
  <div v-if="totalPages > 1" class="pagination">
    <button class="page-btn" :class="{ disabled: current <= 1 }" :disabled="current <= 1" @click="$emit('change', current - 1)">‹</button>
    <template v-if="startPage > 1">
      <button class="page-btn" @click="$emit('change', 1)">1</button>
      <span v-if="startPage > 2" class="page-ellipsis">…</span>
    </template>
    <button v-for="p in pageRange" :key="p" :class="['page-btn', { active: p === current }]" @click="$emit('change', p)">{{ p }}</button>
    <template v-if="endPage < totalPages">
      <span v-if="endPage < totalPages - 1" class="page-ellipsis">…</span>
      <button class="page-btn" @click="$emit('change', totalPages)">{{ totalPages }}</button>
    </template>
    <button class="page-btn" :class="{ disabled: current >= totalPages }" :disabled="current >= totalPages" @click="$emit('change', current + 1)">›</button>
    <span class="page-info">共 {{ total }} 条</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ current: { type: Number, default: 1 }, total: { type: Number, default: 0 }, pageSize: { type: Number, default: 10 } })
defineEmits(['change'])
const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const startPage = computed(() => Math.max(1, props.current - 2))
const endPage = computed(() => Math.min(totalPages.value, props.current + 2))
const pageRange = computed(() => { const arr = []; for (let i = startPage.value; i <= endPage.value; i++) arr.push(i); return arr })
</script>
