import { Link } from 'react-router-dom'
import type { Credential } from '../../../types'
import { Badge, Button, GlassPanel } from '../../../components/ui'
import { IconTile } from '../../../components/ui/IconTile'
import { CREDENTIAL_TYPE_ICON, credentialStatusTone, credentialStatusLabel } from '../../../lib/utils'

/**
 * Reproduces Stitch's "Digital Vault" credential card (my_credentials/code.html):
 * glass surface, huge faint watermark icon bottom-right, top row icon-tile +
 * status pill, title/subtitle/issuer stack, a divided bottom row (ISSUED year
 * left, an identifier right — Stitch shows a fake on-chain "TOKEN ID" there;
 * we show the credential's own real id, truncated, since no fabricated
 * on-chain token exists for an unanchored credential). Buttons are a real
 * addition Stitch's static mockup doesn't need but this interactive app does.
 */
export function CredentialCard({ credential, onShare }: { credential: Credential; onShare?: () => void }) {
  const Icon = CREDENTIAL_TYPE_ICON[credential.type]
  const shareHref = `/student/share?ids=${credential.id}`
  const shortId = credential.id.length > 12 ? `${credential.id.slice(0, 6)}…${credential.id.slice(-4)}` : credential.id
  return (
    <GlassPanel className="group relative overflow-hidden p-4 transition-transform duration-300 hover:-translate-y-1">
      <Icon
        aria-hidden
        className="pointer-events-none absolute -bottom-4 -right-4 h-28 w-28 rotate-[-12deg] text-white/[0.03]"
        strokeWidth={1}
      />
      <div className="relative mb-4 flex items-start justify-between">
        <IconTile icon={Icon} tone="neutral" size="sm" />
        <Badge tone={credentialStatusTone(credential.status)} size="sm">
          {credentialStatusLabel(credential.status)}
        </Badge>
      </div>
      <div className="relative">
        <h3 className="text-[15px] font-bold leading-snug text-primary">{credential.title}</h3>
        <p className="mt-1 text-xs text-muted">{credential.issuer}</p>
      </div>
      <div className="relative mt-4 flex items-end justify-between border-t border-white/5 pt-2.5">
        <div>
          <p className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-wider text-faint">Issued</p>
          <p className="font-[family-name:var(--font-mono)] text-[13px] text-ink">{credential.issuedDate}</p>
        </div>
        <div className="text-right">
          <p className="font-[family-name:var(--font-mono)] text-[10px] uppercase tracking-wider text-faint">Credential ID</p>
          <p className="font-[family-name:var(--font-mono)] text-[13px] text-cyan">{shortId}</p>
        </div>
      </div>
      <div className="relative mt-3 flex gap-2">
        <Link to={`/student/credentials/${credential.id}`} className="flex-1">
          <Button variant="outline" size="sm" className="w-full">
            View
          </Button>
        </Link>
        {onShare ? (
          <Button variant="solid" size="sm" className="flex-1" onClick={onShare}>
            Share
          </Button>
        ) : (
          <Link to={shareHref} className="flex-1">
            <Button variant="solid" size="sm" className="w-full">
              Share
            </Button>
          </Link>
        )}
      </div>
    </GlassPanel>
  )
}
