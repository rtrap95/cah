<script setup lang="ts">
const props = defineProps<{
  deckId: number
}>()

const { combo, loading, error, generateCombo } = useRandomCombo()

onMounted(() => {
  generateCombo(props.deckId)
})

function refresh() {
  generateCombo(props.deckId)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Loading skeleton -->
    <template v-if="loading">
      <USkeleton class="h-40 max-w-md mx-auto rounded-2xl" />
      <div class="flex justify-center">
        <USkeleton class="h-8 w-8 rounded-full" />
      </div>
      <div class="flex justify-center gap-4">
        <USkeleton class="h-24 w-40 rounded-2xl" />
        <USkeleton class="h-24 w-40 rounded-2xl" />
      </div>
      <USkeleton class="h-24 max-w-2xl mx-auto rounded-2xl" />
    </template>

    <!-- Error state -->
    <UEmpty
      v-else-if="error"
      icon="i-lucide-alert-circle"
      :title="error"
      description="Si è verificato un errore durante il caricamento"
      :actions="[{ label: 'Riprova', icon: 'i-lucide-refresh-cw', onClick: refresh }]"
    />

    <div v-else-if="combo" class="space-y-6">
      <!-- Black Card -->
      <div class="bg-gray-900 text-white rounded-2xl p-6 max-w-md mx-auto">
        <p class="text-xl font-bold leading-relaxed">{{ combo.blackCard.text }}</p>
        <div v-if="combo.blackCard.pick > 1" class="mt-4 text-right text-sm opacity-70">
          PICK {{ combo.blackCard.pick }}
        </div>
      </div>

      <!-- Arrow -->
      <div class="flex justify-center">
        <UIcon name="i-lucide-arrow-down" class="w-8 h-8 text-gray-400" />
      </div>

      <!-- White Cards -->
      <div class="flex flex-wrap justify-center gap-4">
        <div
          v-for="(white, idx) in combo.whiteCards"
          :key="white.id"
          class="bg-white border-2 border-gray-200 rounded-2xl p-4 max-w-[200px]"
        >
          <span class="text-xs text-gray-400 font-mono">#{{ idx + 1 }}</span>
          <p class="font-bold mt-1">{{ white.text }}</p>
        </div>
      </div>

      <!-- Combined Result -->
      <div class="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-6 max-w-2xl mx-auto">
        <h4 class="text-sm font-semibold uppercase text-gray-500 mb-2">Risultato</h4>
        <p class="text-lg" v-html="combo.combinedText.replace(/\*\*(.*?)\*\*/g, '<strong class=\'text-primary\'>$1</strong>')"></p>
      </div>

      <!-- Refresh Button -->
      <div class="flex justify-center">
        <UButton
          size="lg"
          icon="i-lucide-refresh-cw"
          :loading="loading"
          @click="refresh"
        >
          Nuova Combo
        </UButton>
      </div>
    </div>
  </div>
</template>
