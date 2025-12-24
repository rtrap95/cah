import { useDB, schema } from '../../database'
import { ne, like, and, eq } from 'drizzle-orm'
import type { CardType } from '../../../types'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const query = getQuery(event)
  const excludeDeckId = query.excludeDeckId ? Number(query.excludeDeckId) : undefined
  const searchText = String(query.q || '')
  const cardType = query.type as CardType | undefined

  // Get texts of cards already in the target deck to exclude duplicates
  let existingTexts: Set<string> = new Set()
  if (excludeDeckId && !isNaN(excludeDeckId)) {
    const existingCards = await db.query.cards.findMany({
      where: eq(schema.cards.deckId, excludeDeckId),
      columns: { text: true },
    })
    existingTexts = new Set(existingCards.map(c => c.text.toLowerCase()))
  }

  const conditions = []

  if (excludeDeckId && !isNaN(excludeDeckId)) {
    conditions.push(ne(schema.cards.deckId, excludeDeckId))
  }

  if (searchText) {
    conditions.push(like(schema.cards.text, `%${searchText}%`))
  }

  if (cardType && (cardType === 'black' || cardType === 'white')) {
    conditions.push(eq(schema.cards.cardType, cardType))
  }

  const cards = await db.query.cards.findMany({
    where: conditions.length > 0 ? and(...conditions) : undefined,
    with: {
      deck: true,
    },
    orderBy: (cards, { asc }) => [asc(cards.deckId), asc(cards.id)],
  })

  // Filter out cards with text already present in target deck
  const filteredCards = cards.filter(card => !existingTexts.has(card.text.toLowerCase()))

  return filteredCards.map(card => ({
    id: card.id,
    deckId: card.deckId,
    deckName: card.deck?.name || 'Unknown',
    text: card.text,
    cardType: card.cardType,
    pick: card.pick,
    fontSize: card.fontSize,
    createdAt: card.createdAt,
  }))
})
