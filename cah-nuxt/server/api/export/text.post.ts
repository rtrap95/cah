import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'

interface ExportBody {
  deckId: number
  cardsType?: 'all' | 'black' | 'white'
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const body = await readBody<ExportBody>(event)

  if (!body.deckId) {
    throw createError({
      statusCode: 400,
      message: 'deckId is required'
    })
  }

  const deckData = await db.query.decks.findFirst({
    where: eq(schema.decks.id, body.deckId)
  })

  if (!deckData) {
    throw createError({
      statusCode: 404,
      message: 'Deck not found'
    })
  }

  const cardsData = await db.query.cards.findMany({
    where: eq(schema.cards.deckId, body.deckId)
  })

  // Filter cards by type
  let filteredCards = cardsData
  if (body.cardsType === 'black') {
    filteredCards = cardsData.filter(c => c.cardType === 'black')
  } else if (body.cardsType === 'white') {
    filteredCards = cardsData.filter(c => c.cardType === 'white')
  }

  const blackCards = filteredCards.filter(c => c.cardType === 'black')
  const whiteCards = filteredCards.filter(c => c.cardType === 'white')

  // Build text content
  let content = `# ${deckData.name}\n`
  content += `Abbreviazione: ${deckData.shortName}\n`
  content += `Totale carte: ${filteredCards.length}\n`
  content += `\n`

  if (blackCards.length > 0) {
    content += `## Carte Nere (${blackCards.length})\n`
    content += `Le carte nere sono le domande/frasi da completare. Il simbolo "_" indica dove inserire una carta bianca.\n\n`
    blackCards.forEach((card, index) => {
      const pickInfo = card.pick > 1 ? ` [PICK ${card.pick}]` : ''
      content += `${index + 1}. ${card.text}${pickInfo}\n`
    })
    content += `\n`
  }

  if (whiteCards.length > 0) {
    content += `## Carte Bianche (${whiteCards.length})\n`
    content += `Le carte bianche sono le risposte da inserire nelle carte nere.\n\n`
    whiteCards.forEach((card, index) => {
      content += `${index + 1}. ${card.text}\n`
    })
  }

  setHeader(event, 'Content-Type', 'text/plain; charset=utf-8')
  setHeader(event, 'Content-Disposition', `attachment; filename="${deckData.shortName}.txt"`)

  return content
})
