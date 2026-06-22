import { ref } from 'vue'

export function useModal() {
  const visible = ref(false)
  function open() { visible.value = true }
  function close() { visible.value = false }
  function toggle() { visible.value = !visible.value }
  return { visible, open, close, toggle }
}
