import { useDB, schema } from '../../database'
import { eq, sql } from 'drizzle-orm'
import type { CardType } from '../../../types'

interface CreateCardBody {
  deckId: number
  text: string
  cardType: CardType
  pick?: number
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const body = await readBody<CreateCardBody>(event)

  if (!body.deckId || !body.text || !body.cardType) {
    throw createError({
      statusCode: 400,
      message: 'deckId, text, and cardType are required',
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

  const [card] = await db.insert(schema.cards).values({
    deckId: body.deckId,
    text: body.text,
    cardType: body.cardType,
    pick: body.cardType === 'black' ? (body.pick || 1) : 1,
  }).returning()

  await db.update(schema.decks)
    .set({ updatedAt: sql`CURRENT_TIMESTAMP` })
    .where(eq(schema.decks.id, body.deckId))

  return card
})
