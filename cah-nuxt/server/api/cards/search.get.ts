import { useDB, schema } from '../../database'
import { eq, like, and } from 'drizzle-orm'
import type { CardType } from '../../../types'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const query = getQuery(event)
  const deckId = Number(query.deckId)
  const searchText = String(query.q || '')
  const cardType = query.type as CardType | undefined

  if (isNaN(deckId)) {
    throw createError({
      statusCode: 400,
      message: 'Valid deckId is required',
    })
  }

  const conditions = [eq(schema.cards.deckId, deckId)]

  if (searchText) {
    conditions.push(like(schema.cards.text, `%${searchText}%`))
  }

  if (cardType && (cardType === 'black' || cardType === 'white')) {
    conditions.push(eq(schema.cards.cardType, cardType))
  }

  const cards = await db.query.cards.findMany({
    where: and(...conditions),
    orderBy: (cards, { asc }) => [asc(cards.id)],
  })

  return cards.map(card => ({
    id: card.id,
    deckId: card.deckId,
    text: card.text,
    cardType: card.cardType,
    pick: card.pick,
    createdAt: card.createdAt,
  }))
})
