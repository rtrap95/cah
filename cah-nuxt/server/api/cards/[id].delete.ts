import { useDB, schema } from '../../database'
import { eq, sql } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const id = Number(getRouterParam(event, 'id'))

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

  await db.delete(schema.cards).where(eq(schema.cards.id, id))

  await db.update(schema.decks)
    .set({ updatedAt: sql`CURRENT_TIMESTAMP` })
    .where(eq(schema.decks.id, existing.deckId))

  return { success: true, message: 'Card deleted successfully' }
})
