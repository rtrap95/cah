import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const body = await readBody(event)
  const { cardId, targetDeckId } = body

  if (!cardId || !targetDeckId) {
    throw createError({
      statusCode: 400,
      message: 'cardId and targetDeckId are required',
    })
  }

  // Get the original card
  const originalCard = await db.query.cards.findFirst({
    where: eq(schema.cards.id, cardId),
  })

  if (!originalCard) {
    throw createError({
      statusCode: 404,
      message: 'Card not found',
    })
  }

  // Check if target deck exists
  const targetDeck = await db.query.decks.findFirst({
    where: eq(schema.decks.id, targetDeckId),
  })

  if (!targetDeck) {
    throw createError({
      statusCode: 404,
      message: 'Target deck not found',
    })
  }

  // Copy the card to the target deck
  const [newCard] = await db.insert(schema.cards).values({
    deckId: targetDeckId,
    text: originalCard.text,
    cardType: originalCard.cardType,
    pick: originalCard.pick,
    fontSize: originalCard.fontSize,
  }).returning()

  return {
    id: newCard.id,
    deckId: newCard.deckId,
    text: newCard.text,
    cardType: newCard.cardType,
    pick: newCard.pick,
    fontSize: newCard.fontSize,
    createdAt: newCard.createdAt,
  }
})
