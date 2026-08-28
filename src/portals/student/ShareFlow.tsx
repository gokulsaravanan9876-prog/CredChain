import { useEffect, useMemo, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Building2, Eye, Download, Lock, Send } from 'lucide-react'
import { getCredentials, getStudentRequests, approveCredentialRequest, createDirectShare, getRealCompanies } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import type { Credential, BackendCredentialRequest, Company } from '../../types'
import { cx, CREDENTIAL_TYPE_ICON } from '../../lib/utils'

const EXPIRY_OPTIONS = [
  { value: 1, label: '1 day' },
  { value: 7, label: '7 days' },
  { value: 30, label: '30 days' },
] as const

/**
 * Reproduces the actual Stitch "share_credential_flow" screen: a page-back
 * link + "Secure Handoff" headline, a left obsidian-glass credential-preview
 * card (3D tilted document, ON-CHAIN/NOT ANCHORED badge, holder/issued/id
 * rows), and a right glass panel with an icon-prefixed recipient field, a
 * two-option bento "Access Protocol" selector, and a TTL control, ending in
 * a gradient "Sign & Generate Link" button — see
 * stitch2/share_credential_flow/code.html. Stitch previews exactly one
 * credential; this page lets a student select several (real functionality,
 * unchanged), so the preview card shows whichever credential is currently
 * checked first. Stitch's fictional "Stanford University" / "Alex Mercer" /
 * "0x7F...9A2C" and its "Zero-Knowledge Proofs" copy are replaced with real
 * data and an accurate description of what CredChain actually does
 * (Ed25519 signatures) — never Stitch's own fabricated claims.
 */
export function ShareFlow() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const requestId = params.get('requestId')
  const idsParam = params.get('ids')

  const [credentials, setCredentials] = useState<Credential[]>([])
  const [request, setRequest] = useState<BackendCredentialRequest | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [recipient, setRecipient] = useState('')
  const [companyId, setCompanyId] = useState('')
  const [expiry, setExpiry] = useState<number>(7)
  const [permission, setPermission] = useState<'view_only' | 'view_download'>('view_only')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getCredentials()
      .then(setCredentials)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Unable to load your credentials. Please try again.'))
    if (requestId) {
      getStudentRequests()
        .then((reqs) => {
          const r = reqs.find((x) => x.id === requestId) ?? null
          setRequest(r)
          if (r) setRecipient(r.company_name)
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : 'Unable to load this request. Please try again.'))
    } else {
      if (idsParam) setChecked(new Set(idsParam.split(',')))
      // Direct share: recipient must be a real, existing company — never free text.
      getRealCompanies()
        .then((cs) => {
          setCompanies(cs)
          if (cs.length > 0) setCompanyId(cs[0].id)
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : 'Unable to load companies. Please try again.'))
    }
  }, [requestId, idsParam])

  // Once both the request and the student's real credentials are loaded,
  // pre-check whichever of the student's credentials match a requested
  // label — the student can still freely toggle any of them (their own
  // full wallet is shown, not just the requested items) before approving.
  useEffect(() => {
    if (request && credentials.length > 0) {
      const matched = credentials.filter((c) =>
        request.requested_credentials.some((label) => c.title.toLowerCase().includes(label.toLowerCase()))
      )
      setChecked(new Set(matched.map((c) => c.id)))
    }
  }, [request, credentials])

  useEffect(() => {
    if (!requestId) {
      const c = companies.find((x) => x.id === companyId)
      setRecipient(c?.name ?? '')
    }
  }, [requestId, companyId, companies])

  const previewCredential = useMemo(() => credentials.find((c) => checked.has(c.id)) ?? null, [credentials, checked])
  const isAnchored = previewCredential?.blockchain?.status === 'anchored'

  function toggle(id: string) {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  async function handleSubmit() {
    setSubmitting(true)
    setError(null)
    try {
      if (requestId) {
        const result = await approveCredentialRequest(requestId, Array.from(checked), expiry, permission)
        navigate('/student/share/confirmation', {
          state: {
            recipient: result.share.company_name,
            count: result.share.credentials.length,
            expiry,
            permission,
            shareUrl: result.share_url,
            credentialTitles: result.share.credentials.map((c) => c.title),
          },
        })
      } else {
        const result = await createDirectShare(companyId, Array.from(checked), expiry, permission)
        navigate('/student/share/confirmation', {
          state: {
            recipient: result.share.company_name,
            count: result.share.credentials.length,
            expiry,
            permission,
            shareUrl: result.share_url,
            credentialTitles: result.share.credentials.map((c) => c.title),
          },
        })
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong while sharing.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative">
      <div aria-hidden className="pointer-events-none fixed -left-40 -top-40 -z-10 h-[500px] w-[500px] rounded-full bg-primary/10 blur-[120px]" />
      <div aria-hidden className="pointer-events-none fixed -bottom-40 -right-40 -z-10 h-[420px] w-[420px] rounded-full bg-cyan/10 blur-[100px]" />

      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-2 font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-muted transition-colors hover:text-primary"
        >
          <ArrowLeft className="h-3.5 w-3.5" strokeWidth={2.25} />
          Back to Vault
        </button>
        <h1 className="text-2xl font-bold tracking-tight text-ink font-[family-name:var(--font-display)] md:text-[32px]">Secure Handoff</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Configure cryptographic access parameters for credential sharing.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left: credential preview */}
        <div className="lg:col-span-5">
          <div className="glass-surface shadow-glow-primary relative overflow-hidden rounded-xl p-6">
            <div aria-hidden className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50" />

            {previewCredential ? (
              <>
                <div
                  className={cx(
                    'absolute right-4 top-4 flex items-center gap-1 rounded px-2 py-1 font-[family-name:var(--font-mono)] text-[10px] border',
                    isAnchored ? 'border-good/20 bg-good/10 text-good' : 'border-line-strong bg-surface-2 text-faint'
                  )}
                >
                  <span className={cx('h-1.5 w-1.5 rounded-full', isAnchored ? 'bg-good' : 'bg-faint')} />
                  {isAnchored ? 'ON-CHAIN' : 'NOT ANCHORED'}
                </div>

                <div className="relative z-10 mt-6 flex flex-col items-center text-center">
                  <div className="group mb-6 flex h-32 w-24 -rotate-6 flex-col justify-between rounded-md border border-white/10 bg-surface-2 p-2 shadow-lg transition-transform duration-500 hover:rotate-0">
                    <div className="mb-1 h-2 w-full rounded-full bg-white/20" />
                    <div className="mb-1 h-2 w-3/4 rounded-full bg-white/10" />
                    <div className="mb-auto h-2 w-5/6 rounded-full bg-white/10" />
                    {(() => {
                      const Icon = CREDENTIAL_TYPE_ICON[previewCredential.type]
                      return (
                        <div className="flex h-6 w-6 items-center justify-center self-end rounded-full border border-primary/50 bg-primary/40">
                          <Icon className="h-3.5 w-3.5 text-white" strokeWidth={2} />
                        </div>
                      )
                    })()}
                  </div>
                  <h3 className="text-lg font-semibold text-ink">{previewCredential.title}</h3>
                  <p className="mb-4 text-sm text-cyan">{previewCredential.issuer}</p>
                  <div className="my-4 h-px w-full bg-white/10" />
                  <div className="w-full space-y-3 text-left">
                    <div className="flex items-center justify-between">
                      <span className="font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">Holder</span>
                      <span className="font-[family-name:var(--font-mono)] text-[13px] text-ink">{previewCredential.issuedTo ? 'You' : '—'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">Issued</span>
                      <span className="font-[family-name:var(--font-mono)] text-[13px] text-ink">{previewCredential.issuedDate}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">ID</span>
                      <span className="rounded bg-black/50 px-2 py-1 font-[family-name:var(--font-mono)] text-[11px] text-ink">
                        {previewCredential.id.slice(0, 6)}...{previewCredential.id.slice(-4)}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="relative z-10 flex min-h-[280px] flex-col items-center justify-center gap-2 text-center">
                <p className="text-sm text-muted">Select a credential from the list to preview it here.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right: sharing controls */}
        <div className="lg:col-span-7">
          <div className="glass-surface shadow-glow-primary space-y-6 rounded-xl p-6">
            <div>
              <label className="mb-2 block font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">
                Recipient Identity
              </label>
              {requestId ? (
                <div className="flex items-center gap-3 rounded-lg border border-line bg-canvas px-4 py-3">
                  <Building2 className="h-5 w-5 shrink-0 text-faint" strokeWidth={2} />
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-ink">{recipient}</p>
                    {request && <p className="truncate text-xs text-muted">{request.purpose}</p>}
                  </div>
                </div>
              ) : companies.length === 0 ? (
                <p className="text-sm text-muted">{error ? 'Unable to load companies.' : 'No companies are registered on CredChain yet.'}</p>
              ) : (
                <div className="flex items-center gap-3 rounded-lg border border-line bg-canvas px-4 py-3 focus-within:border-electric">
                  <Building2 className="h-5 w-5 shrink-0 text-faint" strokeWidth={2} />
                  <select
                    value={companyId}
                    onChange={(e) => setCompanyId(e.target.value)}
                    className="w-full bg-transparent font-semibold text-ink outline-none"
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div>
              <label className="mb-2 block font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">
                Documents
              </label>
              <div className="space-y-2">
                {credentials.map((c) => {
                  const Icon = CREDENTIAL_TYPE_ICON[c.type]
                  const isChecked = checked.has(c.id)
                  return (
                    <label
                      key={c.id}
                      className={cx(
                        'flex cursor-pointer items-center gap-3 rounded-lg border px-3.5 py-3 transition-colors',
                        isChecked ? 'border-primary bg-primary/5' : 'border-line hover:bg-surface-2'
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggle(c.id)}
                        className="h-4 w-4 rounded border-line accent-primary"
                      />
                      <Icon className="h-4 w-4 text-muted" strokeWidth={2} />
                      <span className="text-sm font-medium text-ink">{c.title}</span>
                    </label>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="mb-2 block font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">
                Access Protocol
              </label>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {(
                  [
                    { value: 'view_only' as const, icon: Eye, title: 'View Only', description: 'The recipient can view this credential but cannot download the document.' },
                    { value: 'view_download' as const, icon: Download, title: 'View & Download', description: 'The recipient can view and download the original signed document.' },
                  ]
                ).map((opt) => {
                  const active = permission === opt.value
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setPermission(opt.value)}
                      className={cx(
                        'relative overflow-hidden rounded-lg border p-4 text-left transition-all',
                        active ? 'border-primary bg-primary/5' : 'border-line bg-surface-2/50 hover:bg-surface-2'
                      )}
                    >
                      {active && (
                        <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary shadow-glow-primary" />
                      )}
                      <opt.icon className={cx('mb-2 h-5 w-5', active ? 'text-primary' : 'text-muted')} strokeWidth={2} />
                      <p className="mb-1 text-sm font-semibold text-ink">{opt.title}</p>
                      <p className="text-[12px] text-muted">{opt.description}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-end justify-between">
                <label className="font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-faint">
                  Time to Live (TTL)
                </label>
              </div>
              <div className="flex gap-2">
                {EXPIRY_OPTIONS.map((opt) => {
                  const active = expiry === opt.value
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setExpiry(opt.value)}
                      className={cx(
                        'flex-1 rounded-lg border px-3 py-2 font-[family-name:var(--font-mono)] text-[12px] font-semibold transition-colors',
                        active ? 'border-cyan-line bg-cyan-bg text-cyan' : 'border-line text-muted hover:bg-surface-2'
                      )}
                    >
                      {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="rounded-lg bg-primary-bg px-4 py-3 text-[13px] text-primary">
              You are sharing {checked.size} credential{checked.size === 1 ? '' : 's'}.{' '}
              {recipient || 'This recipient'} will not receive your other credentials.
            </div>

            {error && <div className="rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">{error}</div>}

            <div className="pt-1">
              <button
                type="button"
                disabled={checked.size === 0 || (requestId ? !recipient : !companyId) || submitting}
                onClick={handleSubmit}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-br from-primary to-primary-dark py-3.5 text-[15px] font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] transition-opacity hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : (
                  <Send className="h-4 w-4" strokeWidth={2.25} />
                )}
                Sign &amp; Generate Link
              </button>
              <p className="mt-3 flex items-center justify-center gap-1 text-center text-[12px] text-muted">
                <Lock className="h-3 w-3" strokeWidth={2.25} />
                Secured by Ed25519 digital signatures
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
