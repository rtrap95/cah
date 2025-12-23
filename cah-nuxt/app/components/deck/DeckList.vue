<script setup lang="ts">
import type { DeckListItem } from '~/types'

defineProps<{
  decks: DeckListItem[]
  loading?: boolean
}>()

const emit = defineEmits<{
  select: [deck: DeckListItem]
  delete: [deck: DeckListItem]
}>()
</script>

<template>
  <div class="space-y-2">
    <!-- Loading skeleton -->
    <template v-if="loading">
      <div
        v-for="i in 3"
        :key="i"
        class="flex items-center gap-4 p-4 rounded-lg border border-default"
      >
        <div class="flex-1 space-y-2">
          <USkeleton class="h-5 w-48" />
          <USkeleton class="h-4 w-24" />
        </div>
        <USkeleton class="h-8 w-8 rounded-md" />
      </div>
    </template>

    <!-- Empty state -->
    <UEmpty
      v-else-if="decks.length === 0"
      icon="i-lucide-folder-open"
      title="Nessun deck trovato"
      description="Crea un nuovo deck per iniziare"
    />

    <!-- Deck list -->
    <div
      v-else
      v-for="deck in decks"
      :key="deck.id"
      class="flex items-center gap-4 p-4 rounded-lg border border-default hover:bg-elevated/50 transition-colors cursor-pointer"
      @click="emit('select', deck)"
    >
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold truncate">{{ deck.name }}</h3>
        <p class="text-sm text-muted">
          <span class="inline-flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-inverted" />
            {{ deck.blackCount }}
          </span>
          <span class="mx-2">•</span>
          <span class="inline-flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-default ring-1 ring-default" />
            {{ deck.whiteCount }}
          </span>
        </p>
      </div>

      <UButton
        variant="ghost"
        color="error"
        icon="i-lucide-trash-2"
        size="sm"
        @click.stop="emit('delete', deck)"
      />
    </div>
  </div>
</template>
