import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Sparkles, FlaskConical, FileText, Building2, Target, Lightbulb, MapPin, AlertTriangle, ShieldCheck, ShieldAlert, ShieldQuestion, Briefcase } from 'lucide-react'
import { getJob, getCredentials, analyzeJobWithAI, applyToJob } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import type { Job, Credential, JobAIAnalysisResult, AiAnalysisMode } from '../../types'
import { PageHeader, Card, Button, Badge, CheckRow, GlassPanel, Glow } from '../../components/ui'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { useToast } from '../../components/ui/Toast'

const EMPLOYMENT_LABEL: Record<string, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  internship: 'Internship',
  contract: 'Contract',
}

function ModeBadge({ mode }: { mode: AiAnalysisMode }) {
  return mode === 'ai' ? (
    <Badge tone="primary" size="sm">
      AI Analysis
    </Badge>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full border border-warn-line bg-warn-bg px-2.5 py-1 text-[11px] font-semibold text-warn">
      <FlaskConical className="h-3 w-3" strokeWidth={2.5} />
      Fallback / Demo Mode
    </span>
  )
}

export function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const toast = useToast()

  const [job, setJob] = useState<Job | null>(null)
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)

  const [analysis, setAnalysis] = useState<JobAIAnalysisResult | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [applyError, setApplyError] = useState<string | null>(null)
  const [applied, setApplied] = useState(false)

  useEffect(() => {
    if (!id) return
    Promise.all([getJob(id), getCredentials()])
      .then(([j, creds]) => {
        setJob(j)
        setCredentials(creds)
        const matched = creds.filter((c) => j.required_documents.some((label) => c.title.toLowerCase().includes(label.toLowerCase())))
        setChecked(new Set(matched.map((c) => c.id)))
      })
      .finally(() => setLoading(false))
  }, [id])

  const activeCredentials = useMemo(() => credentials.filter((c) => c.status !== 'revoked'), [credentials])

  function toggle(credId: string) {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(credId)) next.delete(credId)
      else next.add(credId)
      return next
    })
  }

  async function handleAnalyze() {
    if (!id) return
    setAnalyzing(true)
    setAnalysisError(null)
    try {
      setAnalysis(await analyzeJobWithAI(id))
    } catch (err) {
      setAnalysisError(err instanceof ApiError ? err.message : 'AI analysis is temporarily unavailable. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleApply() {
    if (!id || checked.size === 0) return
    setApplying(true)
    setApplyError(null)
    try {
      await applyToJob(id, Array.from(checked))
      setApplied(true)
      toast('Application submitted')
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.message : 'Could not submit this application.')
    } finally {
      setApplying(false)
    }
  }

  if (loading) {
    return (
      <div>
        <PageHeader title="Loading job..." eyebrow="Opportunity" icon={Briefcase} description=" " />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-5 lg:col-span-2">
            <SkeletonCard lines={4} />
            <SkeletonCard lines={3} />
          </div>
          <SkeletonCard lines={3} />
        </div>
      </div>
    )
  }
  if (!job) return null

  const eligibilityStatus = job.eligibility?.status ?? 'eligible'
  const isIncomplete = eligibilityStatus === 'incomplete'
  const deadlinePassed = job.application_deadline != null && new Date(job.application_deadline).getTime() < Date.now()

  return (
    <div>
      <GlassPanel className="relative mb-6 overflow-hidden p-6">
        <Glow color="cyan" size={320} className="-right-16 -top-20" animate={false} />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-primary-line bg-primary-bg">
              <Briefcase className="h-7 w-7 text-primary" strokeWidth={2} />
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-primary">Opportunity</p>
              <h1 className="text-2xl font-bold tracking-tight text-ink font-[family-name:var(--font-display)]">{job.title}</h1>
              <p className="mt-0.5 text-sm text-muted">{job.company_name}</p>
            </div>
          </div>
          {job.application_deadline && (
            <div className="rounded-lg border border-line bg-surface-2 px-3.5 py-2 text-right text-[12px]">
              <p className="font-bold uppercase tracking-wider text-faint">Deadline</p>
              <p className="font-semibold text-ink">{new Date(job.application_deadline).toLocaleDateString()}</p>
            </div>
          )}
        </div>
      </GlassPanel>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card className="p-6">
            <div className="mb-3 flex flex-wrap items-center gap-3 text-[12px] text-faint">
              {job.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" /> {job.location}
                </span>
              )}
              <span>{EMPLOYMENT_LABEL[job.employment_type]}</span>
              {job.application_deadline && <span>Deadline: {new Date(job.application_deadline).toLocaleDateString()}</span>}
            </div>
            <p className="whitespace-pre-line text-sm text-body">{job.description}</p>

            {job.required_documents.length > 0 && (
              <div className="mt-4 border-t border-line pt-4">
                <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-faint">Required Documents</p>
                <div className="flex flex-wrap gap-1.5">
                  {job.required_documents.map((d) => (
                    <span key={d} className="rounded-full border border-line bg-canvas-2/60 px-2.5 py-1 text-[11px] font-medium text-body">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {job.eligibility && (
            <Card className="p-6">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-bold uppercase tracking-wider text-ink">Your Eligibility</h3>
                {eligibilityStatus === 'eligible' && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-good-bg px-3 py-1 text-[12px] font-bold text-good">
                    <ShieldCheck className="h-3.5 w-3.5" strokeWidth={2.5} /> Eligible
                  </span>
                )}
                {eligibilityStatus === 'not_eligible' && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-bad-bg px-3 py-1 text-[12px] font-bold text-bad">
                    <ShieldAlert className="h-3.5 w-3.5" strokeWidth={2.5} /> Not Eligible
                  </span>
                )}
                {eligibilityStatus === 'incomplete' && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-warn-bg px-3 py-1 text-[12px] font-bold text-warn">
                    <ShieldQuestion className="h-3.5 w-3.5" strokeWidth={2.5} /> Incomplete
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {job.eligibility.checks.map((c) => (
                  <CheckRow
                    key={c.label}
                    label={c.status === 'incomplete' ? `${c.label} (no data on file)` : c.label}
                    state={c.status === 'met' ? 'pass' : c.status === 'incomplete' ? 'gap' : 'fail'}
                    bordered
                  />
                ))}
              </div>
              {eligibilityStatus === 'not_eligible' && (
                <div className="mt-4 rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] font-semibold text-bad">
                  Not eligible based on current requirements.
                </div>
              )}
              {eligibilityStatus === 'incomplete' && (
                <div className="mt-4 rounded-lg bg-warn-bg px-3.5 py-2.5 text-[13px] font-semibold text-warn">
                  Some requirements can't be verified — your credentials don't have this data on file yet. This is not a
                  failure, just missing information.
                </div>
              )}
            </Card>
          )}

          <GlassPanel className="relative overflow-hidden border-ai-line p-6">
            <Glow color="ai" size={260} className="-right-14 -top-16" animate={false} />
            <div className="relative mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-ai-bg text-ai">
                  <Sparkles className="h-4 w-4" strokeWidth={2.25} />
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-ink">AI Opportunity Analysis</h3>
              </div>
              <Button variant="solid" size="sm" loading={analyzing} icon={<Sparkles className="h-3.5 w-3.5" />} onClick={handleAnalyze}>
                Analyze with AI
              </Button>
            </div>
            {!analysis && !analysisError && (
              <p className="text-[13px] text-muted">
                Run a real analysis of this job&rsquo;s requirements against your credentials — what it needs, what you
                already have, and what to prepare.
              </p>
            )}
            {analysisError && <div className="rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">{analysisError}</div>}

            {analysis && (
              <div className="space-y-5 motion-safe:animate-[revealIn_220ms_ease-out]">
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-primary" strokeWidth={2} />
                      <p className="text-xs font-bold uppercase tracking-wider text-ink">Documents</p>
                    </div>
                    <ModeBadge mode={analysis.document_requirements.analysis_mode} />
                  </div>
                  <div className="space-y-2">
                    {analysis.document_requirements.requirements.map((r) => {
                      const w = analysis.document_requirements.wallet_comparison.find((x) => x.document === r.document)
                      return (
                        <CheckRow
                          key={r.document}
                          label={`${r.document}${w ? (w.available ? ' — Available' : ' — Missing from your wallet') : ''}`}
                          state={w ? (w.available ? 'pass' : 'gap') : 'pass'}
                          bordered
                        />
                      )
                    })}
                  </div>
                </div>

                <div className="border-t border-line pt-4">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-primary" strokeWidth={2} />
                      <p className="text-xs font-bold uppercase tracking-wider text-ink">Company Intelligence</p>
                    </div>
                    <ModeBadge mode={analysis.company_intelligence.analysis_mode} />
                  </div>
                  <p className="text-sm text-body">{analysis.company_intelligence.overview}</p>
                  <div className="mt-3 border-t border-line pt-3">
                    <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-faint">Package</p>
                    {analysis.company_intelligence.package_information.available ? (
                      <p className="text-sm font-bold text-ink">
                        {analysis.company_intelligence.package_information.amount} {analysis.company_intelligence.package_information.currency}
                      </p>
                    ) : (
                      <p className="text-sm text-muted">Not available — {analysis.company_intelligence.package_information.message}</p>
                    )}
                  </div>
                </div>

                <div className="border-t border-line pt-4">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-primary" strokeWidth={2} />
                      <p className="text-xs font-bold uppercase tracking-wider text-ink">Credential Match</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <ModeBadge mode={analysis.credential_match.analysis_mode} />
                      <Badge tone="primary" withIcon={false}>
                        {analysis.credential_match.match_summary.score}%
                      </Badge>
                    </div>
                  </div>
                  <p className="mb-3 text-[11px] text-faint">
                    Percentage of measurable requirements currently matched — not a hiring probability.
                  </p>
                  <div className="grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2">
                    {analysis.credential_match.matched.map((label) => (
                      <CheckRow key={label} label={label} state="pass" bordered />
                    ))}
                    {analysis.credential_match.missing.map((label) => (
                      <CheckRow key={label} label={label} state="gap" bordered />
                    ))}
                  </div>
                  {analysis.credential_match.recommendations.length > 0 && (
                    <div className="mt-4 rounded-lg bg-ai-bg p-4">
                      <div className="mb-2 flex items-center gap-2 text-ai">
                        <Lightbulb className="h-4 w-4" strokeWidth={2} />
                        <p className="text-[10px] font-bold uppercase tracking-wider">Preparation Suggestions</p>
                      </div>
                      <ul className="space-y-1">
                        {analysis.credential_match.recommendations.map((rec) => (
                          <li key={rec} className="text-sm italic text-ink">
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </GlassPanel>
        </div>

        <div>
          <Card className="p-5">
            <h3 className="mb-3 text-sm font-bold text-ink">Apply</h3>
            {applied ? (
              <div className="rounded-lg bg-good-bg px-3.5 py-2.5 text-[13px] font-semibold text-good">
                Application submitted.
              </div>
            ) : deadlinePassed ? (
              <p className="text-[13px] text-muted">The application deadline for this job has passed.</p>
            ) : eligibilityStatus === 'not_eligible' ? (
              <p className="text-[13px] text-muted">Not eligible based on current requirements.</p>
            ) : (
              <>
                {isIncomplete && (
                  <p className="mb-3 rounded-lg bg-warn-bg px-3 py-2 text-[12px] font-medium text-warn">
                    Some requirements couldn't be verified from your credentials — you can still apply.
                  </p>
                )}
                {job.required_documents.length > 0 &&
                  (() => {
                    const selected = activeCredentials.filter((c) => checked.has(c.id))
                    const missing = job.required_documents.filter(
                      (label) => !selected.some((c) => c.title.toLowerCase().includes(label.toLowerCase()))
                    )
                    const available = job.required_documents.length - missing.length
                    return (
                      <div className="mb-3 rounded-lg border border-line bg-canvas-2/40 px-3 py-2 text-[12px]">
                        <p className="font-semibold text-ink">
                          {available} / {job.required_documents.length} required documents selected
                        </p>
                        {missing.length > 0 && <p className="mt-0.5 text-faint">Missing: {missing.join(', ')}</p>}
                      </div>
                    )
                  })()}
                <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-faint">Select credentials to share</p>
                {activeCredentials.length === 0 ? (
                  <p className="text-[13px] text-muted">You have no active credentials to share yet.</p>
                ) : (
                  <div className="space-y-2">
                    {activeCredentials.map((c) => (
                      <label key={c.id} className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-[13px]">
                        <input type="checkbox" checked={checked.has(c.id)} onChange={() => toggle(c.id)} className="h-4 w-4 accent-primary" />
                        {c.title}
                      </label>
                    ))}
                  </div>
                )}
                {applyError && (
                  <div className="mt-3 flex items-start gap-1.5 rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">
                    <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    {applyError}
                  </div>
                )}
                <Button variant="solid" className="mt-4 w-full" loading={applying} disabled={checked.size === 0} onClick={handleApply}>
                  Apply
                </Button>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
