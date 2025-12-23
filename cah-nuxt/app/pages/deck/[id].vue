<script setup lang="ts">
import type { Card, CardType } from '~/types'

const route = useRoute()
const router = useRouter()

const deckId = computed(() => Number(route.params.id))
const { currentDeck, loading, loadDeck } = useDeck()

// Filter state
const cardFilter = ref<CardType | 'all'>('all')
const searchQuery = ref('')

// Modals state
const showAddCardModal = ref(false)
const showBatchAddModal = ref(false)
const showEditCardModal = ref(false)
const showSettingsModal = ref(false)
const editingCard = ref<Card | null>(null)

// Load deck on mount
onMounted(async () => {
  await loadDeck(deckId.value)
})

// All cards combined for the grid
const allCards = computed(() => {
  if (!currentDeck.value) return []
  return [...currentDeck.value.blackCards, ...currentDeck.value.whiteCards]
})

// Filter options
const filterOptions = [
  { label: 'Tutte', value: 'all' },
  { label: 'Nere', value: 'black' },
  { label: 'Bianche', value: 'white' }
]

function handleCardClick(card: Card) {
  editingCard.value = card
  showEditCardModal.value = true
}

function handleAddCard() {
  showAddCardModal.value = true
}

function handleBatchAdd() {
  showBatchAddModal.value = true
}

function handleRandom() {
  router.push(`/random?deckId=${deckId.value}`)
}

function handleExport() {
  router.push(`/export?deckId=${deckId.value}`)
}

function handleEdit() {
  showSettingsModal.value = true
}

async function refreshDeck() {
  await loadDeck(deckId.value)
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Loading -->
    <div v-if="loading" class="flex-1 p-6">
      <div class="flex items-center gap-4 mb-6">
        <USkeleton class="h-10 w-24" />
        <div class="flex-1" />
        <USkeleton class="h-10 w-64" />
        <USkeleton class="h-10 w-32" />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <USkeleton v-for="i in 6" :key="i" class="h-48 rounded-xl" />
      </div>
    </div>

    <!-- Deck not found -->
    <div v-else-if="!currentDeck" class="flex-1 flex items-center justify-center">
      <UEmpty
        icon="i-lucide-folder-x"
        title="Deck non trovato"
        description="Il deck richiesto non esiste o è stato eliminato"
        :actions="[{ label: 'Torna alla home', to: '/', variant: 'soft' }]"
      />
    </div>

    <!-- Deck Editor -->
    <template v-else>
      <!-- Sidebar -->
      <DeckSidebar
        :deck="currentDeck"
        @add-card="handleAddCard"
        @batch-add="handleBatchAdd"
        @random="handleRandom"
        @export="handleExport"
        @edit="handleEdit"
      />

      <!-- Main Content -->
      <main class="flex-1 p-6 overflow-auto">
        <!-- Header -->
        <div class="flex flex-wrap items-center gap-4 mb-6">
          <UButton
            variant="ghost"
            icon="i-lucide-arrow-left"
            to="/"
          >
            Indietro
          </UButton>

          <div class="flex-1" />

          <UInput
            v-model="searchQuery"
            placeholder="Cerca carte..."
            icon="i-lucide-search"
            class="w-64"
          />

          <USelect
            v-model="cardFilter"
            :items="filterOptions"
            value-key="value"
            class="w-32"
          />
        </div>

        <!-- Cards Grid -->
        <CardGrid
          :cards="allCards"
          :filter="cardFilter"
          :search-query="searchQuery"
          @card-click="handleCardClick"
        />
      </main>
    </template>

    <!-- Modals -->
    <ModalAddCardModal
      v-model:open="showAddCardModal"
      :deck-id="deckId"
      @added="refreshDeck"
    />

    <ModalBatchAddModal
      v-model:open="showBatchAddModal"
      :deck-id="deckId"
      @added="refreshDeck"
    />

    <ModalEditCardModal
      v-model:open="showEditCardModal"
      :card="editingCard"
      @saved="refreshDeck"
      @deleted="refreshDeck"
    />

    <ModalDeckSettingsModal
      v-model:open="showSettingsModal"
      :deck="currentDeck"
      @saved="refreshDeck"
    />
  </div>
</template>
