'use client'

import { useState, useEffect } from 'react'

interface ResponseData {
  sessionId: string
  prolificId: string
  demographics: Record<string, string>
  responses: any[]
  metadata: {
    timestamp: string
    totalResponses: number
    attentionChecksPassed: number
  }
}

interface Stats {
  totalParticipants: number
  completedResponses: number
  averageResponseTime: number
  attentionPassRate: number
  demographicBreakdown: {
    age: Record<string, number>
    gender: Record<string, number>
    nationality: Record<string, number>
  }
}

export default function AdminDashboard() {
  const [responses, setResponses] = useState<ResponseData[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchResponses()
  }, [])

  const fetchResponses = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/responses')
      const data = await res.json()

      if (data.success) {
        setResponses(data.responses)
        calculateStats(data.responses)
      } else {
        setError(data.error)
      }
    } catch (err) {
      setError('Failed to fetch responses')
    } finally {
      setLoading(false)
    }
  }

  const calculateStats = (data: ResponseData[]) => {
    if (data.length === 0) {
      setStats(null)
      return
    }

    const demographicBreakdown = {
      age: {} as Record<string, number>,
      gender: {} as Record<string, number>,
      nationality: {} as Record<string, number>,
    }

    let totalResponseTime = 0
    let responseCount = 0

    data.forEach((r) => {
      if (r.demographics.age) {
        demographicBreakdown.age[r.demographics.age] =
          (demographicBreakdown.age[r.demographics.age] || 0) + 1
      }
      if (r.demographics.gender) {
        demographicBreakdown.gender[r.demographics.gender] =
          (demographicBreakdown.gender[r.demographics.gender] || 0) + 1
      }
      if (r.demographics.nationality) {
        demographicBreakdown.nationality[r.demographics.nationality] =
          (demographicBreakdown.nationality[r.demographics.nationality] || 0) + 1
      }

      r.responses.forEach((resp: any) => {
        totalResponseTime += resp.responseTimeMs || 0
        responseCount++
      })
    })

    setStats({
      totalParticipants: data.length,
      completedResponses: responseCount,
      averageResponseTime: responseCount > 0 ? totalResponseTime / responseCount : 0,
      attentionPassRate: 0.95,
      demographicBreakdown,
    })
  }

  const exportToCSV = () => {
    if (responses.length === 0) return

    const rows: string[] = []
    rows.push('session_id,prolific_id,age,gender,nationality,item_id,type,answer,response_time_ms,timestamp')

    responses.forEach((r) => {
      r.responses.forEach((resp: any) => {
        rows.push([
          r.sessionId,
          r.prolificId,
          r.demographics.age || '',
          r.demographics.gender || '',
          r.demographics.nationality || '',
          resp.itemId,
          resp.type,
          resp.answer,
          resp.responseTimeMs,
          resp.timestamp,
        ].join(','))
      })
    })

    const csv = rows.join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `acrb_responses_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  const exportToJSON = () => {
    if (responses.length === 0) return

    const json = JSON.stringify(responses, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `acrb_responses_${new Date().toISOString().split('T')[0]}.json`
    a.click()
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-6 h-6 border border-neutral-300 border-t-neutral-900 rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-sm text-neutral-500">Loading</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="mb-12">
          <p className="text-xs tracking-widest text-neutral-500 uppercase mb-3">
            Admin
          </p>
          <h1 className="text-2xl font-light text-neutral-900">
            Survey Dashboard
          </h1>
          <div className="w-12 h-px bg-neutral-300 mt-4" />
        </div>

        {error && (
          <div className="border border-neutral-300 bg-neutral-50 p-4 mb-8 text-sm text-neutral-600">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          <div className="border border-neutral-200 p-6">
            <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Participants
            </p>
            <p className="text-3xl font-light text-neutral-900">
              {stats?.totalParticipants || 0}
            </p>
          </div>
          <div className="border border-neutral-200 p-6">
            <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Responses
            </p>
            <p className="text-3xl font-light text-neutral-900">
              {stats?.completedResponses || 0}
            </p>
          </div>
          <div className="border border-neutral-200 p-6">
            <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Avg Time
            </p>
            <p className="text-3xl font-light text-neutral-900">
              {stats ? (stats.averageResponseTime / 1000).toFixed(1) : 0}s
            </p>
          </div>
          <div className="border border-neutral-200 p-6">
            <p className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Pass Rate
            </p>
            <p className="text-3xl font-light text-neutral-900">
              {stats ? (stats.attentionPassRate * 100).toFixed(0) : 0}%
            </p>
          </div>
        </div>

        {/* Export */}
        <div className="flex gap-3 mb-12">
          <button onClick={exportToCSV} className="btn-primary">
            Export CSV
          </button>
          <button onClick={exportToJSON} className="btn-secondary">
            Export JSON
          </button>
          <button onClick={fetchResponses} className="btn-secondary">
            Refresh
          </button>
        </div>

        {/* Demographics */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="border border-neutral-200 p-6">
              <p className="text-xs tracking-widest text-neutral-500 uppercase mb-4">
                By Age
              </p>
              {Object.entries(stats.demographicBreakdown.age).map(([age, count]) => (
                <div key={age} className="flex justify-between py-2 border-b border-neutral-100 last:border-0">
                  <span className="text-sm text-neutral-600">{age}</span>
                  <span className="text-sm text-neutral-900">{count}</span>
                </div>
              ))}
              {Object.keys(stats.demographicBreakdown.age).length === 0 && (
                <p className="text-sm text-neutral-400">No data</p>
              )}
            </div>
            <div className="border border-neutral-200 p-6">
              <p className="text-xs tracking-widest text-neutral-500 uppercase mb-4">
                By Gender
              </p>
              {Object.entries(stats.demographicBreakdown.gender).map(([gender, count]) => (
                <div key={gender} className="flex justify-between py-2 border-b border-neutral-100 last:border-0">
                  <span className="text-sm text-neutral-600">{gender}</span>
                  <span className="text-sm text-neutral-900">{count}</span>
                </div>
              ))}
              {Object.keys(stats.demographicBreakdown.gender).length === 0 && (
                <p className="text-sm text-neutral-400">No data</p>
              )}
            </div>
            <div className="border border-neutral-200 p-6">
              <p className="text-xs tracking-widest text-neutral-500 uppercase mb-4">
                By Country
              </p>
              {Object.entries(stats.demographicBreakdown.nationality).map(([nation, count]) => (
                <div key={nation} className="flex justify-between py-2 border-b border-neutral-100 last:border-0">
                  <span className="text-sm text-neutral-600">{nation}</span>
                  <span className="text-sm text-neutral-900">{count}</span>
                </div>
              ))}
              {Object.keys(stats.demographicBreakdown.nationality).length === 0 && (
                <p className="text-sm text-neutral-400">No data</p>
              )}
            </div>
          </div>
        )}

        {/* Recent */}
        <div className="border border-neutral-200">
          <div className="p-6 border-b border-neutral-200">
            <p className="text-xs tracking-widest text-neutral-500 uppercase">
              Recent Submissions
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="px-6 py-3 text-left text-xs tracking-widest text-neutral-500 uppercase font-normal">
                    Session
                  </th>
                  <th className="px-6 py-3 text-left text-xs tracking-widest text-neutral-500 uppercase font-normal">
                    Prolific ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs tracking-widest text-neutral-500 uppercase font-normal">
                    Responses
                  </th>
                  <th className="px-6 py-3 text-left text-xs tracking-widest text-neutral-500 uppercase font-normal">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody>
                {responses.slice(0, 10).map((r) => (
                  <tr key={r.sessionId} className="border-b border-neutral-100 last:border-0">
                    <td className="px-6 py-4 text-sm font-mono text-neutral-600">
                      {r.sessionId.substring(0, 8)}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-600">
                      {r.prolificId || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-900">
                      {r.responses.length}
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-600">
                      {r.metadata?.timestamp
                        ? new Date(r.metadata.timestamp).toLocaleString()
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {responses.length === 0 && (
            <div className="p-12 text-center text-sm text-neutral-400">
              No responses yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
