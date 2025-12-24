<script setup lang="ts">
import type { Card, CardType } from '~/types'

const props = defineProps<{
  open: boolean
  deckId: number
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  added: []
}>()

const { fetchAllCards, copyCardToDeck } = useCards()
const toast = useToast()

const cards = ref<(Card & { deckName: string })[]>([])
const loading = ref(false)
const copying = ref<number | null>(null)
const searchQuery = ref('')
const cardTypeFilter = ref<CardType | 'all'>('all')

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const filterOptions = [
  { label: 'Tutte', value: 'all' },
  { label: 'Nere', value: 'black' },
  { label: 'Bianche', value: 'white' }
]

const filteredCards = computed(() => {
  let result = cards.value

  if (cardTypeFilter.value !== 'all') {
    result = result.filter(c => c.cardType === cardTypeFilter.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(c => c.text.toLowerCase().includes(q))
  }

  return result
})

async function loadCards() {
  loading.value = true
  try {
    cards.value = await fetchAllCards(props.deckId)
  } catch (e) {
    toast.add({
      title: 'Errore',
      description: 'Impossibile caricare le carte',
      color: 'error'
    })
  } finally {
    loading.value = false
  }
}

async function handleCopyCard(card: Card & { deckName: string }) {
  if (!card.id || copying.value !== null) return

  copying.value = card.id
  try {
    await copyCardToDeck(card.id, props.deckId)
    // Remove the card from the list since it's now in the deck
    cards.value = cards.value.filter(c => c.id !== card.id)
    toast.add({
      title: 'Carta aggiunta',
      description: `"${card.text.substring(0, 30)}..." aggiunta al deck`,
      color: 'success'
    })
    emit('added')
  } catch (e) {
    toast.add({
      title: 'Errore',
      description: 'Impossibile copiare la carta',
      color: 'error'
    })
  } finally {
    copying.value = null
  }
}

watch(isOpen, (value) => {
  if (value) {
    searchQuery.value = ''
    cardTypeFilter.value = 'all'
    loadCards()
  }
})
</script>

<template>
  <UModal
    v-model:open="isOpen"
    title="Sfoglia Carte"
    :ui="{ width: 'sm:max-w-4xl', footer: 'justify-end' }"
  >
    <template #body>
      <div class="space-y-4">
        <!-- Filters -->
        <div class="flex gap-4">
          <UInput
            v-model="searchQuery"
            placeholder="Cerca carte..."
            icon="i-lucide-search"
            class="flex-1"
          />
          <USelect
            v-model="cardTypeFilter"
            :items="filterOptions"
            value-key="value"
            class="w-32"
          />
        </div>

        <!-- Cards List -->
        <div v-if="loading" class="max-h-[60vh] overflow-y-auto space-y-2">
          <div
            v-for="i in 8"
            :key="i"
            class="flex items-center gap-3 p-3 rounded-lg border"
            :class="i % 3 === 0 ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200 dark:bg-gray-800 dark:border-gray-700'"
          >
            <div class="flex-1 space-y-2">
              <USkeleton class="h-4 w-full" :class="i % 3 === 0 ? 'bg-gray-700' : ''" />
              <USkeleton class="h-3 w-24" :class="i % 3 === 0 ? 'bg-gray-700' : ''" />
            </div>
            <USkeleton class="h-7 w-20 rounded" :class="i % 3 === 0 ? 'bg-gray-700' : ''" />
          </div>
        </div>

        <div v-else-if="filteredCards.length === 0" class="text-center py-12 text-gray-500">
          <UIcon name="i-lucide-inbox" class="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Nessuna carta trovata</p>
        </div>

        <div v-else class="max-h-[60vh] overflow-y-auto space-y-2">
          <div
            v-for="card in filteredCards"
            :key="card.id"
            class="group flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors"
            :class="[
              card.cardType === 'black'
                ? 'bg-gray-900 text-white border-gray-800 hover:bg-gray-800'
                : 'bg-white border-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700'
            ]"
            @click="handleCopyCard(card)"
          >
            <div class="flex-1">
              <p class="text-sm">{{ card.text }}</p>
              <p class="text-xs mt-1" :class="card.cardType === 'black' ? 'text-gray-400' : 'text-gray-500'">
                Da: {{ card.deckName }}
                <span v-if="card.cardType === 'black' && card.pick > 1" class="ml-2">
                  PICK {{ card.pick }}
                </span>
              </p>
            </div>
            <UButton
              size="xs"
              :variant="card.cardType === 'black' ? 'soft' : 'outline'"
              :loading="copying === card.id"
              icon="i-lucide-plus"
              class="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              @click.stop="handleCopyCard(card)"
            >
              Aggiungi
            </UButton>
          </div>
        </div>

        <div v-if="loading" class="flex justify-center">
          <USkeleton class="h-4 w-32" />
        </div>
        <p v-else class="text-xs text-gray-500 text-center">
          {{ filteredCards.length }} carte disponibili
        </p>
      </div>
    </template>

    <template #footer="{ close }">
      <UButton variant="ghost" @click="close">
        Chiudi
      </UButton>
    </template>
  </UModal>
</template>
