import { useDB, schema } from '../../database'
import { count, eq } from 'drizzle-orm'

export default defineEventHandler(async () => {
  const db = useDB()

  const decksWithCounts = await db.select({
    id: schema.decks.id,
    name: schema.decks.name,
    shortName: schema.decks.shortName,
    primaryColor: schema.decks.primaryColor,
    secondaryColor: schema.decks.secondaryColor,
    createdAt: schema.decks.createdAt,
    updatedAt: schema.decks.updatedAt
  }).from(schema.decks)

  const result = await Promise.all(decksWithCounts.map(async (deck) => {
    const cards = await db.select({ cardType: schema.cards.cardType })
      .from(schema.cards)
      .where(eq(schema.cards.deckId, deck.id))

    const blackCount = cards.filter(c => c.cardType === 'black').length
    const whiteCount = cards.filter(c => c.cardType === 'white').length

    return {
      ...deck,
      blackCount,
      whiteCount,
      totalCards: blackCount + whiteCount
    }
  }))

  return result
})
