import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Building2, MapPin, Briefcase, ArrowRight } from 'lucide-react'
import { getRealCompanies } from '../../lib/api'
import type { Company } from '../../types'
import { PageHeader, SearchInput, GlassPanel, EmptyState } from '../../components/ui'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { InitialsAvatar } from '../../components/ui/IconTile'

/**
 * No dedicated Stitch screen exists for a company-discovery list — this
 * inherits the bento glass-card grid language already established in
 * career_opportunities (see the rebuilt src/portals/student/Jobs.tsx) rather
 * than staying a plain vertical list, per the instruction to extend the
 * established design system to un-covered screens instead of leaving them
 * generic.
 */
function initialsOf(name: string) {
  return (
    name
      .split(' ')
      .map((w) => w[0])
      .filter(Boolean)
      .slice(0, 2)
      .join('')
      .toUpperCase() || '?'
  )
}

export function Companies() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')

  useEffect(() => {
    getRealCompanies()
      .then(setCompanies)
      .finally(() => setLoading(false))
  }, [])

  const filtered = companies.filter((c) => c.name.toLowerCase().includes(query.toLowerCase()))

  if (loading) return <div className="grid grid-cols-1 gap-4 sm:grid-cols-2"><SkeletonCard lines={3} /><SkeletonCard lines={3} /></div>

  return (
    <div>
      <PageHeader title="Companies" eyebrow="Professional Discovery" icon={Building2} description="Real company profiles registered on CredChain." />

      <SearchInput
        placeholder="Search companies…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="mb-5 max-w-xs"
      />

      {filtered.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No companies yet"
          description={companies.length === 0 ? 'No companies have registered on CredChain yet.' : 'Try a different search term.'}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {filtered.map((c) => (
            <Link key={c.id} to={`/student/companies/${c.id}`} className="group">
              <GlassPanel className="relative flex h-full flex-col gap-3 overflow-hidden p-5 transition-transform duration-200 group-hover:-translate-y-0.5 group-hover:border-primary-line">
                <div className="flex items-start justify-between gap-3">
                  <InitialsAvatar initials={initialsOf(c.name)} tone="ink" />
                  <ArrowRight className="h-4 w-4 shrink-0 text-faint opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                <div>
                  <p className="text-[15px] font-bold text-ink">{c.name}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-muted">
                    {c.industry && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-3 w-3" strokeWidth={2} /> {c.industry}
                      </span>
                    )}
                    {c.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" strokeWidth={2} /> {c.location}
                      </span>
                    )}
                  </div>
                </div>
              </GlassPanel>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
