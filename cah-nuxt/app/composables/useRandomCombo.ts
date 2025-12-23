import type { RandomCombo } from '~/types'

export function useRandomCombo() {
  const combo = useState<RandomCombo | null>('randomCombo', () => null)
  const loading = useState('comboLoading', () => false)
  const error = useState<string | null>('comboError', () => null)

  async function generateCombo(deckId: number) {
    loading.value = true
    error.value = null
    try {
      combo.value = await $fetch<RandomCombo>(`/api/random/combo?deckId=${deckId}`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to generate combo'
      combo.value = null
    } finally {
      loading.value = false
    }
  }

  function clearCombo() {
    combo.value = null
    error.value = null
  }

  return {
    combo,
    loading,
    error,
    generateCombo,
    clearCombo
  }
}
