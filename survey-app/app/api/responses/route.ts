import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

const DATA_DIR = path.join(process.cwd(), 'data')

// Ensure data directory exists
async function ensureDataDir() {
  try {
    await fs.access(DATA_DIR)
  } catch {
    await fs.mkdir(DATA_DIR, { recursive: true })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { sessionId, prolificId, demographics, responses } = body

    await ensureDataDir()

    // Save individual response file
    const filename = `response_${sessionId}_${Date.now()}.json`
    const filepath = path.join(DATA_DIR, filename)

    const data = {
      sessionId,
      prolificId,
      demographics,
      responses,
      metadata: {
        userAgent: request.headers.get('user-agent'),
        timestamp: new Date().toISOString(),
        totalResponses: responses.length,
        attentionChecksPassed: calculateAttentionCheckScore(responses),
      },
    }

    await fs.writeFile(filepath, JSON.stringify(data, null, 2))

    // Append to master log
    const masterLogPath = path.join(DATA_DIR, 'responses_log.jsonl')
    const logEntry = JSON.stringify({
      sessionId,
      prolificId,
      timestamp: new Date().toISOString(),
      responseCount: responses.length,
    }) + '\n'

    await fs.appendFile(masterLogPath, logEntry)

    return NextResponse.json({
      success: true,
      message: 'Responses saved successfully',
      sessionId,
    })
  } catch (error) {
    console.error('Error saving responses:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to save responses' },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    await ensureDataDir()

    const files = await fs.readdir(DATA_DIR)
    const responseFiles = files.filter(f => f.startsWith('response_') && f.endsWith('.json'))

    const responses = await Promise.all(
      responseFiles.map(async (file) => {
        const content = await fs.readFile(path.join(DATA_DIR, file), 'utf-8')
        return JSON.parse(content)
      })
    )

    return NextResponse.json({
      success: true,
      count: responses.length,
      responses,
    })
  } catch (error) {
    console.error('Error fetching responses:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch responses' },
      { status: 500 }
    )
  }
}

function calculateAttentionCheckScore(responses: any[]): number {
  const attentionResponses = responses.filter(r => r.type === 'attention')
  if (attentionResponses.length === 0) return 1

  // In production, compare with expected answers
  // For now, return placeholder
  return attentionResponses.length
}
