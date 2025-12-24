<script setup lang="ts">
const route = useRoute()
const toast = useToast()

const deckId = computed(() => Number(route.query.deckId))

const { decks, fetchDecks, currentDeck, loadDeck } = useDeck()

const selectedDeckId = ref<number | null>(null)
const loading = ref(false)
const loadingText = ref(false)

const form = reactive({
  cardsType: 'all' as 'all' | 'black' | 'white',
  includeBacks: false,
  customName: '',
  customShortName: '',
  showShortName: true,
  logoSize: 20,
  backLogoSize: 60,
  cardPadding: 10
})

const cardsTypeOptions = [
  { label: 'Tutte', value: 'all' },
  { label: 'Solo Nere', value: 'black' },
  { label: 'Solo Bianche', value: 'white' }
]

onMounted(async () => {
  await fetchDecks()
  if (deckId.value && !isNaN(deckId.value)) {
    selectedDeckId.value = deckId.value
    await loadDeck(deckId.value)
    if (currentDeck.value) {
      form.customName = currentDeck.value.config.name
      form.customShortName = currentDeck.value.config.shortName
    }
  }
})

watch(selectedDeckId, async (id) => {
  if (id) {
    await loadDeck(id)
    if (currentDeck.value) {
      form.customName = currentDeck.value.config.name
      form.customShortName = currentDeck.value.config.shortName
    }
  }
})

const deckOptions = computed(() =>
  decks.value.map(d => ({ label: d.name, value: d.id }))
)

async function handleExport() {
  if (!selectedDeckId.value) return

  loading.value = true

  try {
    const response = await $fetch('/api/export/pdf', {
      method: 'POST',
      body: {
        deckId: selectedDeckId.value,
        cardsType: form.cardsType,
        includeBacks: form.includeBacks,
        deckName: form.customName,
        shortName: form.customShortName,
        showShortName: form.showShortName,
        logoSize: form.logoSize,
        backLogoSize: form.backLogoSize,
        cardPadding: form.cardPadding
      },
      responseType: 'blob'
    })

    // Download the PDF
    const blob = new Blob([response as BlobPart], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${form.customShortName || 'cards'}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast.add({
      title: 'PDF esportato',
      description: 'Il file è stato scaricato con successo',
      color: 'success'
    })
  } catch (e) {
    toast.add({
      title: 'Errore',
      description: e instanceof Error ? e.message : 'Errore durante l\'esportazione',
      color: 'error'
    })
  } finally {
    loading.value = false
  }
}

async function handleExportText() {
  if (!selectedDeckId.value) return

  loadingText.value = true

  try {
    const response = await $fetch('/api/export/text', {
      method: 'POST',
      body: {
        deckId: selectedDeckId.value,
        cardsType: form.cardsType
      },
      responseType: 'text'
    })

    // Download the text file
    const blob = new Blob([response as string], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${form.customShortName || 'cards'}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast.add({
      title: 'Testo esportato',
      description: 'Il file è stato scaricato con successo',
      color: 'success'
    })
  } catch (e) {
    toast.add({
      title: 'Errore',
      description: e instanceof Error ? e.message : 'Errore durante l\'esportazione',
      color: 'error'
    })
  } finally {
    loadingText.value = false
  }
}
</script>

<template>
  <div class="min-h-screen">
    <div class="max-w-2xl mx-auto px-4 py-12">
      <!-- Header -->
      <div class="flex items-center gap-4 mb-8">
        <UButton
          variant="ghost"
          icon="i-lucide-arrow-left"
          to="/"
        >
          Indietro
        </UButton>
        <h1 class="text-2xl font-bold">Esporta Deck</h1>
      </div>

      <!-- Export Form -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-6">
        <UFormField label="Seleziona deck">
          <USelect
            v-model="selectedDeckId"
            :items="deckOptions"
            value-key="value"
            placeholder="Seleziona un deck"
          />
        </UFormField>

        <UFormField label="Nome deck (per la stampa)">
          <UInput v-model="form.customName" placeholder="Cards Against Humanity" />
        </UFormField>

        <UFormField label="Abbreviazione">
          <UInput
            v-model="form.customShortName"
            placeholder="CAH"
            :maxlength="5"
            class="uppercase"
          />
        </UFormField>

        <UFormField label="Tipo di carte">
          <USelect
            v-model="form.cardsType"
            :items="cardsTypeOptions"
            value-key="value"
          />
        </UFormField>

        <UCheckbox
          v-model="form.includeBacks"
          label="Includi retro delle carte (per stampa fronte-retro)"
        />

        <UCheckbox
          v-model="form.showShortName"
          label="Mostra abbreviazione sulle carte"
        />

        <UFormField label="Dimensione logo frontale (px)">
          <div class="flex items-center gap-4">
            <USlider
              v-model="form.logoSize"
              :min="10"
              :max="40"
              :step="2"
              class="flex-1"
            />
            <span class="text-sm text-gray-500 w-12 text-right">{{ form.logoSize }}px</span>
          </div>
        </UFormField>

        <UFormField label="Dimensione logo retro (px)">
          <div class="flex items-center gap-4">
            <USlider
              v-model="form.backLogoSize"
              :min="30"
              :max="100"
              :step="5"
              class="flex-1"
            />
            <span class="text-sm text-gray-500 w-12 text-right">{{ form.backLogoSize }}px</span>
          </div>
        </UFormField>

        <UFormField label="Padding carte (px)">
          <div class="flex items-center gap-4">
            <USlider
              v-model="form.cardPadding"
              :min="5"
              :max="20"
              :step="1"
              class="flex-1"
            />
            <span class="text-sm text-gray-500 w-12 text-right">{{ form.cardPadding }}px</span>
          </div>
        </UFormField>

        <div class="pt-4 space-y-3">
          <UButton
            block
            size="lg"
            icon="i-lucide-download"
            :loading="loading"
            :disabled="!selectedDeckId"
            @click="handleExport"
          >
            Esporta PDF
          </UButton>
          <UButton
            block
            size="lg"
            variant="outline"
            icon="i-lucide-file-text"
            :loading="loadingText"
            :disabled="!selectedDeckId"
            @click="handleExportText"
          >
            Esporta Testo (per AI)
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>
