import { useDB, schema } from '../../database'
import { eq, sql } from 'drizzle-orm'

interface UpdateCardBody {
  text?: string
  pick?: number
  fontSize?: number
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody<UpdateCardBody>(event)

  if (isNaN(id)) {
    throw createError({
      statusCode: 400,
      message: 'Invalid card ID',
    })
  }

  const existing = await db.query.cards.findFirst({
    where: eq(schema.cards.id, id),
  })

  if (!existing) {
    throw createError({
      statusCode: 404,
      message: 'Card not found',
    })
  }

  const [updated] = await db.update(schema.cards)
    .set({
      text: body.text ?? existing.text,
      pick: existing.cardType === 'black' ? (body.pick ?? existing.pick) : 1,
      fontSize: body.fontSize ?? existing.fontSize,
    })
    .where(eq(schema.cards.id, id))
    .returning()

  await db.update(schema.decks)
    .set({ updatedAt: sql`CURRENT_TIMESTAMP` })
    .where(eq(schema.decks.id, existing.deckId))

  return updated
})
