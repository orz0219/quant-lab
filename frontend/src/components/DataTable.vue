<template>
  <div>
    <div class="table-wrap">
      <table class="trades-table">
        <thead><tr>
          <th v-for="col in columns" :key="col.key" :style="col.width ? `width:${col.width}` : ''">{{ col.label }}</th>
        </tr></thead>
        <tbody>
          <tr v-if="!pageData.length">
            <td :colspan="columns.length" style="text-align:center;color:var(--muted);padding:40px 0;">
              <slot name="empty">{{ emptyText }}</slot>
            </td>
          </tr>
          <tr v-for="(row, idx) in pageData" :key="row._key || row.ts_code || idx">
            <td v-for="col in columns" :key="col.key" :class="col.class || ''">
              <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">{{ row[col.key] ?? '—' }}</slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <Pagination
      v-if="rows.length > pageSize"
      :current="page"
      :total="rows.length"
      :page-size="pageSize"
      @change="page = $event"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Pagination from '@/components/Pagination.vue'

const props = defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  pageSize: { type: Number, default: 10 },
  emptyText: { type: String, default: '暂无数据' },
})

const page = ref(1)
watch(() => props.rows, () => { page.value = 1 }, { deep: false })

const pageData = computed(() => {
  const start = (page.value - 1) * props.pageSize
  return props.rows.slice(start, start + props.pageSize)
})
</script>
