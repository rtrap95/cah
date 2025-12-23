<script setup lang="ts">
import type { Card } from '~/types'

const props = defineProps<{
  open: boolean
  card: Card | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
  deleted: []
}>()

const { updateCard, deleteCard } = useCards()
const { confirm } = useConfirm()

const form = reactive({
  text: '',
  pick: 1
})

const loading = ref(false)
const error = ref('')

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const pickOptions = [
  { label: '1', value: 1 },
  { label: '2', value: 2 },
  { label: '3', value: 3 }
]

watch(() => props.card, (card) => {
  if (card) {
    form.text = card.text
    form.pick = card.pick
  }
}, { immediate: true })

async function handleSave() {
  if (!props.card?.id) return

  if (!form.text.trim()) {
    error.value = 'Il testo della carta è obbligatorio'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await updateCard(props.card.id, form.text.trim(), form.pick)
    emit('saved')
    isOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Errore durante il salvataggio'
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  if (!props.card?.id) return

  const confirmed = await confirm({
    title: 'Elimina carta',
    description: 'Sei sicuro di voler eliminare questa carta? Questa azione non può essere annullata.',
    confirmLabel: 'Elimina',
    confirmColor: 'error',
    icon: 'i-lucide-trash-2'
  })
  if (!confirmed) return

  loading.value = true
  error.value = ''

  try {
    await deleteCard(props.card.id)
    emit('deleted')
    isOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Errore durante l\'eliminazione'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal v-if="card" v-model:open="isOpen" :ui="{ footer: 'justify-between' }">
    <template #title>
      <span>Modifica Carta</span>
      <UBadge
        :color="card.cardType === 'black' ? 'neutral' : 'neutral'"
        :variant="card.cardType === 'black' ? 'solid' : 'outline'"
        size="sm"
        class="ml-2"
      >
        {{ card.cardType === 'black' ? 'NERA' : 'BIANCA' }}
      </UBadge>
    </template>

    <template #body>
      <form class="space-y-4" @submit.prevent="handleSave">
        <UFormField label="Testo carta">
          <UTextarea
            v-model="form.text"
            :rows="4"
          />
        </UFormField>

        <UFormField v-if="card.cardType === 'black'" label="Carte da pescare">
          <USelect
            v-model="form.pick"
            :items="pickOptions"
            value-key="value"
          />
        </UFormField>

        <p v-if="error" class="text-sm text-error">{{ error }}</p>
      </form>
    </template>

    <template #footer="{ close }">
      <UButton
        variant="ghost"
        color="error"
        icon="i-lucide-trash-2"
        :loading="loading"
        @click="handleDelete"
      >
        Elimina
      </UButton>
      <div class="flex gap-2">
        <UButton variant="ghost" @click="close">
          Annulla
        </UButton>
        <UButton :loading="loading" @click="handleSave">
          Salva
        </UButton>
      </div>
    </template>
  </UModal>
</template>
