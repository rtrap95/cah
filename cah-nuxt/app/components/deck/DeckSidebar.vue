<script setup lang="ts">
import type { Deck } from '~/types'

const props = defineProps<{
  deck: Deck
}>()

const emit = defineEmits<{
  'browse-cards': []
  'batch-add': []
  'export': []
  'random': []
  'edit': []
}>()

const blackCount = computed(() => props.deck.blackCards.length)
const whiteCount = computed(() => props.deck.whiteCards.length)
const totalCards = computed(() => blackCount.value + whiteCount.value)
</script>

<template>
  <aside class="w-64 shrink-0 border-r border-gray-200 dark:border-gray-800 p-4 space-y-6">
    <div>
      <h2 class="text-lg font-bold truncate">{{ deck.config.name }}</h2>
      <p class="text-xs text-gray-500 font-mono">{{ deck.config.shortName }}</p>
    </div>

    <div class="space-y-2">
      <h3 class="text-xs font-semibold uppercase text-gray-500">Statistiche</h3>
      <div class="grid grid-cols-2 gap-2 text-sm">
        <div class="bg-gray-900 text-white rounded-lg p-3 text-center">
          <div class="text-2xl font-bold">{{ blackCount }}</div>
          <div class="text-xs opacity-70">Nere</div>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3 text-center dark:bg-gray-800 dark:border-gray-700">
          <div class="text-2xl font-bold">{{ whiteCount }}</div>
          <div class="text-xs text-gray-500">Bianche</div>
        </div>
      </div>
      <p class="text-xs text-center text-gray-500">{{ totalCards }} carte totali</p>
    </div>

    <div class="space-y-2">
      <h3 class="text-xs font-semibold uppercase text-gray-500">Azioni</h3>

      <UButton
        block
        variant="soft"
        icon="i-lucide-library"
        @click="emit('browse-cards')"
      >
        Sfoglia Carte
      </UButton>

      <UButton
        block
        variant="soft"
        icon="i-lucide-list-plus"
        @click="emit('batch-add')"
      >
        Aggiungi Multiple
      </UButton>

      <UButton
        block
        variant="soft"
        icon="i-lucide-shuffle"
        @click="emit('random')"
      >
        Combo Casuale
      </UButton>

      <UButton
        block
        variant="soft"
        icon="i-lucide-download"
        @click="emit('export')"
      >
        Esporta PDF
      </UButton>

      <UButton
        block
        variant="ghost"
        icon="i-lucide-settings"
        @click="emit('edit')"
      >
        Impostazioni Deck
      </UButton>
    </div>
  </aside>
</template>
