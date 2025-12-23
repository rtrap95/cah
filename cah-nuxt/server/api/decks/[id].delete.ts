import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const id = Number(getRouterParam(event, 'id'))

  if (isNaN(id)) {
    throw createError({
      statusCode: 400,
      message: 'Invalid deck ID',
    })
  }

  const existing = await db.query.decks.findFirst({
    where: eq(schema.decks.id, id),
  })

  if (!existing) {
    throw createError({
      statusCode: 404,
      message: 'Deck not found',
    })
  }

  await db.delete(schema.decks).where(eq(schema.decks.id, id))

  return { success: true, message: 'Deck deleted successfully' }
})
