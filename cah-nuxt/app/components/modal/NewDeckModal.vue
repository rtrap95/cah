<script setup lang="ts">
const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  created: [deckId: number]
}>()

const { createDeck } = useDeck()

const form = reactive({
  name: '',
  shortName: '',
  importDefaultCards: true
})

const loading = ref(false)
const error = ref('')

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

watch(isOpen, (value) => {
  if (value) {
    form.name = ''
    form.shortName = ''
    form.importDefaultCards = true
    error.value = ''
  }
})

async function handleSubmit() {
  if (!form.name.trim() || !form.shortName.trim()) {
    error.value = 'Nome e abbreviazione sono obbligatori'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const deck = await createDeck(
      { name: form.name.trim(), shortName: form.shortName.trim().toUpperCase().slice(0, 5) },
      form.importDefaultCards
    )
    emit('created', (deck as { id: number }).id)
    isOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Errore durante la creazione'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen" title="Nuovo Deck" :ui="{ footer: 'justify-end' }">
    <template #body>
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <UFormField label="Nome deck">
          <UInput
            v-model="form.name"
            placeholder="Es: Cards Against Humanity"
            autofocus
          />
        </UFormField>

        <UFormField label="Abbreviazione (max 5 caratteri)">
          <UInput
            v-model="form.shortName"
            placeholder="Es: CAH"
            :maxlength="5"
            class="uppercase"
          />
        </UFormField>

        <UCheckbox
          v-model="form.importDefaultCards"
          label="Importa carte di default"
        />

        <p v-if="error" class="text-sm text-error">{{ error }}</p>
      </form>
    </template>

    <template #footer="{ close }">
      <UButton variant="ghost" @click="close">
        Annulla
      </UButton>
      <UButton :loading="loading" @click="handleSubmit">
        Crea Deck
      </UButton>
    </template>
  </UModal>
</template>
