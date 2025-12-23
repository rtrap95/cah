import { useDB, schema } from '../../database'
import { eq, sql } from 'drizzle-orm'

interface BatchCreateBody {
  deckId: number
  blackCards?: string[]
  whiteCards?: string[]
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const body = await readBody<BatchCreateBody>(event)

  if (!body.deckId) {
    throw createError({
      statusCode: 400,
      message: 'deckId is required',
    })
  }

  const deck = await db.query.decks.findFirst({
    where: eq(schema.decks.id, body.deckId),
  })

  if (!deck) {
    throw createError({
      statusCode: 404,
      message: 'Deck not found',
    })
  }

  const cardsToInsert: { deckId: number; text: string; cardType: 'black' | 'white'; pick: number }[] = []

  if (body.blackCards) {
    for (const text of body.blackCards) {
      if (text.trim()) {
        const blankCount = (text.match(/_____/g) || []).length
        cardsToInsert.push({
          deckId: body.deckId,
          text: text.trim(),
          cardType: 'black',
          pick: Math.max(1, blankCount),
        })
      }
    }
  }

  if (body.whiteCards) {
    for (const text of body.whiteCards) {
      if (text.trim()) {
        cardsToInsert.push({
          deckId: body.deckId,
          text: text.trim(),
          cardType: 'white',
          pick: 1,
        })
      }
    }
  }

  if (cardsToInsert.length === 0) {
    throw createError({
      statusCode: 400,
      message: 'No valid cards to insert',
    })
  }

  const inserted = await db.insert(schema.cards).values(cardsToInsert).returning()

  await db.update(schema.decks)
    .set({ updatedAt: sql`CURRENT_TIMESTAMP` })
    .where(eq(schema.decks.id, body.deckId))

  return {
    inserted: inserted.length,
    blackCount: inserted.filter(c => c.cardType === 'black').length,
    whiteCount: inserted.filter(c => c.cardType === 'white').length,
  }
})
