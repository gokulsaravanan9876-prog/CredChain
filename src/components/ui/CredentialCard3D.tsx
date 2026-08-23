import { ShieldCheck } from 'lucide-react'
import { cx } from '../../lib/utils'

/**
 * The one coherent 3D motif reused across Landing hero, auth worlds, Student
 * Dashboard hero, and Credential Detail hero: a floating glass "credential
 * passport" card built from CSS 3D transforms (perspective + rotate), a
 * metallic gradient edge, and a soft ambient float — no 3D engine, no
 * texture assets. Content is passed as props so real data can drive it on
 * dashboard/detail pages while marketing chrome (Landing) can use
 * illustrative-but-generic labels.
 */
export function CredentialCard3D({
  issuer,
  title,
  subtitle,
  checks = ['Issuer Verified', 'Signature Valid', 'Integrity Verified', 'Active Credential'],
  size = 'md',
  className,
}: {
  issuer: string
  title: string
  subtitle?: string
  checks?: string[]
  size?: 'sm' | 'md' | 'lg'
  className?: string
}) {
  const dims = { sm: 'w-64 h-40', md: 'w-80 h-48', lg: 'w-96 h-56' }[size]
  return (
    <div className={cx('perspective-1000', className)}>
      <div
        className={cx(
          'preserve-3d relative rounded-2xl border border-white/15 bg-gradient-to-br from-surface-2/90 via-surface/80 to-canvas-2/90 p-5 shadow-2xl shadow-black/60',
          'motion-safe:animate-[floatCard_7s_ease-in-out_infinite]',
          dims
        )}
        style={{
          backgroundImage:
            'linear-gradient(135deg, rgba(109,90,251,0.14), rgba(167,139,250,0.10) 40%, rgba(34,211,238,0.08) 100%)',
          boxShadow: '0 0 0 1px rgba(255,255,255,0.06) inset, 0 30px 60px -20px rgba(0,0,0,0.65)',
        }}
      >
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-white/70">CredChain</span>
          <ShieldCheck className="h-4 w-4 text-cyan" strokeWidth={2.25} />
        </div>
        <div className="mt-4">
          <p className="text-lg font-bold leading-tight text-white font-[family-name:var(--font-display)]">{title}</p>
          {subtitle && <p className="text-xs text-white/60">{subtitle}</p>}
          <p className="mt-1 text-[11px] font-semibold uppercase tracking-wider text-white/50">{issuer}</p>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-x-3 gap-y-1">
          {checks.map((c) => (
            <span key={c} className="flex items-center gap-1 text-[10px] font-medium text-emerald-300/90">
              <span className="h-1 w-1 shrink-0 rounded-full bg-good shadow-[0_0_6px_var(--color-good)]" />
              {c}
            </span>
          ))}
        </div>
        {/* metallic edge highlight */}
        <div className="pointer-events-none absolute inset-0 rounded-2xl border border-white/10" />
        <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-tr from-transparent via-white/5 to-transparent" />
      </div>
    </div>
  )
}
