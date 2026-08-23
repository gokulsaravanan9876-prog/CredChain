import { useLocation, useNavigate, Link, Navigate } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { CheckCircle2, Copy, Eye, X, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { GlassPanel } from '../../components/ui'

interface LocationState {
  recipient: string
  count: number
  expiry: number
  permission?: 'view_only' | 'view_download'
  /** Always the real, backend-issued share URL — every path that reaches this page creates a real ShareGrant. */
  shareUrl: string
  credentialTitles?: string[]
}

const PERMISSION_LABEL: Record<'view_only' | 'view_download', string> = {
  view_only: 'View Only',
  view_download: 'View & Download',
}

/**
 * Reproduces the actual Stitch "share_confirmation" screen: a centered
 * transactional card (no nav chrome) with a gradient headline, a QR frame
 * with a faint shield watermark behind it, a 2x2 "TO / PERMISSION / EXPIRES"
 * meta grid, then one primary "Copy Link" action and two secondary actions
 * — see stitch2/share_confirmation/code.html. Stitch's own reference
 * hardcodes "Google HR Dept" / "View Only" / "Oct 26, 2023"; every one of
 * those slots below uses the real recipient/permission/expiry that produced
 * this real, backend-issued share.
 */
export function ShareConfirmation() {
  const { state } = useLocation() as { state: LocationState | null }
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)

  // No fabricated fallback link — if this page is reached without a real
  // backend-issued shareUrl (e.g. a direct visit, not via a real share
  // creation), there is nothing honest to show, so redirect back.
  if (!state?.shareUrl) {
    return <Navigate to="/student/shares" replace />
  }

  const { recipient, count, expiry, shareUrl, permission } = state
  const expiresOn = new Date(Date.now() + expiry * 24 * 60 * 60 * 1000).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      // Clipboard access can fail (permissions/insecure context) — the link is still visible and selectable.
    }
  }

  return (
    <div className="relative flex min-h-[calc(100vh-4rem)] items-center justify-center py-8">
      <div aria-hidden className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[420px] w-[420px] rounded-full bg-good/10 blur-[110px]" />
      </div>

      <GlassPanel glow className="relative z-10 flex w-full max-w-md flex-col items-center p-7 text-center motion-safe:animate-[fadeIn_500ms_ease-out]">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-good/30 bg-good/10 shadow-[0_0_20px_rgba(78,222,163,0.2)]">
          <CheckCircle2 className="h-9 w-9 text-good" strokeWidth={1.75} />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-transparent font-[family-name:var(--font-display)] bg-gradient-to-r from-primary to-cyan bg-clip-text">
          Credential Shared
        </h1>
        <p className="mt-1.5 text-sm text-muted">
          Scan to securely verify {count === 1 ? 'this credential' : `these ${count} credentials`}.
        </p>

        {state.credentialTitles && state.credentialTitles.length > 0 && (
          <div className="mt-4 w-full space-y-1.5 text-left">
            {state.credentialTitles.map((title) => (
              <div key={title} className="rounded-lg border border-line bg-canvas-2/40 px-3.5 py-2 text-sm font-medium text-ink">
                {title}
              </div>
            ))}
          </div>
        )}

        {/* QR frame with faint shield watermark */}
        <div className="relative mt-6 rounded-xl border border-white/5 bg-surface p-4 shadow-glow-primary">
          <div aria-hidden className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.05]">
            <ShieldCheck className="h-32 w-32 text-primary" strokeWidth={1.5} />
          </div>
          <div className="relative z-10 flex h-48 w-48 items-center justify-center rounded-lg bg-white">
            <QRCodeSVG value={shareUrl} size={176} fgColor="#0F1729" />
          </div>
        </div>

        {/* Meta grid — real recipient / permission / expiry */}
        <div className="mt-6 grid w-full grid-cols-2 gap-2.5">
          <div className="rounded-lg border border-line bg-surface-2/60 p-3 text-left">
            <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">To</p>
            <p className="truncate font-[family-name:var(--font-mono)] text-[13px] text-primary">{recipient}</p>
          </div>
          <div className="rounded-lg border border-line bg-surface-2/60 p-3 text-left">
            <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">Permission</p>
            <p className="font-[family-name:var(--font-mono)] text-[13px] text-primary">{permission ? PERMISSION_LABEL[permission] : '—'}</p>
          </div>
          <div className="col-span-2 rounded-lg border border-line bg-surface-2/60 p-3 text-left">
            <p className="mb-1 font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-[0.1em] text-faint">Expires</p>
            <p className="font-[family-name:var(--font-mono)] text-[13px] text-primary">{expiresOn}</p>
          </div>
        </div>

        {/* Raw link, kept visible/selectable in case the clipboard call is unavailable */}
        <p className="mt-3 w-full truncate rounded-lg border border-line bg-canvas-2/60 px-3 py-2 text-left text-xs text-muted">{shareUrl}</p>

        <div className="mt-6 flex w-full flex-col gap-2.5">
          <button
            type="button"
            onClick={copyLink}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-br from-primary to-primary-dark py-3 text-[15px] font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] transition-opacity hover:opacity-90"
          >
            <Copy className="h-4 w-4" strokeWidth={2.25} />
            {copied ? 'Copied' : 'Copy Link'}
          </button>
          <div className="flex w-full gap-2.5">
            <a
              href={shareUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-cyan-line bg-cyan-bg py-3 text-sm font-semibold text-cyan transition-colors hover:bg-cyan-bg/70"
            >
              <Eye className="h-4 w-4" strokeWidth={2.25} />
              View Share
            </a>
            <button
              type="button"
              onClick={() => navigate('/student')}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-line bg-surface-2 py-3 text-sm font-semibold text-ink transition-colors hover:bg-surface"
            >
              <X className="h-4 w-4" strokeWidth={2.25} />
              Close
            </button>
          </div>
        </div>

        <Link to="/student/shares" className="mt-4 text-xs font-semibold text-muted hover:text-primary hover:underline">
          View all my shares
        </Link>
      </GlassPanel>
    </div>
  )
}
