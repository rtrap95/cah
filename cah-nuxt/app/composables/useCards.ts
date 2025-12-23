import type { Card, CardType } from '~/types'

export function useCards() {
  const { currentDeck, loadDeck } = useDeck()

  const allCards = computed(() => {
    if (!currentDeck.value) return []
    return [...currentDeck.value.blackCards, ...currentDeck.value.whiteCards]
  })

  const blackCards = computed(() => currentDeck.value?.blackCards || [])
  const whiteCards = computed(() => currentDeck.value?.whiteCards || [])

  async function addCard(deckId: number, text: string, cardType: CardType, pick = 1) {
    await $fetch('/api/cards', {
      method: 'POST',
      body: { deckId, text, cardType, pick }
    })
    await loadDeck(deckId)
  }

  async function batchAddCards(deckId: number, blackCards: string[], whiteCards: string[]) {
    const result = await $fetch('/api/cards/batch', {
      method: 'POST',
      body: { deckId, blackCards, whiteCards }
    })
    await loadDeck(deckId)
    return result
  }

  async function updateCard(cardId: number, text: string, pick?: number) {
    await $fetch(`/api/cards/${cardId}`, {
      method: 'PUT',
      body: { text, pick }
    })
    if (currentDeck.value?.id) {
      await loadDeck(currentDeck.value.id)
    }
  }

  async function deleteCard(cardId: number) {
    await $fetch(`/api/cards/${cardId}`, { method: 'DELETE' })
    if (currentDeck.value?.id) {
      await loadDeck(currentDeck.value.id)
    }
  }

  async function searchCards(deckId: number, query: string, type?: CardType): Promise<Card[]> {
    const params = new URLSearchParams({ deckId: String(deckId) })
    if (query) params.set('q', query)
    if (type) params.set('type', type)

    return await $fetch(`/api/cards/search?${params}`)
  }

  return {
    allCards,
    blackCards,
    whiteCards,
    addCard,
    batchAddCards,
    updateCard,
    deleteCard,
    searchCards
  }
}
