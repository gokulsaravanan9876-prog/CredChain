import { useEffect, useState } from 'react'
import { Shield, Check, Activity as ActivityIcon } from 'lucide-react'
import { getInstitutionActivity } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import { useAuth } from '../../context/AuthContext'
import type { AccessLogEntry } from '../../types'
import { PageHeader, EmptyState, ErrorState } from '../../components/ui'
import { TONE_CLASSES, cx, type Tone } from '../../lib/utils'
import { SkeletonCard } from '../../components/ui/Skeleton'

const LOG_ICON = { shield: Shield, mail: Shield, check: Check }
const LOG_TONE: Record<AccessLogEntry['icon'], Tone> = { shield: 'primary', mail: 'primary', check: 'good' }

/**
 * Reproduces Stitch's "activity_log" screen: each event is its own glass
 * card with a status chip + timestamp header row, a bold title, and a
 * description line, connected by a glowing vertical line with an icon-node
 * per card (see stitch1/activity_log/screen.png). Stitch's own reference
 * pads each card with fabricated on-chain metadata (Tx Hash, Gas Used,
 * ZK-proof predicates) — the real AccessLogEntry has no such fields, so
 * those metadata boxes are simply omitted rather than invented; only the
 * real action/actor/timestamp are shown.
 */
function ActivityCard({ entry, last }: { entry: AccessLogEntry; last: boolean }) {
  const Icon = LOG_ICON[entry.icon]
  const tone = TONE_CLASSES[LOG_TONE[entry.icon]]
  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <div className={cx('z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border', tone.border, tone.bg)}>
          <Icon className={cx('h-4 w-4', tone.text)} strokeWidth={2.25} />
        </div>
        {!last && <span aria-hidden className="mt-1 w-px flex-1 bg-gradient-to-b from-line-strong to-transparent" />}
      </div>
      <div className={cx('mb-4 flex-1 rounded-xl border p-4', tone.border === 'border-line' ? 'border-line' : 'border-line', 'glass-surface')}>
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <span className={cx('rounded-full border px-2 py-0.5 font-[family-name:var(--font-mono)] text-[10px] font-bold uppercase tracking-wider', tone.bg, tone.text, tone.border)}>
            {entry.icon === 'check' ? 'Verified' : entry.icon === 'mail' ? 'Request' : 'Issued'}
          </span>
          <span className="text-[11px] text-faint">{entry.timestamp}</span>
        </div>
        <p className="text-sm font-bold text-ink">{entry.action}</p>
        <p className="mt-0.5 text-[13px] text-muted">{entry.actor}</p>
      </div>
    </div>
  )
}

export function InstitutionActivity() {
  const { user } = useAuth()
  const [log, setLog] = useState<AccessLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getInstitutionActivity()
      .then(setLog)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load activity. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader
        title="Activity"
        eyebrow="Audit Trail"
        icon={ActivityIcon}
        description={`Issuance, revocation, and verification events for ${user?.org_name ?? 'your institution'}'s credentials.`}
      />

      {error && <div className="mb-5 max-w-2xl"><ErrorState description={error} onRetry={() => window.location.reload()} /></div>}

      {loading ? (
        <div className="max-w-2xl"><SkeletonCard lines={4} /></div>
      ) : log.length === 0 ? (
        <EmptyState icon={ActivityIcon} title="No activity yet" description="Issuance, revocation, and verification events will show up here." />
      ) : (
        <div className="max-w-2xl">
          {log.map((entry, i) => (
            <ActivityCard key={entry.id} entry={entry} last={i === log.length - 1} />
          ))}
        </div>
      )}
    </div>
  )
}
