<script setup lang="ts">
import type { Deck } from '~/types'

const props = defineProps<{
  open: boolean
  deck: Deck | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const toast = useToast()

const form = reactive({
  name: '',
  shortName: '',
  blackLogoPath: null as string | null,
  whiteLogoPath: null as string | null,
  blackBackLogoPath: null as string | null,
  whiteBackLogoPath: null as string | null
})

const loading = ref(false)
const error = ref('')
const uploadingLogo = ref<string | null>(null)

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

watch(() => props.deck, (deck) => {
  if (deck) {
    form.name = deck.config.name
    form.shortName = deck.config.shortName
    form.blackLogoPath = deck.config.blackLogoPath || null
    form.whiteLogoPath = deck.config.whiteLogoPath || null
    form.blackBackLogoPath = deck.config.blackBackLogoPath || null
    form.whiteBackLogoPath = deck.config.whiteBackLogoPath || null
  }
}, { immediate: true })

async function uploadLogo(logoType: 'blackLogo' | 'whiteLogo' | 'blackBackLogo' | 'whiteBackLogo', file: File) {
  if (!props.deck?.id) return

  uploadingLogo.value = logoType

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('deckId', String(props.deck.id))
    formData.append('logoType', logoType)

    const result = await $fetch<{ path: string }>('/api/upload/logo', {
      method: 'POST',
      body: formData
    })

    // Update the form with the new path
    const pathKey = `${logoType}Path` as keyof typeof form
    form[pathKey] = result.path as any

    toast.add({
      title: 'Logo caricato',
      color: 'success'
    })
  } catch (e) {
    toast.add({
      title: 'Errore upload',
      description: e instanceof Error ? e.message : 'Errore durante il caricamento',
      color: 'error'
    })
  } finally {
    uploadingLogo.value = null
  }
}

function handleFileChange(logoType: 'blackLogo' | 'whiteLogo' | 'blackBackLogo' | 'whiteBackLogo', files: FileList | null) {
  if (files && files.length > 0) {
    uploadLogo(logoType, files[0])
  }
}

function removeLogo(logoType: 'blackLogo' | 'whiteLogo' | 'blackBackLogo' | 'whiteBackLogo') {
  const pathKey = `${logoType}Path` as keyof typeof form
  form[pathKey] = null as any
}

async function handleSubmit() {
  if (!props.deck?.id) return

  if (!form.name.trim() || !form.shortName.trim()) {
    error.value = 'Nome e abbreviazione sono obbligatori'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await $fetch(`/api/decks/${props.deck.id}`, {
      method: 'PUT',
      body: {
        name: form.name.trim(),
        shortName: form.shortName.trim().toUpperCase().slice(0, 5),
        blackLogoPath: form.blackLogoPath,
        whiteLogoPath: form.whiteLogoPath,
        blackBackLogoPath: form.blackBackLogoPath,
        whiteBackLogoPath: form.whiteBackLogoPath
      }
    })

    toast.add({
      title: 'Impostazioni salvate',
      color: 'success'
    })

    emit('saved')
    isOpen.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Errore durante il salvataggio'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen" title="Impostazioni Deck" :ui="{ footer: 'justify-end' }">
    <template #body>
      <form class="space-y-6" @submit.prevent="handleSubmit">
        <!-- Basic info -->
        <div class="space-y-4">
          <UFormField label="Nome deck">
            <UInput
              v-model="form.name"
              placeholder="Es: Cards Against Humanity"
            />
          </UFormField>

          <UFormField label="Abbreviazione (max 5 caratteri)">
            <UInput
              v-model="form.shortName"
              placeholder="Es: CAH"
              :maxlength="5"
              class="uppercase"
            />
          </UFormField>
        </div>

        <USeparator label="Loghi Fronte" />

        <!-- Front logos -->
        <div class="grid grid-cols-2 gap-4">
          <!-- Black card front logo -->
          <div class="space-y-2">
            <label class="text-sm font-medium">Carte Nere</label>
            <div
              class="relative aspect-square rounded-lg border-2 border-dashed border-default bg-gray-900 flex items-center justify-center overflow-hidden"
            >
              <img
                v-if="form.blackLogoPath"
                :src="form.blackLogoPath"
                alt="Logo carte nere"
                class="w-full h-full object-contain p-2"
              >
              <UIcon v-else name="i-lucide-image" class="size-8 text-gray-500" />

              <div class="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 hover:opacity-100 transition-opacity">
                <UButton
                  size="xs"
                  color="neutral"
                  variant="solid"
                  icon="i-lucide-upload"
                  :loading="uploadingLogo === 'blackLogo'"
                  @click="($refs.blackLogoInput as HTMLInputElement)?.click()"
                />
                <UButton
                  v-if="form.blackLogoPath"
                  size="xs"
                  color="error"
                  variant="solid"
                  icon="i-lucide-trash-2"
                  @click="removeLogo('blackLogo')"
                />
              </div>
            </div>
            <input
              ref="blackLogoInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileChange('blackLogo', ($event.target as HTMLInputElement).files)"
            >
          </div>

          <!-- White card front logo -->
          <div class="space-y-2">
            <label class="text-sm font-medium">Carte Bianche</label>
            <div
              class="relative aspect-square rounded-lg border-2 border-dashed border-default bg-white flex items-center justify-center overflow-hidden"
            >
              <img
                v-if="form.whiteLogoPath"
                :src="form.whiteLogoPath"
                alt="Logo carte bianche"
                class="w-full h-full object-contain p-2"
              >
              <UIcon v-else name="i-lucide-image" class="size-8 text-gray-400" />

              <div class="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 hover:opacity-100 transition-opacity">
                <UButton
                  size="xs"
                  color="neutral"
                  variant="solid"
                  icon="i-lucide-upload"
                  :loading="uploadingLogo === 'whiteLogo'"
                  @click="($refs.whiteLogoInput as HTMLInputElement)?.click()"
                />
                <UButton
                  v-if="form.whiteLogoPath"
                  size="xs"
                  color="error"
                  variant="solid"
                  icon="i-lucide-trash-2"
                  @click="removeLogo('whiteLogo')"
                />
              </div>
            </div>
            <input
              ref="whiteLogoInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileChange('whiteLogo', ($event.target as HTMLInputElement).files)"
            >
          </div>
        </div>

        <USeparator label="Loghi Retro" />

        <!-- Back logos -->
        <div class="grid grid-cols-2 gap-4">
          <!-- Black card back logo -->
          <div class="space-y-2">
            <label class="text-sm font-medium">Retro Nere</label>
            <div
              class="relative aspect-square rounded-lg border-2 border-dashed border-default bg-gray-900 flex items-center justify-center overflow-hidden"
            >
              <img
                v-if="form.blackBackLogoPath"
                :src="form.blackBackLogoPath"
                alt="Logo retro carte nere"
                class="w-full h-full object-contain p-2"
              >
              <UIcon v-else name="i-lucide-image" class="size-8 text-gray-500" />

              <div class="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 hover:opacity-100 transition-opacity">
                <UButton
                  size="xs"
                  color="neutral"
                  variant="solid"
                  icon="i-lucide-upload"
                  :loading="uploadingLogo === 'blackBackLogo'"
                  @click="($refs.blackBackLogoInput as HTMLInputElement)?.click()"
                />
                <UButton
                  v-if="form.blackBackLogoPath"
                  size="xs"
                  color="error"
                  variant="solid"
                  icon="i-lucide-trash-2"
                  @click="removeLogo('blackBackLogo')"
                />
              </div>
            </div>
            <input
              ref="blackBackLogoInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileChange('blackBackLogo', ($event.target as HTMLInputElement).files)"
            >
          </div>

          <!-- White card back logo -->
          <div class="space-y-2">
            <label class="text-sm font-medium">Retro Bianche</label>
            <div
              class="relative aspect-square rounded-lg border-2 border-dashed border-default bg-white flex items-center justify-center overflow-hidden"
            >
              <img
                v-if="form.whiteBackLogoPath"
                :src="form.whiteBackLogoPath"
                alt="Logo retro carte bianche"
                class="w-full h-full object-contain p-2"
              >
              <UIcon v-else name="i-lucide-image" class="size-8 text-gray-400" />

              <div class="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 hover:opacity-100 transition-opacity">
                <UButton
                  size="xs"
                  color="neutral"
                  variant="solid"
                  icon="i-lucide-upload"
                  :loading="uploadingLogo === 'whiteBackLogo'"
                  @click="($refs.whiteBackLogoInput as HTMLInputElement)?.click()"
                />
                <UButton
                  v-if="form.whiteBackLogoPath"
                  size="xs"
                  color="error"
                  variant="solid"
                  icon="i-lucide-trash-2"
                  @click="removeLogo('whiteBackLogo')"
                />
              </div>
            </div>
            <input
              ref="whiteBackLogoInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileChange('whiteBackLogo', ($event.target as HTMLInputElement).files)"
            >
          </div>
        </div>

        <p v-if="error" class="text-sm text-error">{{ error }}</p>
      </form>
    </template>

    <template #footer="{ close }">
      <UButton variant="ghost" @click="close">
        Annulla
      </UButton>
      <UButton :loading="loading" @click="handleSubmit">
        Salva
      </UButton>
    </template>
  </UModal>
</template>
