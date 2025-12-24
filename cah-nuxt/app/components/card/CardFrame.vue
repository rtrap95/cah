<script setup lang="ts">
import type { Card } from '~/types'

const props = defineProps<{
  card: Card
  index?: number
  clickable?: boolean
}>()

const emit = defineEmits<{
  click: [card: Card]
}>()

const isBlack = computed(() => props.card.cardType === 'black')

const textStyle = computed(() => ({
  fontSize: `${(props.card.fontSize || 100) / 100}em`
}))

function handleClick() {
  if (props.clickable) {
    emit('click', props.card)
  }
}
</script>

<template>
  <div
    class="card-frame relative rounded-xl p-4 min-h-[180px] flex flex-col transition-all duration-200"
    :class="[
      isBlack ? 'bg-gray-900 text-white' : 'bg-white text-gray-900 border border-gray-200',
      clickable ? 'cursor-pointer hover:scale-[1.02] hover:shadow-lg' : ''
    ]"
    @click="handleClick"
  >
    <span
      v-if="index !== undefined"
      class="absolute top-2 left-3 text-xs font-mono opacity-50"
    >
      #{{ index + 1 }}
    </span>

    <div class="flex-1 flex items-center justify-center pt-4">
      <p class="text-sm font-bold text-center leading-relaxed" :style="textStyle">
        {{ card.text }}
      </p>
    </div>

    <div v-if="isBlack && card.pick > 1" class="mt-2 text-right">
      <span class="text-xs opacity-70">PICK {{ card.pick }}</span>
    </div>
  </div>
</template>

<style scoped>
.card-frame {
  aspect-ratio: 2.5 / 3.5;
}
</style>
