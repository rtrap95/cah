import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'
import type { Card, RandomCombo } from '../../../types'

export default defineEventHandler(async (event) => {
  const db = useDB()
  const query = getQuery(event)
  const deckId = Number(query.deckId)

  if (isNaN(deckId)) {
    throw createError({
      statusCode: 400,
      message: 'Valid deckId is required'
    })
  }

  const allCards = await db.query.cards.findMany({
    where: eq(schema.cards.deckId, deckId)
  })

  const blackCards = allCards.filter(c => c.cardType === 'black')
  const whiteCards = allCards.filter(c => c.cardType === 'white')

  if (blackCards.length === 0) {
    throw createError({
      statusCode: 400,
      message: 'No black cards in deck'
    })
  }

  if (whiteCards.length === 0) {
    throw createError({
      statusCode: 400,
      message: 'No white cards in deck'
    })
  }

  // Select random black card
  const randomBlackIndex = Math.floor(Math.random() * blackCards.length)
  const selectedBlack = blackCards[randomBlackIndex]

  // Count blanks in the black card text
  const blanksInText = (selectedBlack.text.match(/_____/g) || []).length
  // Use the higher of: explicit pick value or number of blanks found
  const pickCount = Math.max(selectedBlack.pick, blanksInText, 1)

  // Select random white cards (ensure we don't pick more than available)
  const numWhiteCards = Math.min(pickCount, whiteCards.length)
  const shuffledWhites = [...whiteCards].sort(() => Math.random() - 0.5)
  const selectedWhites = shuffledWhites.slice(0, numWhiteCards)

  // Build combined text - replace each blank with a white card
  let combinedText = selectedBlack.text
  for (let i = 0; i < selectedWhites.length; i++) {
    const whiteText = selectedWhites[i].text
    // Remove trailing period from white card if present, for cleaner insertion
    const cleanWhiteText = whiteText.replace(/\.$/, '')
    combinedText = combinedText.replace('_____', `**${cleanWhiteText}**`)
  }

  // If there are still blanks left (not enough white cards), leave them as-is
  // If no blanks in original text, append white cards at the end
  if (blanksInText === 0 && selectedWhites.length > 0) {
    combinedText = combinedText + ' ' + selectedWhites.map(w => `**${w.text}**`).join(', ')
  }

  const result: RandomCombo = {
    blackCard: {
      id: selectedBlack.id,
      deckId: selectedBlack.deckId,
      text: selectedBlack.text,
      cardType: 'black',
      pick: selectedBlack.pick
    },
    whiteCards: selectedWhites.map(w => ({
      id: w.id,
      deckId: w.deckId,
      text: w.text,
      cardType: 'white' as const,
      pick: 1
    })),
    combinedText
  }

  return result
})
