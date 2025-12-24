<script setup lang="ts">
import type { DeckListItem } from '~/types'

const router = useRouter()
const { decks, isLoadingDecks, fetchDecks, deleteDeck } = useDeck()
const { confirm } = useConfirm()

const showNewDeckModal = ref(false)

onMounted(() => {
  fetchDecks()
})

function handleSelectDeck(deck: DeckListItem) {
  router.push(`/deck/${deck.id}`)
}

async function handleDeleteDeck(deck: DeckListItem) {
  const confirmed = await confirm({
    title: 'Elimina deck',
    description: `Sei sicuro di voler eliminare "${deck.name}"? Questa azione non può essere annullata.`,
    confirmLabel: 'Elimina',
    confirmColor: 'error',
    icon: 'i-lucide-trash-2'
  })
  if (!confirmed) return
  await deleteDeck(deck.id)
}

function handleDeckCreated(deckId: number) {
  router.push(`/deck/${deckId}`)
}
</script>

<template>
  <div class="min-h-screen">
    <div class="max-w-4xl mx-auto px-4 py-12">
      <!-- Header -->
      <div class="text-center mb-12">
        <h1 class="text-4xl font-black mb-4">
          Cards Against Humanity
        </h1>
        <p class="text-lg text-gray-600 dark:text-gray-400">
          Crea e gestisci i tuoi mazzi di carte personalizzati
        </p>
      </div>

      <!-- Actions -->
      <div class="flex justify-center mb-8">
        <UButton
          size="lg"
          icon="i-lucide-plus"
          @click="showNewDeckModal = true"
        >
          Nuovo Deck
        </UButton>
      </div>

      <!-- Deck List -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
        <h2 class="text-lg font-semibold mb-4">I tuoi Deck</h2>
        <DeckList
          :decks="decks"
          :loading="isLoadingDecks"
          @select="handleSelectDeck"
          @delete="handleDeleteDeck"
        />
      </div>
    </div>

    <!-- New Deck Modal -->
    <ModalNewDeckModal
      v-model:open="showNewDeckModal"
      @created="handleDeckCreated"
    />
  </div>
</template>
