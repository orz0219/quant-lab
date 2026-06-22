<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-box">
        <div v-if="title" class="modal-title">{{ title }}</div>
        <div class="modal-body"><slot /></div>
        <div class="modal-footer">
          <button class="btn-primary" @click="$emit('confirm')">确定</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({ visible: { type: Boolean, default: false }, title: { type: String, default: '' } })
defineEmits(['close', 'confirm'])
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; z-index: 99999; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; }
.modal-box { background: #0A1330; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 28px 32px; max-width: 420px; width: 90%; text-align: center; }
.modal-title { font-weight: 600; font-size: 16px; color: #E2E8F0; margin-bottom: 12px; }
.modal-body { color: #94A3B8; font-size: 14px; margin-bottom: 20px; line-height: 1.6; }
.modal-footer { display: flex; justify-content: center; gap: 12px; }
</style>
