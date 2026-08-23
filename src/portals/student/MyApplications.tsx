import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileStack, Clock3, RefreshCw, Star, CheckCircle2, XCircle, Ban } from 'lucide-react'
import { getMyJobApplications, withdrawApplication } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import type { StudentJobApplication, ApplicationStatus } from '../../types'
import { PageHeader, Badge, Button, EmptyState, GlassPanel } from '../../components/ui'
import { SkeletonCard } from '../../components/ui/Skeleton'

const STATUS_TONE: Record<ApplicationStatus, 'good' | 'warn' | 'bad' | 'neutral' | 'primary'> = {
  applied: 'neutral',
  under_review: 'primary',
  shortlisted: 'primary',
  accepted: 'good',
  rejected: 'bad',
  withdrawn: 'neutral',
}

const STATUS_LABEL: Record<ApplicationStatus, string> = {
  applied: 'Applied',
  under_review: 'Under Review',
  shortlisted: 'Shortlisted',
  accepted: 'Accepted',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
}

const STATUS_ICON: Record<ApplicationStatus, typeof Clock3> = {
  applied: Clock3,
  under_review: RefreshCw,
  shortlisted: Star,
  accepted: CheckCircle2,
  rejected: XCircle,
  withdrawn: Ban,
}

/** How far through the real pipeline this status sits — drives the progress rail
 * (Stitch's "Est. 3-5 days" style bar), never a fabricated percentage. */
const STATUS_PROGRESS: Record<ApplicationStatus, number> = {
  applied: 25,
  under_review: 55,
  shortlisted: 80,
  accepted: 100,
  rejected: 100,
  withdrawn: 100,
}

const WITHDRAWABLE: ApplicationStatus[] = ['applied', 'under_review', 'shortlisted']

export function MyApplications() {
  const [applications, setApplications] = useState<StudentJobApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [withdrawingId, setWithdrawingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  function load() {
    return getMyJobApplications()
      .then(setApplications)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  async function handleWithdraw(id: string) {
    setWithdrawingId(id)
    setError(null)
    try {
      await withdrawApplication(id)
      await load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not withdraw this application.')
    } finally {
      setWithdrawingId(null)
    }
  }

  if (loading) return <div className="space-y-4"><SkeletonCard lines={3} /><SkeletonCard lines={3} /></div>

  return (
    <div>
      <PageHeader title="My Applications" eyebrow="Application Pipeline" icon={FileStack} description="Real applications you've submitted to real companies." />

      {error && <div className="mb-5 max-w-2xl rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">{error}</div>}

      {applications.length === 0 ? (
        <EmptyState icon={FileStack} title="No applications yet" description="Apply to a job to see it tracked here." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {applications.map((a) => {
            const StatusIcon = STATUS_ICON[a.status]
            const tone = STATUS_TONE[a.status]
            return (
              <GlassPanel
                key={a.id}
                className={`relative overflow-hidden p-5 ${a.status === 'rejected' ? 'border-l-[3px] border-l-bad' : ''}`}
              >
                <Link to={`/student/jobs/${a.job_id}`} className="block">
                  <div className="mb-3 flex items-start justify-between">
                    <Badge tone={tone} size="sm">
                      {STATUS_LABEL[a.status]}
                    </Badge>
                    <StatusIcon className={`h-5 w-5 ${tone === 'good' ? 'text-good' : tone === 'bad' ? 'text-bad' : tone === 'primary' ? 'text-primary' : 'text-faint'}`} strokeWidth={2} />
                  </div>
                  <h3 className="text-[15px] font-bold text-ink hover:underline">{a.job_title}</h3>
                  <p className="mb-4 text-xs text-muted">{a.company_name}</p>
                </Link>

                {a.status === 'rejected' && a.rejection_reason ? (
                  <div className="rounded-lg border border-bad-line bg-bad-bg p-3">
                    <p className="text-[13px] text-bad">{a.rejection_reason}</p>
                  </div>
                ) : (
                  <>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-canvas-2">
                      <div
                        className={`h-full rounded-full ${tone === 'good' ? 'bg-good' : tone === 'primary' ? 'bg-primary' : 'bg-line-strong'}`}
                        style={{ width: `${STATUS_PROGRESS[a.status]}%` }}
                      />
                    </div>
                    <p className="mt-2 text-right font-[family-name:var(--font-mono)] text-[11px] text-faint">
                      Applied {new Date(a.created_at).toLocaleDateString()}
                    </p>
                  </>
                )}

                {WITHDRAWABLE.includes(a.status) && (
                  <div className="mt-3 border-t border-white/5 pt-3">
                    <Button variant="outline" size="sm" loading={withdrawingId === a.id} onClick={() => handleWithdraw(a.id)}>
                      Withdraw Application
                    </Button>
                  </div>
                )}
              </GlassPanel>
            )
          })}
        </div>
      )}
    </div>
  )
}
