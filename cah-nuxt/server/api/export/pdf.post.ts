import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'
import { generatePDF } from '../../utils/pdf'
import type { Card } from '../../../types'
import { join } from 'path'

interface ExportBody {
  deckId: number
  cardsType?: 'all' | 'black' | 'white'
  includeBacks?: boolean
  deckName?: string
  shortName?: string
  showShortName?: boolean
  logoSize?: number
  backLogoSize?: number
  cardPadding?: number
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

  const cards: Card[] = cardsData.map(c => ({
    id: c.id,
    deckId: c.deckId,
    text: c.text,
    cardType: c.cardType as 'black' | 'white',
    pick: c.pick
  }))

  // Convert relative paths to absolute paths for PDFKit
  const publicDir = join(process.cwd(), 'public')
  const toAbsolutePath = (relativePath: string | null) => {
    if (!relativePath) return null
    return join(publicDir, relativePath)
  }

  const pdfBuffer = await generatePDF(cards, {
    deckName: body.deckName || deckData.name,
    shortName: body.shortName || deckData.shortName,
    cardsType: body.cardsType || 'all',
    includeBacks: body.includeBacks || false,
    showShortName: body.showShortName !== false,
    logoSize: body.logoSize || 20,
    backLogoSize: body.backLogoSize || 60,
    cardPadding: body.cardPadding || 10,
    logos: {
      blackFront: toAbsolutePath(deckData.blackLogoPath),
      whiteFront: toAbsolutePath(deckData.whiteLogoPath),
      blackBack: toAbsolutePath(deckData.blackBackLogoPath),
      whiteBack: toAbsolutePath(deckData.whiteBackLogoPath)
    }
  })

  setHeader(event, 'Content-Type', 'application/pdf')
  setHeader(event, 'Content-Disposition', `attachment; filename="${body.shortName || deckData.shortName}.pdf"`)

  return pdfBuffer
})
