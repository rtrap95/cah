import type { Deck, DeckListItem, DeckConfig } from '~/types'

export function useDeck() {
  const currentDeck = useState<Deck | null>('currentDeck', () => null)
  const decks = useState<DeckListItem[]>('decks', () => [])
  const loading = useState('deckLoading', () => false)
  const error = useState<string | null>('deckError', () => null)

  async function fetchDecks() {
    loading.value = true
    error.value = null
    try {
      decks.value = await $fetch<DeckListItem[]>('/api/decks')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch decks'
    } finally {
      loading.value = false
    }
  }

  async function loadDeck(id: number) {
    loading.value = true
    error.value = null
    try {
      currentDeck.value = await $fetch<Deck>(`/api/decks/${id}`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load deck'
      currentDeck.value = null
    } finally {
      loading.value = false
    }
  }

  async function createDeck(config: Partial<DeckConfig> & { name: string; shortName: string }, importDefaultCards = false) {
    loading.value = true
    error.value = null
    try {
      const newDeck = await $fetch('/api/decks', {
        method: 'POST',
        body: {
          ...config,
          importDefaultCards
        }
      })
      await fetchDecks()
      return newDeck
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create deck'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateDeck(id: number, updates: Partial<DeckConfig>) {
    loading.value = true
    error.value = null
    try {
      await $fetch(`/api/decks/${id}`, {
        method: 'PUT',
        body: updates
      })
      if (currentDeck.value?.id === id) {
        await loadDeck(id)
      }
      await fetchDecks()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update deck'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteDeck(id: number) {
    loading.value = true
    error.value = null
    try {
      await $fetch(`/api/decks/${id}`, { method: 'DELETE' })
      if (currentDeck.value?.id === id) {
        currentDeck.value = null
      }
      await fetchDecks()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete deck'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function duplicateDeck(id: number, newName?: string) {
    loading.value = true
    error.value = null
    try {
      const newDeck = await $fetch(`/api/decks/${id}/duplicate`, {
        method: 'POST',
        body: { newName }
      })
      await fetchDecks()
      return newDeck
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to duplicate deck'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    currentDeck,
    decks,
    loading,
    error,
    fetchDecks,
    loadDeck,
    createDeck,
    updateDeck,
    deleteDeck,
    duplicateDeck
  }
}
