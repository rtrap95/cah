import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'
import { sql, relations } from 'drizzle-orm'

export const decks = sqliteTable('decks', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  shortName: text('short_name').notNull(),
  blackLogoPath: text('black_logo_path'),
  whiteLogoPath: text('white_logo_path'),
  blackBackLogoPath: text('black_back_logo_path'),
  whiteBackLogoPath: text('white_back_logo_path'),
  primaryColor: text('primary_color').default('#000000').notNull(),
  secondaryColor: text('secondary_color').default('#FFFFFF').notNull(),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`).notNull(),
  updatedAt: text('updated_at').default(sql`CURRENT_TIMESTAMP`).notNull(),
})

export const cards = sqliteTable('cards', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  deckId: integer('deck_id').notNull().references(() => decks.id, { onDelete: 'cascade' }),
  text: text('text').notNull(),
  cardType: text('card_type', { enum: ['black', 'white'] }).notNull(),
  pick: integer('pick').default(1).notNull(),
  fontSize: integer('font_size').default(100).notNull(),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`).notNull(),
})

export const settings = sqliteTable('settings', {
  key: text('key').primaryKey(),
  value: text('value'),
})

// Relations
export const decksRelations = relations(decks, ({ many }) => ({
  cards: many(cards),
}))

export const cardsRelations = relations(cards, ({ one }) => ({
  deck: one(decks, {
    fields: [cards.deckId],
    references: [decks.id],
  }),
}))

export type InsertDeck = typeof decks.$inferInsert
export type SelectDeck = typeof decks.$inferSelect
export type InsertCard = typeof cards.$inferInsert
export type SelectCard = typeof cards.$inferSelect
