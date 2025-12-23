import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'

interface SetDefaultDeckBody {
  deckId: number | null
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const body = await readBody<SetDefaultDeckBody>(event)

  if (body.deckId !== null) {
    // Verify deck exists
    const deck = await db.query.decks.findFirst({
      where: eq(schema.decks.id, body.deckId)
    })

    if (!deck) {
      throw createError({
        statusCode: 404,
        message: 'Deck not found'
      })
    }
  }

  // Upsert the setting
  const existing = await db.query.settings.findFirst({
    where: eq(schema.settings.key, 'default_deck_id')
  })

  if (existing) {
    await db.update(schema.settings)
      .set({ value: body.deckId?.toString() || null })
      .where(eq(schema.settings.key, 'default_deck_id'))
  } else {
    await db.insert(schema.settings).values({
      key: 'default_deck_id',
      value: body.deckId?.toString() || null
    })
  }

  return { success: true, defaultDeckId: body.deckId }
})
