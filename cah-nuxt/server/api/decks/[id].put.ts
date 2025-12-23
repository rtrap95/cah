import { useDB, schema } from '../../database'
import { eq, sql } from 'drizzle-orm'

interface UpdateDeckBody {
  name?: string
  shortName?: string
  blackLogoPath?: string | null
  whiteLogoPath?: string | null
  blackBackLogoPath?: string | null
  whiteBackLogoPath?: string | null
  primaryColor?: string
  secondaryColor?: string
}

export default defineEventHandler(async (event) => {
  const db = useDB()
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody<UpdateDeckBody>(event)

  if (isNaN(id)) {
    throw createError({
      statusCode: 400,
      message: 'Invalid deck ID',
    })
  }

  const existing = await db.query.decks.findFirst({
    where: eq(schema.decks.id, id),
  })

  if (!existing) {
    throw createError({
      statusCode: 404,
      message: 'Deck not found',
    })
  }

  const [updated] = await db.update(schema.decks)
    .set({
      name: body.name ?? existing.name,
      shortName: body.shortName?.toUpperCase().slice(0, 5) ?? existing.shortName,
      blackLogoPath: body.blackLogoPath !== undefined ? body.blackLogoPath : existing.blackLogoPath,
      whiteLogoPath: body.whiteLogoPath !== undefined ? body.whiteLogoPath : existing.whiteLogoPath,
      blackBackLogoPath: body.blackBackLogoPath !== undefined ? body.blackBackLogoPath : existing.blackBackLogoPath,
      whiteBackLogoPath: body.whiteBackLogoPath !== undefined ? body.whiteBackLogoPath : existing.whiteBackLogoPath,
      primaryColor: body.primaryColor ?? existing.primaryColor,
      secondaryColor: body.secondaryColor ?? existing.secondaryColor,
      updatedAt: sql`CURRENT_TIMESTAMP`,
    })
    .where(eq(schema.decks.id, id))
    .returning()

  return updated
})
