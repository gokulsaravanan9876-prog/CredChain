import { useState } from 'react'
import { CheckCircle2, XCircle, ShieldAlert, Lock, Clock, HelpCircle, AlertTriangle, Download, ShieldCheck, Info } from 'lucide-react'
import type { BundleVerificationResult } from '../../../types'
import { Button, GlassPanel } from '../../../components/ui'
import { CREDENTIAL_TYPE_ICON } from '../../../lib/utils'
import { VerificationBlockchainProof } from '../../../components/blockchain/BlockchainProof'
import { viewSharedCredentialDocument, downloadSharedCredentialDocument } from '../../../lib/api'
import { ApiError } from '../../../lib/apiClient'

function openBlobInNewTab(blob: Blob) {
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

/** Icon + color + Stitch-exact copy per status. Deliberately mirrors the wording on the
 * three real Stitch reference screens ("CREDENTIAL VERIFIED", "CREDENTIAL REVOKED", the
 * mismatch screen's amber framing) rather than inventing new labels. */
const STATUS_CONFIG = {
  VERIFIED: { icon: ShieldCheck, color: 'text-good', ring: 'border-good/30', glowRgb: '78,222,163', label: 'CREDENTIAL VERIFIED', sub: 'This credential passed all required authenticity and integrity checks.' },
  INVALID: { icon: XCircle, color: 'text-bad', ring: 'border-bad/30', glowRgb: '248,113,113', label: 'CREDENTIAL INVALID', sub: 'This credential failed cryptographic verification against the issuer’s trusted record.' },
  REVOKED: { icon: ShieldAlert, color: 'text-bad', ring: 'border-bad/30', glowRgb: '248,113,113', label: 'CREDENTIAL REVOKED', sub: 'The issuing institution has revoked this credential since it was signed.' },
  EXPIRED: { icon: Clock, color: 'text-warn', ring: 'border-warn/30', glowRgb: '245,165,36', label: 'ACCESS EXPIRED', sub: 'This share link or grant has expired as of the institution’s records.' },
  UNAUTHORIZED: { icon: Lock, color: 'text-bad', ring: 'border-bad/30', glowRgb: '248,113,113', label: 'UNAUTHORIZED', sub: 'Your organization does not have authorized access to this credential.' },
  NOT_FOUND: { icon: HelpCircle, color: 'text-muted', ring: 'border-line', glowRgb: '136,145,168', label: 'NOT FOUND', sub: 'No credential was found for this request.' },
  TYPE_MISMATCH: { icon: AlertTriangle, color: 'text-warn', ring: 'border-warn/30', glowRgb: '245,165,36', label: 'CREDENTIAL TYPE MISMATCH', sub: 'This credential is genuine, but it is not the type that was requested.' },
} as const

/**
 * Reproduces the actual Stitch "verification_report_verified" /
 * "_mismatch" / "_revoked" screens: a large glowing icon-medallion hero with
 * an uppercase display headline, a "Verification Sequence" connected
 * timeline (checkmark-node + gradient line, one card per real check with a
 * PASSED/FAILED mono chip), then a distinct "Blockchain Proof" section — see
 * the stitch2 verification_report_(verified|mismatch|revoked)/code.html trio. Stitch's own reference hardcodes
 * "Stanford University" as the issuer step and a fake local hash; every
 * status-chip and detail below reads only from the real `result` prop.
 * Stitch's mismatch screen also contains a fabricated free-text "AI
 * Analysis" sentence explaining the mismatch — the real backend result has
 * no such field, so that callout is built from the real requested/received
 * values only, never invented prose.
 */
export function ResultCard({ result }: { result: BundleVerificationResult }) {
  const cfg = STATUS_CONFIG[result.status]
  const Icon = cfg.icon

  const [busyId, setBusyId] = useState<string | null>(null)
  const [docError, setDocError] = useState<string | null>(null)

  async function handleView(credentialId: string) {
    setBusyId(`view:${credentialId}`)
    setDocError(null)
    try {
      openBlobInNewTab(await viewSharedCredentialDocument(credentialId))
    } catch (err) {
      setDocError(err instanceof ApiError ? err.message : 'Could not open this document.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDownload(credentialId: string) {
    setBusyId(`download:${credentialId}`)
    setDocError(null)
    try {
      openBlobInNewTab(await downloadSharedCredentialDocument(credentialId))
    } catch (err) {
      // A view_only grant gets a real 403 here — the button being visible
      // and the backend rejecting it IS the enforcement, not a bug.
      setDocError(err instanceof ApiError ? err.message : 'Could not download this document.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      {/* Hero — Stitch's atmospheric glowing-medallion status card */}
      <div
        className="relative overflow-hidden rounded-2xl border p-8 text-center md:p-12"
        style={{
          background: 'rgba(10,15,30,0.6)',
          backdropFilter: 'blur(20px)',
          borderColor: `rgba(${cfg.glowRgb},0.25)`,
          boxShadow: `0px 20px 60px -15px rgba(${cfg.glowRgb},0.15)`,
        }}
      >
        <div aria-hidden className="pointer-events-none absolute left-1/2 top-0 h-64 w-[120%] -translate-x-1/2 rounded-full blur-[100px]" style={{ background: `rgba(${cfg.glowRgb},0.12)` }} />
        <div className="relative z-10 mx-auto mb-4 flex h-32 w-32 items-center justify-center">
          <div aria-hidden className="absolute inset-0 animate-pulse rounded-full blur-2xl" style={{ background: `rgba(${cfg.glowRgb},0.25)` }} />
          <div className={`absolute inset-2 rounded-full border bg-gradient-to-b from-surface-2 to-canvas ${cfg.ring}`} style={{ boxShadow: `inset 0 0 20px rgba(${cfg.glowRgb},0.25)` }} />
          <Icon className={`relative h-16 w-16 ${cfg.color}`} strokeWidth={1.5} style={{ filter: `drop-shadow(0 0 18px rgba(${cfg.glowRgb},0.7))` }} />
        </div>
        <h1 className={`relative z-10 text-2xl font-extrabold uppercase tracking-tight ${cfg.color} font-[family-name:var(--font-display)] md:text-[32px]`}>
          {cfg.label}
        </h1>
        <p className="relative z-10 mx-auto mt-2 max-w-md text-sm text-muted">{cfg.sub}</p>

        {result.status === 'VERIFIED' && result.credentials.length > 0 && (
          <div className="relative z-10 mt-6 flex flex-wrap justify-center gap-2">
            {result.credentials.map((c) => {
              const Icon2 = CREDENTIAL_TYPE_ICON[c.type]
              return (
                <div key={c.id} className="flex flex-wrap justify-center gap-2">
                  <Button variant="outline" size="sm" icon={<Icon2 className="h-3.5 w-3.5" />} loading={busyId === `view:${c.id}`} onClick={() => handleView(c.id)}>
                    View {c.title}
                  </Button>
                  <Button variant="outline" size="sm" icon={<Download className="h-3.5 w-3.5" />} loading={busyId === `download:${c.id}`} onClick={() => handleDownload(c.id)}>
                    Download
                  </Button>
                </div>
              )
            })}
          </div>
        )}
        {docError && <p className="relative z-10 mx-auto mt-3 max-w-xs text-[12px] text-bad">{docError}</p>}
      </div>

      {/* Type-mismatch / tamper detail — real requested-vs-received data only, no fabricated AI prose */}
      {result.status === 'TYPE_MISMATCH' && (
        <GlassPanel className="p-5">
          <div className="mb-3 flex items-center gap-2 text-warn">
            <AlertTriangle className="h-4 w-4" strokeWidth={2.25} />
            <p className="text-sm font-bold uppercase tracking-wider">Type Analysis</p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-line bg-canvas-2/50 p-3">
              <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-faint">Requested Payload</p>
              <p className="text-sm font-semibold text-ink">{result.requestedCredentials?.join(', ') ?? '—'}</p>
            </div>
            <div className="rounded-lg border border-warn-line bg-warn-bg p-3">
              <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-warn">Received On-Chain</p>
              <p className="text-sm font-semibold text-warn">{result.credentials[0]?.title ?? '—'}</p>
            </div>
          </div>
        </GlassPanel>
      )}

      {result.status === 'INVALID' && result.tamperDiff && (
        <GlassPanel className="p-5">
          <div className="mb-3 flex items-center gap-2 text-bad">
            <XCircle className="h-4 w-4" strokeWidth={2.25} />
            <p className="text-sm font-bold uppercase tracking-wider">Tamper Detected</p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-line bg-canvas-2/50 p-3">
              <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-faint">Original trusted {result.tamperDiff.field}</p>
              <p className="text-sm font-semibold text-ink">{result.tamperDiff.original}</p>
            </div>
            <div className="rounded-lg border border-bad-line bg-bad-bg p-3">
              <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-bad">Presented document</p>
              <p className="text-sm font-semibold text-bad">{result.tamperDiff.presented}</p>
            </div>
          </div>
        </GlassPanel>
      )}

      {/* Verification Sequence — Stitch's connected checkmark timeline, built from the real result.checks array */}
      {result.checks.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-base font-semibold text-ink">Verification Sequence</h2>
          <GlassPanel className="p-5">
            <div className="relative flex flex-col gap-5 pl-1">
              {result.checks.length > 1 && (
                <div
                  aria-hidden
                  className="absolute left-[19px] top-8 bottom-8 w-[2px] rounded-full"
                  style={{ background: `linear-gradient(to bottom, rgba(${cfg.glowRgb},0.5), rgba(${cfg.glowRgb},0.1))` }}
                />
              )}
              {result.checks.map((c) => (
                <div key={c.label} className="relative z-10 flex items-start gap-3.5">
                  <div
                    className={cxTone(c.passed)}
                    style={{ boxShadow: c.passed ? '0 0 15px rgba(78,222,163,0.3)' : '0 0 15px rgba(248,113,113,0.3)' }}
                  >
                    {c.passed ? <CheckCircle2 className="h-5 w-5 text-good" strokeWidth={2} /> : <XCircle className="h-5 w-5 text-bad" strokeWidth={2} />}
                  </div>
                  <div className="flex-1 rounded-lg border border-white/5 bg-canvas-2/40 p-3">
                    <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">{c.label}</p>
                    <div className="flex flex-wrap items-center gap-2">
                      {c.description && <p className="text-[13px] font-medium text-ink">{c.description}</p>}
                      <span
                        className={cx2(c.passed)}
                      >
                        {c.passed ? 'PASSED' : 'FAILED'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </GlassPanel>
        </div>
      )}

      {/* Blockchain Proof — always the real, honest state from VerificationBlockchainProof; never fabricated */}
      {result.blockchain && (
        <div className="flex flex-col gap-3">
          <h2 className="text-base font-semibold text-ink">Blockchain Proof</h2>
          <GlassPanel className="overflow-hidden p-0">
            <div className="p-5">
              <VerificationBlockchainProof blockchain={result.blockchain} />
            </div>
          </GlassPanel>
        </div>
      )}

      <div className="mx-auto flex items-center gap-2 rounded-full border border-line bg-canvas-2/50 px-3.5 py-2 text-[11px] font-medium text-muted">
        <Info className="h-3.5 w-3.5 text-primary" strokeWidth={2} />
        Verified by CredChain
      </div>
    </div>
  )
}

function cxTone(passed: boolean): string {
  return `flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 bg-surface-2 ${passed ? 'border-good/60' : 'border-bad/60'}`
}
function cx2(passed: boolean): string {
  return `rounded border px-2 py-0.5 font-[family-name:var(--font-mono)] text-[11px] ${
    passed ? 'border-good/20 bg-good/10 text-good' : 'border-bad/20 bg-bad/10 text-bad'
  }`
}
