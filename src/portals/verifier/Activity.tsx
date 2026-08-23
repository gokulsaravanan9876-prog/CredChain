import { useEffect, useMemo, useState } from 'react'
import { Shield, Mail, Check, Activity as ActivityIcon } from 'lucide-react'
import { getVerifierActivity } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import type { AccessLogEntry } from '../../types'
import { PageHeader, Card, EmptyState, ErrorState, Timeline, TimelineItem, FilterPills } from '../../components/ui'
import { SkeletonCard } from '../../components/ui/Skeleton'

const LOG_ICON = { shield: Shield, mail: Mail, check: Check }
const LOG_TONE = { shield: 'primary', mail: 'neutral', check: 'good' } as const

/**
 * Reproduces Stitch's "activity_log" screen: a filterable connected audit
 * timeline (see stitch1/activity_log/code.html + screen.png) — filter pills
 * above a single glowing vertical line with a colored icon-node per event.
 * Stitch's own reference invents Tx Hash / Gas Used / DID detail boxes on
 * every card; this app has no such per-event technical metadata to show, so
 * those boxes are simply omitted rather than fabricated — every title/actor/
 * timestamp below is the real AccessLogEntry already returned by
 * getVerifierActivity. Filtering is a client-side-only presentational
 * addition (Stitch's own "All Events/Issued/Verified/Shared" pattern) over
 * the same already-fetched `log` array — no new API call.
 */
type Filter = 'all' | 'shield' | 'mail' | 'check'
const FILTER_OPTIONS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All Events' },
  { value: 'check', label: 'Verified' },
  { value: 'shield', label: 'Requests' },
  { value: 'mail', label: 'Shared' },
]

export function VerifierActivity() {
  const [log, setLog] = useState<AccessLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')

  useEffect(() => {
    getVerifierActivity()
      .then(setLog)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load activity. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => (filter === 'all' ? log : log.filter((e) => e.icon === filter)), [log, filter])

  return (
    <div>
      <PageHeader title="Activity" eyebrow="Audit Trail" icon={ActivityIcon} description="A record of verification checks and credential requests." />
      {error && <div className="mb-5 max-w-2xl"><ErrorState description={error} onRetry={() => window.location.reload()} /></div>}
      {loading ? (
        <div className="max-w-2xl"><SkeletonCard lines={4} /></div>
      ) : log.length === 0 ? (
        <EmptyState icon={ActivityIcon} title="No activity yet" description="Verification checks will appear here as you review candidates." />
      ) : (
        <div className="max-w-2xl">
          <div className="mb-4">
            <FilterPills options={FILTER_OPTIONS} value={filter} onChange={setFilter} />
          </div>
          {filtered.length === 0 ? (
            <EmptyState icon={ActivityIcon} title="No matching events" description="Try a different filter." />
          ) : (
            <Card className="overflow-hidden py-1">
              <Timeline>
                {filtered.map((entry, i) => (
                  <TimelineItem
                    key={entry.id}
                    icon={LOG_ICON[entry.icon]}
                    tone={LOG_TONE[entry.icon]}
                    title={entry.action}
                    subtitle={entry.actor}
                    timestamp={entry.timestamp}
                    last={i === filtered.length - 1}
                  />
                ))}
              </Timeline>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
