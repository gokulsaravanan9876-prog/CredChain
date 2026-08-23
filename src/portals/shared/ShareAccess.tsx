import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ShieldCheck, Lock, FileText } from 'lucide-react'
import { accessShareByToken, verifyCredential, viewSharedCredentialDocument, downloadSharedCredentialDocument } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import { useAuth } from '../../context/AuthContext'
import type { ShareTokenAccessResult, VerifyCredentialResponse } from '../../types'
import { Button, Badge, GlassPanel, RoleBackground } from '../../components/ui'
import { SkeletonCard } from '../../components/ui/Skeleton'

function openBlobInNewTab(blob: Blob) {
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

/**
 * Public route (no auth required to load) — the unguessable share token
 * itself is the authorization mechanism, matching a normal share-link/QR
 * pattern. Stitch has no dedicated mockup for this exact recipient-facing
 * page, so it borrows the two closest Stitch reference treatments: the
 * centered "transactional card, no nav chrome" composition and mono-label
 * meta grid from share_confirmation/code.html, and the honest
 * not-yet-verified framing from verification_report_verified/code.html —
 * this page previews what was shared (GET /api/shares/verify/{token});
 * actually proving a credential is authentic still requires the viewer to
 * be signed in as the specific company the share was created for, which
 * runs the real verification call (POST /api/verification/verify).
 */
export function ShareAccess() {
  const { token } = useParams<{ token: string }>()
  const { user } = useAuth()

  const [preview, setPreview] = useState<ShareTokenAccessResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, VerifyCredentialResponse>>({})
  const [verifyingId, setVerifyingId] = useState<string | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    accessShareByToken(token)
      .then(setPreview)
      .catch((err) => setPreviewError(err instanceof ApiError ? err.message : 'Could not load this share.'))
      .finally(() => setLoading(false))
  }, [token])

  async function handleVerify(credentialId: string) {
    setVerifyingId(credentialId)
    setVerifyError(null)
    try {
      const result = await verifyCredential(credentialId)
      setResults((prev) => ({ ...prev, [credentialId]: result }))
    } catch (err) {
      setVerifyError(err instanceof ApiError ? err.message : 'Verification failed.')
    } finally {
      setVerifyingId(null)
    }
  }

  async function handleView(credentialId: string) {
    setBusyId(credentialId)
    setVerifyError(null)
    try {
      openBlobInNewTab(await viewSharedCredentialDocument(credentialId))
    } catch (err) {
      setVerifyError(err instanceof ApiError ? err.message : 'Could not open this document.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDownload(credentialId: string) {
    setBusyId(credentialId)
    setVerifyError(null)
    try {
      openBlobInNewTab(await downloadSharedCredentialDocument(credentialId))
    } catch (err) {
      // The backend returns a real 403 here when the grant is view_only —
      // this is the enforcement, not just a hidden button.
      setVerifyError(err instanceof ApiError ? err.message : 'Could not download this document.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4 py-10">
      <RoleBackground role="landing" />
      <div aria-hidden className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[420px] w-[420px] rounded-full bg-primary/10 blur-[110px]" />
      </div>

      <GlassPanel glow className="relative z-10 w-full max-w-lg p-7">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-ai text-white shadow-glow-primary">
            <ShieldCheck className="h-6 w-6" strokeWidth={2.25} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-ink font-[family-name:var(--font-display)]">CredChain</h1>
          <p className="mt-1 font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.1em] text-cyan">
            Secure Verification Portal
          </p>
        </div>

        {loading && <SkeletonCard lines={3} />}

        {!loading && previewError && (
          <div className="rounded-xl border border-bad-line bg-bad-bg/40 p-6 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-bad-bg">
              <Lock className="h-6 w-6 text-bad" strokeWidth={1.75} />
            </div>
            <p className="text-sm font-semibold text-bad">{previewError}</p>
            <p className="mt-1 text-xs text-muted">This link may have expired or been revoked by the student.</p>
          </div>
        )}

        {!loading && preview && (
          <>
            {/* Real recipient / permission / expiry meta grid — mirrors the
                mono-label treatment used on ShareConfirmation, built from real
                accessShareByToken() response fields only. */}
            <div className="mb-5 grid grid-cols-2 gap-2.5">
              <div className="col-span-2 rounded-lg border border-line bg-surface-2/60 p-3 text-left">
                <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">Granted To</p>
                <p className="truncate text-sm font-semibold text-ink">{preview.company_name}</p>
              </div>
              <div className="rounded-lg border border-line bg-surface-2/60 p-3 text-left">
                <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">Access</p>
                <p className="font-[family-name:var(--font-mono)] text-[13px] text-primary">
                  {preview.permission === 'view_download' ? 'View & Download' : 'View Only'}
                </p>
              </div>
              <div className="rounded-lg border border-line bg-surface-2/60 p-3 text-left">
                <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">Expires</p>
                <p className="font-[family-name:var(--font-mono)] text-[13px] text-primary">
                  {new Date(preview.expires_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
                </p>
              </div>
            </div>

            {verifyError && <div className="mb-4 rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">{verifyError}</div>}

            <div className="space-y-2.5">
              {preview.credentials.map((c) => {
                const result = results[c.id]
                return (
                  <div key={c.id} className="rounded-lg border border-line bg-canvas-2/40 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-2 text-muted">
                          <FileText className="h-4.5 w-4.5" strokeWidth={2} />
                        </div>
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-ink">{c.title}</p>
                          <p className="truncate text-xs text-muted">{c.institution_name}</p>
                        </div>
                      </div>
                      {result ? (
                        <Badge tone={result.result === 'VERIFIED' ? 'good' : result.result === 'TYPE_MISMATCH' ? 'warn' : 'bad'} size="sm">
                          {result.result.replace(/_/g, ' ')}
                        </Badge>
                      ) : user?.role === 'verifier' ? (
                        <Button size="sm" variant="solid" loading={verifyingId === c.id} onClick={() => handleVerify(c.id)}>
                          Verify
                        </Button>
                      ) : (
                        <Link to="/login" state={{ from: `/share/verify/${token}` }} className="shrink-0 text-xs font-semibold text-primary hover:underline">
                          Sign in to verify
                        </Link>
                      )}
                    </div>
                    {user?.role === 'verifier' && (
                      <div className="mt-3 flex gap-2">
                        <Button size="sm" variant="outline" loading={busyId === c.id} onClick={() => handleView(c.id)}>
                          View
                        </Button>
                        {preview.permission === 'view_download' && (
                          <Button size="sm" variant="outline" loading={busyId === c.id} onClick={() => handleDownload(c.id)}>
                            Download
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </>
        )}
      </GlassPanel>
    </div>
  )
}
