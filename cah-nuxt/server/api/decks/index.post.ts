import { useDB, schema } from '../../database'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

interface CreateDeckBody {
  name: string
  shortName: string
  blackLogoPath?: string | null
  whiteLogoPath?: string | null
  primaryColor?: string
  secondaryColor?: string
  importDefaultCards?: boolean
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const body = await readBody<CreateDeckBody>(event)

  if (!body.name || !body.shortName) {
    throw createError({
      statusCode: 400,
      message: 'Name and shortName are required',
    })
  }

  const [deck] = await db.insert(schema.decks).values({
    name: body.name,
    shortName: body.shortName.toUpperCase().slice(0, 5),
    blackLogoPath: body.blackLogoPath,
    whiteLogoPath: body.whiteLogoPath,
    primaryColor: body.primaryColor || '#000000',
    secondaryColor: body.secondaryColor || '#FFFFFF',
  }).returning()

  if (body.importDefaultCards) {
    const cardsPath = join(process.cwd(), 'data', 'cards.json')
    if (existsSync(cardsPath)) {
      const cardsData = JSON.parse(readFileSync(cardsPath, 'utf-8'))
      const cardsToInsert = cardsData.map((card: { text: string; card_type: string; pick: number }) => ({
        deckId: deck.id,
        text: card.text,
        cardType: card.card_type as 'black' | 'white',
        pick: card.pick || 1,
      }))

      if (cardsToInsert.length > 0) {
        await db.insert(schema.cards).values(cardsToInsert)
      }
    }
  }

  return deck
})
