<script setup lang="ts">
import type { Card, CardType } from '~/types'

const props = withDefaults(defineProps<{
  cards: Card[]
  filter?: CardType | 'all'
  searchQuery?: string
  itemsPerPage?: number
}>(), {
  filter: 'all',
  searchQuery: '',
  itemsPerPage: 30
})

const emit = defineEmits<{
  'card-click': [card: Card]
}>()

const filteredCards = computed(() => {
  let result = props.cards

  if (props.filter !== 'all') {
    result = result.filter(c => c.cardType === props.filter)
  }

  if (props.searchQuery) {
    const query = props.searchQuery.toLowerCase()
    result = result.filter(c => c.text.toLowerCase().includes(query))
  }

  return result
})

const { currentPage, totalPages, paginatedItems, hasNextPage, hasPrevPage, nextPage, prevPage, reset } = usePagination(filteredCards, props.itemsPerPage)

// Reset pagination when filter or search changes
watch([() => props.filter, () => props.searchQuery], () => {
  reset()
})

function handleCardClick(card: Card) {
  emit('card-click', card)
}
</script>

<template>
  <div class="space-y-4">
    <UEmpty
      v-if="filteredCards.length === 0"
      icon="i-lucide-search-x"
      title="Nessuna carta trovata"
      description="Prova a modificare i filtri di ricerca"
    />

    <template v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
        <CardFrame
          v-for="(card, idx) in paginatedItems"
          :key="card.id"
          :card="card"
          :index="(currentPage - 1) * itemsPerPage + idx"
          clickable
          @click="handleCardClick"
        />
      </div>

      <div v-if="totalPages > 1" class="flex justify-center pt-4">
        <UPagination
          v-model:page="currentPage"
          :total="filteredCards.length"
          :items-per-page="itemsPerPage"
          :sibling-count="1"
          show-edges
        />
      </div>
    </template>
  </div>
</template>
