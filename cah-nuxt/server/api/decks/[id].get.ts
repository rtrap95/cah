import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'
import type { Deck, Card } from '../../../types'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const id = Number(getRouterParam(event, 'id'))

  if (isNaN(id)) {
    throw createError({
      statusCode: 400,
      message: 'Invalid deck ID',
    })
  }

  const deckData = await db.query.decks.findFirst({
    where: eq(schema.decks.id, id),
  })

  if (!deckData) {
    throw createError({
      statusCode: 404,
      message: 'Deck not found',
    })
  }

  const cardsData = await db.query.cards.findMany({
    where: eq(schema.cards.deckId, id),
    orderBy: (cards, { asc }) => [asc(cards.id)],
  })

  const blackCards: Card[] = []
  const whiteCards: Card[] = []

  for (const card of cardsData) {
    const cardObj: Card = {
      id: card.id,
      deckId: card.deckId,
      text: card.text,
      cardType: card.cardType as 'black' | 'white',
      pick: card.pick,
      fontSize: card.fontSize,
      createdAt: new Date(card.createdAt),
    }

    if (card.cardType === 'black') {
      blackCards.push(cardObj)
    } else {
      whiteCards.push(cardObj)
    }
  }

  const deck: Deck = {
    id: deckData.id,
    config: {
      name: deckData.name,
      shortName: deckData.shortName,
      blackLogoPath: deckData.blackLogoPath,
      whiteLogoPath: deckData.whiteLogoPath,
      blackBackLogoPath: deckData.blackBackLogoPath,
      whiteBackLogoPath: deckData.whiteBackLogoPath,
      primaryColor: deckData.primaryColor,
      secondaryColor: deckData.secondaryColor,
    },
    blackCards,
    whiteCards,
    createdAt: new Date(deckData.createdAt),
    updatedAt: new Date(deckData.updatedAt),
  }

  return deck
})
