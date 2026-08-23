import type { ButtonHTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

type Variant = 'solid' | 'outline' | 'ghost' | 'danger' | 'accent' | 'success'
type Size = 'sm' | 'md'

/** Stitch: primary CTAs use a 45deg Indigo->Violet gradient with a subtle inner top-edge
 * glow and a diffused colored "glow shadow" (never a plain black shadow). Secondary/ghost
 * stay dark-glass. Cyan (accent) and Emerald (success) cover the two remaining semantic
 * actions Stitch's button set defines (crypto-status affirmations, verified confirmations). */
const VARIANT_CLASSES: Record<Variant, string> = {
  solid:
    'bg-gradient-to-br from-primary to-ai text-white border border-white/10 shadow-[0_0_0_1px_rgba(255,255,255,0.08)_inset,0_10px_28px_-8px_rgba(79,70,229,0.55)] hover:brightness-110 hover:-translate-y-px',
  outline: 'bg-surface text-ink border border-line hover:border-line-strong hover:bg-surface-2',
  ghost: 'bg-transparent text-muted hover:text-ink hover:bg-surface-2 border border-transparent',
  danger: 'bg-surface text-bad border border-bad-line hover:bg-bad-bg hover:border-bad',
  accent:
    'bg-transparent text-cyan border border-cyan-line backdrop-blur-md hover:bg-cyan-bg shadow-[0_0_20px_-8px_var(--color-cyan)]',
  success:
    'bg-gradient-to-br from-good to-good text-canvas border border-white/10 shadow-[0_10px_24px_-8px_rgba(78,222,163,0.45)] hover:brightness-110',
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: React.ReactNode
  loading?: boolean
}

export function Button({ variant = 'outline', size = 'md', icon, loading, className, children, disabled, ...rest }: Props) {
  return (
    <button
      className={cx(
        'inline-flex items-center justify-center gap-1.5 rounded-lg font-semibold transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:brightness-100',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className
      )}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        icon
      )}
      {children}
    </button>
  )
}
