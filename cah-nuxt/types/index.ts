export type CardType = 'black' | 'white'

export interface Card {
  id?: number
  deckId?: number
  text: string
  cardType: CardType
  pick: number
  fontSize: number
  createdAt?: Date
}

export interface DeckConfig {
  name: string
  shortName: string
  blackLogoPath?: string | null
  whiteLogoPath?: string | null
  blackBackLogoPath?: string | null
  whiteBackLogoPath?: string | null
  primaryColor: string
  secondaryColor: string
}

export interface Deck {
  id?: number
  config: DeckConfig
  blackCards: Card[]
  whiteCards: Card[]
  createdAt?: Date
  updatedAt?: Date
}

export interface DeckListItem {
  id: number
  name: string
  shortName: string
  blackCount: number
  whiteCount: number
  totalCards: number
  createdAt: Date
  updatedAt: Date
}

export interface RandomCombo {
  blackCard: Card
  whiteCards: Card[]
  combinedText: string
}

export interface ExportConfig {
  deckName: string
  shortName: string
  blackLogoPath?: string | null
  whiteLogoPath?: string | null
  blackBackLogoPath?: string | null
  whiteBackLogoPath?: string | null
  cardsType: 'all' | 'black' | 'white'
  includeBacks: boolean
  showShortName?: boolean
  logoSize?: number
  backLogoSize?: number
  cardPadding?: number
}
