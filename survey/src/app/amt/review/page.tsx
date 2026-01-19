import { redirect } from 'next/navigation'

type SearchParams = Record<string, string | string[] | undefined>

const buildQueryString = (searchParams: SearchParams) => {
  const params = new URLSearchParams()
  Object.entries(searchParams).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((entry) => params.append(key, entry))
    } else if (typeof value === 'string') {
      params.append(key, value)
    }
  })
  const query = params.toString()
  return query ? `?${query}` : ''
}

export default function AmtReviewRedirectPage({
  searchParams
}: {
  searchParams: SearchParams
}) {
  const query = buildQueryString(searchParams)
  redirect(`/tasks/review${query}`)
}
