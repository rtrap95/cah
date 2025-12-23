import { useDB, schema } from '../../../database'
import { eq } from 'drizzle-orm'

interface DuplicateBody {
  newName?: string
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody<DuplicateBody>(event)

  if (isNaN(id)) {
    throw createError({
      statusCode: 400,
      message: 'Invalid deck ID'
    })
  }

  const existing = await db.query.decks.findFirst({
    where: eq(schema.decks.id, id)
  })

  if (!existing) {
    throw createError({
      statusCode: 404,
      message: 'Deck not found'
    })
  }

  const [newDeck] = await db.insert(schema.decks).values({
    name: body.newName || `${existing.name} (Copy)`,
    shortName: existing.shortName,
    blackLogoPath: existing.blackLogoPath,
    whiteLogoPath: existing.whiteLogoPath,
    blackBackLogoPath: existing.blackBackLogoPath,
    whiteBackLogoPath: existing.whiteBackLogoPath,
    primaryColor: existing.primaryColor,
    secondaryColor: existing.secondaryColor
  }).returning()

  const existingCards = await db.query.cards.findMany({
    where: eq(schema.cards.deckId, id)
  })

  if (existingCards.length > 0) {
    const cardsToInsert = existingCards.map(card => ({
      deckId: newDeck.id,
      text: card.text,
      cardType: card.cardType as 'black' | 'white',
      pick: card.pick
    }))

    await db.insert(schema.cards).values(cardsToInsert)
  }

  return newDeck
})
