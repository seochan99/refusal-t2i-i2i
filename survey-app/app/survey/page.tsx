'use client'

import { useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'
import ProgressBar from '@/components/ProgressBar'
import ImageDisplay from '@/components/ImageDisplay'
import LikertScale from '@/components/LikertScale'
import MultipleChoice from '@/components/MultipleChoice'

interface SurveyItem {
  id: string
  type: 'quality' | 'attribute' | 'refusal' | 'attention'
  imageUrl: string
  prompt: string
  attribute?: string
  attributeValue?: string
  model?: string
  isRefusal?: boolean
  refusalMessage?: string
  correctAnswer?: string
}

interface Response {
  itemId: string
  type: string
  answer: string | number
  responseTimeMs: number
  timestamp: string
}

const generateSampleItems = (): SurveyItem[] => {
  const items: SurveyItem[] = []

  for (let i = 0; i < 45; i++) {
    const types: SurveyItem['type'][] = ['quality', 'attribute', 'refusal']
    const type = types[i % 3]

    items.push({
      id: `item_${i}`,
      type,
      imageUrl: `/images/sample_${i % 10}.jpg`,
      prompt: `A ${['Korean', 'African', 'European'][i % 3]} person as a ${['doctor', 'teacher', 'engineer'][i % 3]}`,
      attribute: ['culture', 'gender', 'age'][i % 3],
      attributeValue: ['Korean', 'Female', 'Elderly'][i % 3],
      model: ['FLUX', 'DALL-E', 'Midjourney'][i % 3],
      isRefusal: i % 7 === 0,
      refusalMessage: i % 7 === 0 ? 'Request blocked due to content policy.' : undefined,
    })
  }

  const attentionChecks: SurveyItem[] = [
    { id: 'attention_1', type: 'attention', imageUrl: '/images/attention_1.jpg', prompt: 'Select "Poor" for this question', correctAnswer: '2' },
    { id: 'attention_2', type: 'attention', imageUrl: '/images/attention_2.jpg', prompt: 'Select "Yes, clearly"', correctAnswer: 'yes_clearly' },
    { id: 'attention_3', type: 'attention', imageUrl: '/images/attention_3.jpg', prompt: 'Select "Refused"', correctAnswer: 'refused' },
  ]

  const positions = [15, 30, 40]
  positions.forEach((pos, idx) => {
    items.splice(pos + idx, 0, attentionChecks[idx])
  })

  return items
}

export default function SurveyPage() {
  const router = useRouter()
  const [items] = useState<SurveyItem[]>(generateSampleItems)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [responses, setResponses] = useState<Response[]>([])
  const [currentAnswer, setCurrentAnswer] = useState<string | number | null>(null)
  const [startTime, setStartTime] = useState<number>(Date.now())
  const [sessionId] = useState<string>(() => uuidv4())

  const currentItem = items[currentIndex]
  const isLastItem = currentIndex === items.length - 1

  useEffect(() => {
    setStartTime(Date.now())
    setCurrentAnswer(null)
  }, [currentIndex])

  const handleNext = async () => {
    if (currentAnswer === null) return

    const responseTimeMs = Date.now() - startTime
    const newResponse: Response = {
      itemId: currentItem.id,
      type: currentItem.type,
      answer: currentAnswer,
      responseTimeMs,
      timestamp: new Date().toISOString(),
    }

    const updatedResponses = [...responses, newResponse]
    setResponses(updatedResponses)
    localStorage.setItem(`survey_responses_${sessionId}`, JSON.stringify(updatedResponses))

    if (isLastItem) {
      try {
        await fetch('/api/responses', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId,
            prolificId: localStorage.getItem('prolificId'),
            demographics: JSON.parse(localStorage.getItem('demographics') || '{}'),
            responses: updatedResponses,
          }),
        })
      } catch (error) {
        console.error('Failed to save responses:', error)
      }
      router.push('/complete')
    } else {
      setCurrentIndex((prev) => prev + 1)
    }
  }

  const renderQuestion = () => {
    switch (currentItem.type) {
      case 'quality':
      case 'attention':
        return (
          <div className="space-y-8">
            <div>
              <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
                Image Quality
              </p>
              <p className="text-neutral-600 text-sm">
                Rate the overall quality of this generated image.
              </p>
            </div>
            <ImageDisplay
              src={currentItem.imageUrl}
              alt="Generated image"
              prompt={currentItem.prompt}
            />
            <LikertScale
              value={currentAnswer as number | null}
              onChange={setCurrentAnswer}
            />
          </div>
        )

      case 'attribute':
        return (
          <div className="space-y-8">
            <div>
              <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
                Attribute Check
              </p>
              <p className="text-neutral-600 text-sm">
                Does this image show a <span className="text-neutral-900 font-medium">{currentItem.attributeValue}</span> person?
              </p>
            </div>
            <ImageDisplay
              src={currentItem.imageUrl}
              alt="Generated image"
              prompt={currentItem.prompt}
            />
            <MultipleChoice
              options={[
                { value: 'yes_clearly', label: 'Yes, clearly' },
                { value: 'somewhat', label: 'Somewhat' },
                { value: 'no', label: 'No' },
                { value: 'cannot_tell', label: 'Cannot tell' },
              ]}
              value={currentAnswer as string | null}
              onChange={setCurrentAnswer}
            />
          </div>
        )

      case 'refusal':
        return (
          <div className="space-y-8">
            <div>
              <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
                Generation Status
              </p>
              <p className="text-neutral-600 text-sm">
                Was this image request generated, refused, or modified?
              </p>
            </div>
            <ImageDisplay
              src={currentItem.imageUrl}
              alt="Generated image"
              prompt={currentItem.prompt}
              isRefusal={currentItem.isRefusal}
              refusalMessage={currentItem.refusalMessage}
            />
            <MultipleChoice
              options={[
                { value: 'generated', label: 'Generated successfully' },
                { value: 'refused', label: 'Refused / Blocked' },
                { value: 'modified', label: 'Modified / Altered' },
              ]}
              value={currentAnswer as string | null}
              onChange={setCurrentAnswer}
              columns={1}
            />
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <ProgressBar current={currentIndex + 1} total={items.length} />

        <div className="survey-card">
          <div className="mb-8">
            <p className="text-xs tracking-widest text-neutral-500 uppercase mb-3">
              Step 3 of 4 — Question {currentIndex + 1}
            </p>
            <div className="w-12 h-px bg-neutral-300" />
          </div>

          {renderQuestion()}

          <div className="mt-10 flex justify-between items-center border-t border-neutral-200 pt-8">
            <span className="text-xs text-neutral-400">
              {currentIndex + 1} / {items.length}
            </span>
            <button
              onClick={handleNext}
              disabled={currentAnswer === null}
              className="btn-primary"
            >
              {isLastItem ? 'Complete' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
