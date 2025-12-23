import PDFDocument from 'pdfkit'
import type { Card } from '~/types'
import { existsSync } from 'fs'

// Card dimensions in points (1mm = 2.83465 points)
const MM_TO_PT = 2.83465
const CARD_WIDTH = 58 * MM_TO_PT  // 58mm
const CARD_HEIGHT = 88 * MM_TO_PT // 88mm
const CORNER_RADIUS = 3 * MM_TO_PT // 3mm
const MARGIN = 10 * MM_TO_PT // 10mm margin
const GAP = 5 * MM_TO_PT // 5mm gap between cards

const CARDS_PER_ROW = 3
const CARDS_PER_COL = 3
const CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL

interface LogoPaths {
  blackFront: string | null
  whiteFront: string | null
  blackBack: string | null
  whiteBack: string | null
}

interface ExportOptions {
  deckName: string
  shortName: string
  cardsType: 'all' | 'black' | 'white'
  includeBacks: boolean
  logos?: LogoPaths
}

function wrapText(text: string, maxChars = 22): string[] {
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''

  for (const word of words) {
    if (currentLine.length + word.length + 1 <= maxChars) {
      currentLine += (currentLine ? ' ' : '') + word
    } else {
      if (currentLine) lines.push(currentLine)
      currentLine = word
    }
  }

  if (currentLine) lines.push(currentLine)
  return lines
}

function drawRoundedRect(doc: PDFKit.PDFDocument, x: number, y: number, width: number, height: number, radius: number) {
  doc.moveTo(x + radius, y)
  doc.lineTo(x + width - radius, y)
  doc.quadraticCurveTo(x + width, y, x + width, y + radius)
  doc.lineTo(x + width, y + height - radius)
  doc.quadraticCurveTo(x + width, y + height, x + width - radius, y + height)
  doc.lineTo(x + radius, y + height)
  doc.quadraticCurveTo(x, y + height, x, y + height - radius)
  doc.lineTo(x, y + radius)
  doc.quadraticCurveTo(x, y, x + radius, y)
  doc.closePath()
}

function drawCard(
  doc: PDFKit.PDFDocument,
  card: Card,
  x: number,
  y: number,
  deckName: string,
  shortName: string,
  logoPath: string | null
) {
  const isBlack = card.cardType === 'black'

  // Background
  drawRoundedRect(doc, x, y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS)
  doc.fill(isBlack ? '#1a1a1a' : '#ffffff')

  // Border for white cards
  if (!isBlack) {
    drawRoundedRect(doc, x, y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS)
    doc.stroke('#cccccc')
  }

  const textColor = isBlack ? '#ffffff' : '#000000'
  doc.fillColor(textColor)

  // Card text
  const lines = wrapText(card.text, 22)
  const fontSize = lines.length > 4 ? 9 : 11
  const lineHeight = fontSize * 1.3
  const textStartY = y + 20

  doc.font('Helvetica-Bold').fontSize(fontSize)

  lines.forEach((line, i) => {
    doc.text(line, x + 10, textStartY + (i * lineHeight), {
      width: CARD_WIDTH - 20,
      align: 'left'
    })
  })

  // Logo at bottom left (if available)
  if (logoPath && existsSync(logoPath)) {
    try {
      const logoSize = 20
      doc.image(logoPath, x + 10, y + CARD_HEIGHT - logoSize - 10, {
        width: logoSize,
        height: logoSize,
        fit: [logoSize, logoSize]
      })
    } catch {
      // Logo loading failed, skip it
    }
  }

  // Deck name at bottom (next to logo if present)
  const textX = logoPath && existsSync(logoPath) ? x + 35 : x + 10
  doc.font('Helvetica-Bold').fontSize(7)
  doc.text(deckName, textX, y + CARD_HEIGHT - 25, {
    width: CARD_WIDTH - textX + x - 10,
    align: 'left'
  })

  // Short name at bottom right
  doc.font('Helvetica').fontSize(6)
  doc.text(shortName, x + 10, y + CARD_HEIGHT - 15, {
    width: CARD_WIDTH - 20,
    align: 'right'
  })

  // Pick indicator for black cards
  if (isBlack && card.pick > 1) {
    doc.font('Helvetica-Bold').fontSize(8)
    doc.text(`PICK ${card.pick}`, textX, y + CARD_HEIGHT - 15, {
      width: CARD_WIDTH - 20,
      align: 'left'
    })
  }
}

function drawCardBack(
  doc: PDFKit.PDFDocument,
  isBlack: boolean,
  x: number,
  y: number,
  shortName: string,
  logoPath: string | null
) {
  // Background
  drawRoundedRect(doc, x, y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS)
  doc.fill(isBlack ? '#1a1a1a' : '#ffffff')

  // Border for white cards
  if (!isBlack) {
    drawRoundedRect(doc, x, y, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS)
    doc.stroke('#cccccc')
  }

  // Logo in center (if available)
  if (logoPath && existsSync(logoPath)) {
    try {
      const logoSize = 60
      doc.image(logoPath, x + (CARD_WIDTH - logoSize) / 2, y + (CARD_HEIGHT - logoSize) / 2 - 10, {
        width: logoSize,
        height: logoSize,
        fit: [logoSize, logoSize]
      })
    } catch {
      // Logo loading failed, fall back to text
      const textColor = isBlack ? '#ffffff' : '#000000'
      doc.fillColor(textColor)
      doc.font('Helvetica-Bold').fontSize(16)
      doc.text(shortName, x, y + (CARD_HEIGHT / 2) - 10, {
        width: CARD_WIDTH,
        align: 'center'
      })
    }
  } else {
    // No logo, just show short name
    const textColor = isBlack ? '#ffffff' : '#000000'
    doc.fillColor(textColor)
    doc.font('Helvetica-Bold').fontSize(16)
    doc.text(shortName, x, y + (CARD_HEIGHT / 2) - 10, {
      width: CARD_WIDTH,
      align: 'center'
    })
  }

  // Short name below logo
  if (logoPath && existsSync(logoPath)) {
    const textColor = isBlack ? '#ffffff' : '#000000'
    doc.fillColor(textColor)
    doc.font('Helvetica-Bold').fontSize(10)
    doc.text(shortName, x, y + (CARD_HEIGHT / 2) + 35, {
      width: CARD_WIDTH,
      align: 'center'
    })
  }
}

function drawFrontPage(
  doc: PDFKit.PDFDocument,
  cards: Card[],
  options: ExportOptions
) {
  cards.forEach((card, index) => {
    const row = Math.floor(index / CARDS_PER_ROW)
    const col = index % CARDS_PER_ROW
    const x = MARGIN + (col * (CARD_WIDTH + GAP))
    const y = MARGIN + (row * (CARD_HEIGHT + GAP))

    const logoPath = card.cardType === 'black'
      ? options.logos?.blackFront || null
      : options.logos?.whiteFront || null

    drawCard(doc, card, x, y, options.deckName, options.shortName, logoPath)
  })
}

function drawBackPage(
  doc: PDFKit.PDFDocument,
  cards: Card[],
  options: ExportOptions
) {
  // Mirror horizontally for proper back alignment when printed double-sided
  cards.forEach((card, index) => {
    const row = Math.floor(index / CARDS_PER_ROW)
    const col = (CARDS_PER_ROW - 1) - (index % CARDS_PER_ROW) // Mirror column
    const x = MARGIN + (col * (CARD_WIDTH + GAP))
    const y = MARGIN + (row * (CARD_HEIGHT + GAP))

    const logoPath = card.cardType === 'black'
      ? options.logos?.blackBack || null
      : options.logos?.whiteBack || null

    drawCardBack(doc, card.cardType === 'black', x, y, options.shortName, logoPath)
  })
}

export async function generatePDF(
  cards: Card[],
  options: ExportOptions
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({
      size: 'A4',
      margin: MARGIN
    })

    const chunks: Buffer[] = []

    doc.on('data', (chunk: Buffer) => chunks.push(chunk))
    doc.on('end', () => resolve(Buffer.concat(chunks)))
    doc.on('error', reject)

    // Filter cards by type
    let filteredCards = cards
    if (options.cardsType === 'black') {
      filteredCards = cards.filter(c => c.cardType === 'black')
    } else if (options.cardsType === 'white') {
      filteredCards = cards.filter(c => c.cardType === 'white')
    }

    if (filteredCards.length === 0) {
      doc.text('No cards to export')
      doc.end()
      return
    }

    // Calculate number of pages needed
    const totalPages = Math.ceil(filteredCards.length / CARDS_PER_PAGE)

    for (let pageIndex = 0; pageIndex < totalPages; pageIndex++) {
      const pageStart = pageIndex * CARDS_PER_PAGE
      const pageCards = filteredCards.slice(pageStart, pageStart + CARDS_PER_PAGE)

      // Draw front page
      if (pageIndex > 0 || (pageIndex === 0 && options.includeBacks)) {
        if (pageIndex > 0) doc.addPage()
      }

      if (pageIndex === 0) {
        // First page, just draw
        drawFrontPage(doc, pageCards, options)
      } else {
        drawFrontPage(doc, pageCards, options)
      }

      // Draw back page immediately after front (for double-sided printing)
      if (options.includeBacks) {
        doc.addPage()
        drawBackPage(doc, pageCards, options)
      }
    }

    doc.end()
  })
}
