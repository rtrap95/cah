import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import { join } from 'path'

export default defineEventHandler(async (event) => {
  const formData = await readMultipartFormData(event)

  if (!formData || formData.length === 0) {
    throw createError({
      statusCode: 400,
      message: 'No file uploaded'
    })
  }

  const file = formData.find(f => f.name === 'file')
  const deckId = formData.find(f => f.name === 'deckId')?.data.toString()
  const logoType = formData.find(f => f.name === 'logoType')?.data.toString()

  if (!file || !file.data) {
    throw createError({
      statusCode: 400,
      message: 'No file provided'
    })
  }

  if (!deckId || !logoType) {
    throw createError({
      statusCode: 400,
      message: 'Missing deckId or logoType'
    })
  }

  // Validate logo type
  const validTypes = ['blackLogo', 'whiteLogo', 'blackBackLogo', 'whiteBackLogo']
  if (!validTypes.includes(logoType)) {
    throw createError({
      statusCode: 400,
      message: 'Invalid logo type'
    })
  }

  // Validate file type
  const mimeType = file.type
  if (!mimeType?.startsWith('image/')) {
    throw createError({
      statusCode: 400,
      message: 'File must be an image'
    })
  }

  // Get file extension
  const ext = mimeType.split('/')[1] || 'png'

  // Create uploads directory if it doesn't exist
  const uploadsDir = join(process.cwd(), 'public', 'uploads', 'logos')
  if (!existsSync(uploadsDir)) {
    await mkdir(uploadsDir, { recursive: true })
  }

  // Generate unique filename
  const filename = `${deckId}-${logoType}-${Date.now()}.${ext}`
  const filepath = join(uploadsDir, filename)

  // Save file
  await writeFile(filepath, file.data)

  // Return the public URL path
  const publicPath = `/uploads/logos/${filename}`

  return {
    path: publicPath
  }
})
