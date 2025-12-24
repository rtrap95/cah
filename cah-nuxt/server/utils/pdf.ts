import PDFDocument from 'pdfkit'
import type { Card } from '~/types'
import { existsSync } from 'fs'
import { join } from 'path'

// Font paths for emoji support
const FONTS_DIR = join(process.cwd(), 'server/fonts')
const FONT_REGULAR = join(FONTS_DIR, 'NotoSans-Regular.ttf')
const FONT_BOLD = join(FONTS_DIR, 'NotoSans-Bold.ttf')

// Check if custom fonts are available
const hasCustomFonts = existsSync(FONT_BOLD) && existsSync(FONT_REGULAR)
const BOLD_FONT = hasCustomFonts ? 'NotoSans-Bold' : 'Helvetica-Bold'
const REGULAR_FONT = hasCustomFonts ? 'NotoSans-Regular' : 'Helvetica'

// Card dimensions in points (1mm = 2.83465 points)
const MM_TO_PT = 2.83465
const CARD_WIDTH = 58 * MM_TO_PT // 58mm
const CARD_HEIGHT = 88 * MM_TO_PT // 88mm
const CORNER_RADIUS = 3 * MM_TO_PT // 3mm
const GAP = 5 * MM_TO_PT // 5mm gap between cards

const CARDS_PER_ROW = 3
const CARDS_PER_COL = 3
const CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COL

// A4 dimensions: 210mm x 297mm
const A4_WIDTH = 210 * MM_TO_PT
const A4_HEIGHT = 297 * MM_TO_PT

// Calculate centered margins
const TOTAL_CARDS_WIDTH = (CARDS_PER_ROW * CARD_WIDTH) + ((CARDS_PER_ROW - 1) * GAP)
const TOTAL_CARDS_HEIGHT = (CARDS_PER_COL * CARD_HEIGHT) + ((CARDS_PER_COL - 1) * GAP)
const MARGIN_X = (A4_WIDTH - TOTAL_CARDS_WIDTH) / 2
const MARGIN_Y = (A4_HEIGHT - TOTAL_CARDS_HEIGHT) / 2

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
  showShortName?: boolean
  logoSize?: number
  backLogoSize?: number
  cardPadding?: number
  showCutLines?: boolean
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

const CUT_LINE_LENGTH = 8 * MM_TO_PT // 8mm cut marks
const CUT_LINE_OFFSET = 2 * MM_TO_PT // 2mm offset from card edge

function drawCutLines(doc: PDFKit.PDFDocument, x: number, y: number, width: number, height: number) {
  doc.strokeColor('#888888')
  doc.lineWidth(0.5)

  // Top-left corner
  doc.moveTo(x - CUT_LINE_OFFSET - CUT_LINE_LENGTH, y)
  doc.lineTo(x - CUT_LINE_OFFSET, y)
  doc.stroke()
  doc.moveTo(x, y - CUT_LINE_OFFSET - CUT_LINE_LENGTH)
  doc.lineTo(x, y - CUT_LINE_OFFSET)
  doc.stroke()

  // Top-right corner
  doc.moveTo(x + width + CUT_LINE_OFFSET, y)
  doc.lineTo(x + width + CUT_LINE_OFFSET + CUT_LINE_LENGTH, y)
  doc.stroke()
  doc.moveTo(x + width, y - CUT_LINE_OFFSET - CUT_LINE_LENGTH)
  doc.lineTo(x + width, y - CUT_LINE_OFFSET)
  doc.stroke()

  // Bottom-left corner
  doc.moveTo(x - CUT_LINE_OFFSET - CUT_LINE_LENGTH, y + height)
  doc.lineTo(x - CUT_LINE_OFFSET, y + height)
  doc.stroke()
  doc.moveTo(x, y + height + CUT_LINE_OFFSET)
  doc.lineTo(x, y + height + CUT_LINE_OFFSET + CUT_LINE_LENGTH)
  doc.stroke()

  // Bottom-right corner
  doc.moveTo(x + width + CUT_LINE_OFFSET, y + height)
  doc.lineTo(x + width + CUT_LINE_OFFSET + CUT_LINE_LENGTH, y + height)
  doc.stroke()
  doc.moveTo(x + width, y + height + CUT_LINE_OFFSET)
  doc.lineTo(x + width, y + height + CUT_LINE_OFFSET + CUT_LINE_LENGTH)
  doc.stroke()
}

function drawCard(
  doc: PDFKit.PDFDocument,
  card: Card,
  x: number,
  y: number,
  deckName: string,
  shortName: string,
  logoPath: string | null,
  showShortName: boolean = true,
  logoSize: number = 20,
  padding: number = 10
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

  // Deck name at top (centered)
  doc.font(BOLD_FONT).fontSize(8)
  doc.text(deckName, x + padding, y + 12, {
    width: CARD_WIDTH - (padding * 2),
    align: 'center'
  })

  // Card text (starts after deck name with more spacing)
  const textStartY = y + 38
  const bottomReserved = 35 // Space for logo, shortName, pick indicator
  const availableHeight = CARD_HEIGHT - 38 - bottomReserved

  // Calculate font size based on text length
  let fontSize = 12
  let lines = wrapText(card.text, 20)
  let lineHeight = fontSize * 1.3
  let maxLines = Math.floor(availableHeight / lineHeight)

  // If too many lines, reduce font size
  if (lines.length > maxLines) {
    fontSize = 10
    lines = wrapText(card.text, 24)
    lineHeight = fontSize * 1.3
    maxLines = Math.floor(availableHeight / lineHeight)
  }

  // If still too many lines, reduce further
  if (lines.length > maxLines) {
    fontSize = 8
    lines = wrapText(card.text, 28)
    lineHeight = fontSize * 1.3
    maxLines = Math.floor(availableHeight / lineHeight)
  }

  // Limit lines to available space
  if (lines.length > maxLines) {
    lines = lines.slice(0, maxLines)
    // Add ellipsis to last line if truncated
    if (lines[maxLines - 1]) {
      lines[maxLines - 1] = lines[maxLines - 1].slice(0, -3) + '...'
    }
  }

  doc.font(BOLD_FONT).fontSize(fontSize)

  lines.forEach((line, i) => {
    doc.text(line, x + padding, textStartY + (i * lineHeight), {
      width: CARD_WIDTH - (padding * 2),
      align: 'left'
    })
  })

  // Logo at bottom right (if available)
  if (logoPath && existsSync(logoPath)) {
    try {
      doc.image(logoPath, x + CARD_WIDTH - logoSize - padding, y + CARD_HEIGHT - logoSize - padding, {
        width: logoSize,
        height: logoSize,
        fit: [logoSize, logoSize]
      })
    } catch {
      // Logo loading failed, skip it
    }
  }

  // Short name at bottom left (optional)
  if (showShortName) {
    doc.font(REGULAR_FONT).fontSize(7)
    doc.text(shortName, x + padding, y + CARD_HEIGHT - 16, {
      width: CARD_WIDTH - (padding * 2),
      align: 'left'
    })
  }

  // Pick indicator for black cards
  if (isBlack && card.pick > 1) {
    doc.font(BOLD_FONT).fontSize(9)
    doc.text(`PICK ${card.pick}`, x + padding, y + CARD_HEIGHT - 27, {
      width: CARD_WIDTH - (padding * 2),
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
  logoPath: string | null,
  showShortName: boolean = true,
  backLogoSize: number = 60
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
      // If showing short name, offset logo up to make room for text below
      const logoOffsetY = showShortName ? -15 : 0
      doc.image(logoPath, x + (CARD_WIDTH - backLogoSize) / 2, y + (CARD_HEIGHT - backLogoSize) / 2 + logoOffsetY, {
        width: backLogoSize,
        height: backLogoSize,
        fit: [backLogoSize, backLogoSize]
      })

      // Short name below logo (optional)
      if (showShortName) {
        const textColor = isBlack ? '#ffffff' : '#000000'
        doc.fillColor(textColor)
        doc.font(BOLD_FONT).fontSize(10)
        doc.text(shortName, x, y + (CARD_HEIGHT / 2) + backLogoSize / 2 + 10, {
          width: CARD_WIDTH,
          align: 'center'
        })
      }
    } catch {
      // Logo loading failed, fall back to text if showing short name
      if (showShortName) {
        const textColor = isBlack ? '#ffffff' : '#000000'
        doc.fillColor(textColor)
        doc.font(BOLD_FONT).fontSize(16)
        doc.text(shortName, x, y + (CARD_HEIGHT / 2) - 10, {
          width: CARD_WIDTH,
          align: 'center'
        })
      }
    }
  } else if (showShortName) {
    // No logo, show short name if enabled
    const textColor = isBlack ? '#ffffff' : '#000000'
    doc.fillColor(textColor)
    doc.font(BOLD_FONT).fontSize(16)
    doc.text(shortName, x, y + (CARD_HEIGHT / 2) - 10, {
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
    const x = MARGIN_X + (col * (CARD_WIDTH + GAP))
    const y = MARGIN_Y + (row * (CARD_HEIGHT + GAP))

    const logoPath = card.cardType === 'black'
      ? options.logos?.blackFront || null
      : options.logos?.whiteFront || null

    drawCard(
      doc,
      card,
      x,
      y,
      options.deckName,
      options.shortName,
      logoPath,
      options.showShortName !== false,
      options.logoSize || 20,
      options.cardPadding || 10
    )

    // Draw cut lines if enabled
    if (options.showCutLines) {
      drawCutLines(doc, x, y, CARD_WIDTH, CARD_HEIGHT)
    }
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
    const x = MARGIN_X + (col * (CARD_WIDTH + GAP))
    const y = MARGIN_Y + (row * (CARD_HEIGHT + GAP))

    const logoPath = card.cardType === 'black'
      ? options.logos?.blackBack || null
      : options.logos?.whiteBack || null

    drawCardBack(doc, card.cardType === 'black', x, y, options.shortName, logoPath, options.showShortName !== false, options.backLogoSize || 60)

    // Draw cut lines if enabled
    if (options.showCutLines) {
      drawCutLines(doc, x, y, CARD_WIDTH, CARD_HEIGHT)
    }
  })
}

export async function generatePDF(
  cards: Card[],
  options: ExportOptions
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({
      size: 'A4',
      margin: 0
    })

    // Register custom fonts with emoji support
    if (existsSync(FONT_BOLD)) {
      doc.registerFont('NotoSans-Bold', FONT_BOLD)
    }
    if (existsSync(FONT_REGULAR)) {
      doc.registerFont('NotoSans-Regular', FONT_REGULAR)
    }

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
