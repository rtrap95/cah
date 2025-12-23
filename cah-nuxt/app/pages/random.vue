<script setup lang="ts">
const route = useRoute()

const deckId = computed(() => Number(route.query.deckId))

const { decks, fetchDecks } = useDeck()
const selectedDeckId = ref<number | null>(null)

onMounted(async () => {
  await fetchDecks()
  if (deckId.value && !isNaN(deckId.value)) {
    selectedDeckId.value = deckId.value
  } else if (decks.value.length > 0) {
    selectedDeckId.value = decks.value[0].id
  }
})

const deckOptions = computed(() =>
  decks.value.map(d => ({ label: d.name, value: d.id }))
)
</script>

<template>
  <div class="min-h-screen">
    <div class="max-w-4xl mx-auto px-4 py-12">
      <!-- Header -->
      <div class="flex items-center gap-4 mb-8">
        <UButton
          variant="ghost"
          icon="i-lucide-arrow-left"
          to="/"
        >
          Indietro
        </UButton>
        <h1 class="text-2xl font-bold">Combo Casuale</h1>
      </div>

      <!-- Deck Selector -->
      <div class="flex items-center gap-4 mb-8">
        <label class="text-sm font-medium">Seleziona deck:</label>
        <USelect
          v-model="selectedDeckId"
          :items="deckOptions"
          value-key="value"
          placeholder="Seleziona un deck"
          class="w-64"
        />
      </div>

      <!-- Random Combo -->
      <div v-if="selectedDeckId" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8">
        <RandomCombo :deck-id="selectedDeckId" />
      </div>

      <UEmpty
        v-else
        icon="i-lucide-shuffle"
        title="Seleziona un deck"
        description="Scegli un deck per generare combo casuali"
      />
    </div>
  </div>
</template>
