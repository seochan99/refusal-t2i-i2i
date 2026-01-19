'use client'

import { useState, useEffect, useMemo } from 'react'

export const dynamic = 'force-dynamic'

interface SampledItem {
  id: string
  model: string
  promptId: string
  category: string
  categoryName: string
  race: string
  gender: string
  age: string
  filename: string
  sourceImageUrl: string
  outputImageUrl: string
}

interface SampledData {
  experiment: string
  description: string
  total_items: number
  items: SampledItem[]
}

const MODELS = ['all', 'flux', 'qwen', 'step1x']
const RACES = ['all', 'Black', 'EastAsian', 'Indian', 'Latino', 'MiddleEastern', 'SoutheastAsian', 'White']
const GENDERS = ['all', 'Male', 'Female']
const AGES = ['all', '20s', '30s', '40s', '50s', '60s', '70plus']
const CATEGORIES = ['all', 'B', 'D']

export default function AMTReviewPage() {
  const [data, setData] = useState<SampledData | null>(null)
  const [loading, setLoading] = useState(true)

  // Filters
  const [modelFilter, setModelFilter] = useState('all')
  const [raceFilter, setRaceFilter] = useState('all')
  const [genderFilter, setGenderFilter] = useState('all')
  const [ageFilter, setAgeFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [searchPrompt, setSearchPrompt] = useState('')

  // Pagination
  const [page, setPage] = useState(1)
  const itemsPerPage = 20

  useEffect(() => {
    fetch('/data/exp1_amt_sampled.json')
      .then(res => res.json())
      .then(data => {
        setData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load data:', err)
        setLoading(false)
      })
  }, [])

  const filteredItems = useMemo(() => {
    if (!data) return []

    return data.items.filter(item => {
      if (modelFilter !== 'all' && item.model !== modelFilter) return false
      if (raceFilter !== 'all' && item.race !== raceFilter) return false
      if (genderFilter !== 'all' && item.gender !== genderFilter) return false
      if (ageFilter !== 'all' && item.age !== ageFilter) return false
      if (categoryFilter !== 'all' && item.category !== categoryFilter) return false
      if (searchPrompt && !item.promptId.toLowerCase().includes(searchPrompt.toLowerCase())) return false
      return true
    })
  }, [data, modelFilter, raceFilter, genderFilter, ageFilter, categoryFilter, searchPrompt])

  const paginatedItems = useMemo(() => {
    const start = (page - 1) * itemsPerPage
    return filteredItems.slice(start, start + itemsPerPage)
  }, [filteredItems, page])

  const totalPages = Math.ceil(filteredItems.length / itemsPerPage)

  // Reset page when filters change
  useEffect(() => {
    setPage(1)
  }, [modelFilter, raceFilter, genderFilter, ageFilter, categoryFilter, searchPrompt])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-lg" style={{ color: 'var(--text-muted)' }}>Loading sampled data...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-lg text-red-500">Failed to load data</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
          AMT Sampling Review
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {data.total_items} sampled items for human evaluation
        </p>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto mb-6 p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex flex-wrap gap-4 items-center">
          {/* Model */}
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>Model</label>
            <select
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
              className="px-3 py-1.5 rounded text-sm"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}
            >
              {MODELS.map(m => <option key={m} value={m}>{m === 'all' ? 'All Models' : m}</option>)}
            </select>
          </div>

          {/* Race */}
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>Race</label>
            <select
              value={raceFilter}
              onChange={(e) => setRaceFilter(e.target.value)}
              className="px-3 py-1.5 rounded text-sm"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}
            >
              {RACES.map(r => <option key={r} value={r}>{r === 'all' ? 'All Races' : r}</option>)}
            </select>
          </div>

          {/* Gender */}
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>Gender</label>
            <select
              value={genderFilter}
              onChange={(e) => setGenderFilter(e.target.value)}
              className="px-3 py-1.5 rounded text-sm"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}
            >
              {GENDERS.map(g => <option key={g} value={g}>{g === 'all' ? 'All Genders' : g}</option>)}
            </select>
          </div>

          {/* Age */}
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>Age</label>
            <select
              value={ageFilter}
              onChange={(e) => setAgeFilter(e.target.value)}
              className="px-3 py-1.5 rounded text-sm"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}
            >
              {AGES.map(a => <option key={a} value={a}>{a === 'all' ? 'All Ages' : a}</option>)}
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-1.5 rounded text-sm"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}
            >
              {CATEGORIES.map(c => <option key={c} value={c}>{c === 'all' ? 'All Categories' : `Cat ${c}`}</option>)}
            </select>
          </div>

          {/* Prompt Search */}
          <div>
            <label className="text-xs font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>Prompt ID</label>
            <input
              type="text"
              value={searchPrompt}
              onChange={(e) => setSearchPrompt(e.target.value)}
              placeholder="e.g. B01"
              className="px-3 py-1.5 rounded text-sm w-24"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border-default)' }}
            />
          </div>

          {/* Results count */}
          <div className="ml-auto text-sm" style={{ color: 'var(--text-secondary)' }}>
            Showing {paginatedItems.length} of {filteredItems.length} items
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {paginatedItems.map((item) => (
            <div
              key={item.id}
              className="rounded-lg overflow-hidden"
              style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-default)' }}
            >
              {/* Images */}
              <div className="flex">
                <div className="w-1/2 aspect-square relative">
                  <img
                    src={item.sourceImageUrl}
                    alt="Source"
                    className="w-full h-full object-cover"
                  />
                  <span className="absolute bottom-1 left-1 text-[10px] px-1 rounded" style={{ backgroundColor: 'rgba(0,0,0,0.7)', color: 'white' }}>
                    Source
                  </span>
                </div>
                <div className="w-1/2 aspect-square relative">
                  <img
                    src={item.outputImageUrl}
                    alt="Output"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const img = e.target as HTMLImageElement
                      if (img.src.includes('_success.png')) {
                        img.src = item.outputImageUrl.replace('_success.png', '_unchanged.png')
                      }
                    }}
                  />
                  <span className="absolute bottom-1 right-1 text-[10px] px-1 rounded" style={{ backgroundColor: 'rgba(0,0,0,0.7)', color: 'white' }}>
                    Output
                  </span>
                </div>
              </div>

              {/* Info */}
              <div className="p-2">
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                  {item.promptId}
                </div>
                <div className="flex flex-wrap gap-1">
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                    {item.model}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>
                    {item.race}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>
                    {item.gender}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)' }}>
                    {item.age}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-2 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded text-sm disabled:opacity-50"
              style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
            >
              Prev
            </button>
            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded text-sm disabled:opacity-50"
              style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)' }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
