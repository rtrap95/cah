import { useDB, schema } from '../../database'
import { eq } from 'drizzle-orm'

export default defineEventHandler(async () => {
  const db = useDB()
  const setting = await db.query.settings.findFirst({
    where: eq(schema.settings.key, 'default_deck_id')
  })

  if (!setting || !setting.value) {
    return { defaultDeckId: null }
  }

  return { defaultDeckId: Number(setting.value) }
})
