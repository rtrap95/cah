<script setup>
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'it'
  }
})

const title = 'Cards Against Humanity - Generator'
const description = 'Crea e gestisci i tuoi mazzi di carte personalizzati per Cards Against Humanity'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description
})
</script>

<template>
  <UApp>
    <UHeader>
      <template #left>
        <NuxtLink to="/" class="flex items-center gap-2">
          <span class="text-xl font-black">CAH</span>
          <span class="text-sm text-gray-500">Generator</span>
        </NuxtLink>
      </template>

      <template #right>
        <UButton
          to="/random"
          variant="ghost"
          icon="i-lucide-shuffle"
        >
          Random
        </UButton>

        <UButton
          to="/export"
          variant="ghost"
          icon="i-lucide-download"
        >
          Export
        </UButton>

        <UColorModeButton />
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>

    <UFooter>
      <template #left>
        <p class="text-sm text-muted">
          Cards Against Humanity Generator
        </p>
      </template>
    </UFooter>

    <UToaster />
  </UApp>
</template>
