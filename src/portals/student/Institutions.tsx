import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Landmark, MapPin, Globe, ArrowRight, GraduationCap } from 'lucide-react'
import { getInstitutions } from '../../lib/api'
import type { InstitutionSummary } from '../../types'
import { PageHeader, SearchInput, GlassPanel, EmptyState, Badge } from '../../components/ui'
import { SkeletonCard } from '../../components/ui/Skeleton'

/**
 * Student Institution Directory — mirrors the bento glass-card grid already
 * established for the Company directory (see Companies.tsx). Search is
 * backend-driven (GET /api/institutions?search=...), debounced so it
 * doesn't fire a request per keystroke.
 */
export function Institutions() {
  const [institutions, setInstitutions] = useState<InstitutionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true)
      getInstitutions(query.trim() ? { search: query.trim() } : undefined)
        .then((data) => {
          setInstitutions(data)
          setHasSearched(true)
        })
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(handle)
  }, [query])

  return (
    <div>
      <PageHeader
        title="Institutions"
        eyebrow="Academic Discovery"
        icon={Landmark}
        description="Discover universities and academic institutions."
      />

      <SearchInput
        placeholder="Search institutions…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="mb-5 max-w-xs"
      />

      {loading && institutions.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <SkeletonCard lines={3} />
          <SkeletonCard lines={3} />
        </div>
      ) : institutions.length === 0 && hasSearched ? (
        <EmptyState
          icon={Landmark}
          title="No institutions found"
          description={query ? `No institutions found matching "${query}".` : 'No institutions are in the directory yet.'}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {institutions.map((inst) => (
            <GlassPanel key={inst.id} className="flex flex-col gap-3 p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary-line bg-primary-bg text-primary">
                  <GraduationCap className="h-5 w-5" strokeWidth={1.8} />
                </div>
                {inst.institution_type && (
                  <Badge tone="primary" size="sm" withIcon={false}>
                    {inst.institution_type}
                  </Badge>
                )}
              </div>
              <div>
                <p className="text-[15px] font-bold text-ink">{inst.name}</p>
                {inst.location && (
                  <p className="mt-1 flex items-center gap-1 text-[12px] text-muted">
                    <MapPin className="h-3 w-3" strokeWidth={2} /> {inst.location}
                  </p>
                )}
                {inst.description && <p className="mt-2 line-clamp-2 text-[13px] text-body">{inst.description}</p>}
              </div>
              <div className="mt-auto flex items-center gap-2 border-t border-white/5 pt-3">
                <Link
                  to={`/student/institutions/${inst.id}`}
                  className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-[12px] font-semibold text-white transition-opacity hover:opacity-90"
                >
                  View Institution <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                {inst.website && (
                  <a
                    href={inst.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-line px-3 py-2 text-[12px] font-semibold text-body transition-colors hover:border-primary-line hover:text-ink"
                  >
                    <Globe className="h-3.5 w-3.5" strokeWidth={2} /> Website
                  </a>
                )}
              </div>
            </GlassPanel>
          ))}
        </div>
      )}
    </div>
  )
}
