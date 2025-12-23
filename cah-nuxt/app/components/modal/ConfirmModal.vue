<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  confirmColor?: 'primary' | 'error' | 'warning' | 'success' | 'info' | 'neutral'
  icon?: string
}>()

const emit = defineEmits<{
  close: [confirmed: boolean]
}>()
</script>

<template>
  <UModal
    :title="title || 'Conferma'"
    :description="description"
    :ui="{ footer: 'justify-end' }"
  >
    <template v-if="icon" #leading>
      <UIcon :name="icon" class="size-6" />
    </template>

    <template #footer>
      <UButton
        :label="cancelLabel || 'Annulla'"
        color="neutral"
        variant="ghost"
        @click="emit('close', false)"
      />
      <UButton
        :label="confirmLabel || 'Conferma'"
        :color="confirmColor || 'primary'"
        @click="emit('close', true)"
      />
    </template>
  </UModal>
</template>
