<script setup lang="ts">
import type { CardType } from '~/types'

const props = defineProps<{
  open: boolean
  deckId: number
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  added: []
}>()

const { addCard } = useCards()

const form = reactive({
  text: '',
  cardType: 'black' as CardType,
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

const cardTypeOptions = [
  { label: 'Nera (domanda)', value: 'black' },
  { label: 'Bianca (risposta)', value: 'white' }
]

watch(isOpen, (value) => {
  if (value) {
    form.text = ''
    form.cardType = 'black'
    form.pick = 1
    error.value = ''
  }
})

async function handleSubmit() {
  if (!form.text.trim()) {
    error.value = 'Il testo della carta è obbligatorio'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await addCard(props.deckId, form.text.trim(), form.cardType, form.pick)
    emit('added')
    isOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Errore durante l\'aggiunta'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen" title="Aggiungi Carta" :ui="{ footer: 'justify-end' }">
    <template #body>
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <UFormField label="Tipo carta">
          <URadioGroup
            v-model="form.cardType"
            :items="cardTypeOptions"
            orientation="horizontal"
          />
        </UFormField>

        <UFormField label="Testo carta">
          <UTextarea
            v-model="form.text"
            placeholder="Scrivi il testo della carta... Usa _____ per i blank"
            :rows="4"
          />
        </UFormField>

        <UFormField v-if="form.cardType === 'black'" label="Carte da pescare">
          <USelect
            v-model="form.pick"
            :items="pickOptions"
            value-key="value"
          />
        </UFormField>

        <p class="text-xs text-muted">
          Suggerimento: usa _____ per indicare i blank nelle carte nere
        </p>

        <p v-if="error" class="text-sm text-error">{{ error }}</p>
      </form>
    </template>

    <template #footer="{ close }">
      <UButton variant="ghost" @click="close">
        Annulla
      </UButton>
      <UButton :loading="loading" @click="handleSubmit">
        Aggiungi
      </UButton>
    </template>
  </UModal>
</template>
