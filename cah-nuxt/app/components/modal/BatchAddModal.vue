<script setup lang="ts">
const props = defineProps<{
  open: boolean
  deckId: number
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  added: [result: { blackCount: number; whiteCount: number }]
}>()

const { batchAddCards } = useCards()

const form = reactive({
  blackCards: '',
  whiteCards: ''
})

const loading = ref(false)
const error = ref('')

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

watch(isOpen, (value) => {
  if (value) {
    form.blackCards = ''
    form.whiteCards = ''
    error.value = ''
  }
})

async function handleSubmit() {
  const blackLines = form.blackCards.split('\n').filter(l => l.trim())
  const whiteLines = form.whiteCards.split('\n').filter(l => l.trim())

  if (blackLines.length === 0 && whiteLines.length === 0) {
    error.value = 'Inserisci almeno una carta'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const result = await batchAddCards(props.deckId, blackLines, whiteLines) as { blackCount: number; whiteCount: number }
    emit('added', result)
    isOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Errore durante l\'aggiunta'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen" title="Aggiungi Carte Multiple" :ui="{ footer: 'justify-end' }">
    <template #body>
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <UFormField label="Carte Nere (una per riga)">
          <UTextarea
            v-model="form.blackCards"
            placeholder="Chi ha rubato _____?&#10;Perché _____?&#10;_____ è la causa di _____."
            :rows="5"
          />
          <template #hint>
            Usa _____ per i blank. Il numero di pick viene calcolato automaticamente.
          </template>
        </UFormField>

        <UFormField label="Carte Bianche (una per riga)">
          <UTextarea
            v-model="form.whiteCards"
            placeholder="Una risposta divertente&#10;Un'altra risposta&#10;Qualcosa di inappropriato"
            :rows="5"
          />
        </UFormField>

        <p v-if="error" class="text-sm text-error">{{ error }}</p>
      </form>
    </template>

    <template #footer="{ close }">
      <UButton variant="ghost" @click="close">
        Annulla
      </UButton>
      <UButton :loading="loading" @click="handleSubmit">
        Aggiungi Tutte
      </UButton>
    </template>
  </UModal>
</template>
