import { cx } from '../../lib/utils'

type GlowColor = 'primary' | 'ai' | 'cyan' | 'good' | 'magenta' | 'electric' | 'warn' | 'bad'

const COLOR_VAR: Record<GlowColor, string> = {
  primary: 'var(--color-primary)',
  ai: 'var(--color-ai)',
  cyan: 'var(--color-cyan)',
  good: 'var(--color-good)',
  magenta: 'var(--color-magenta)',
  electric: 'var(--color-electric)',
  warn: 'var(--color-warn)',
  bad: 'var(--color-bad)',
}

/**
 * A single ambient light source — a positioned, blurred radial-gradient
 * blob. The background engine (RoleBackground) and hero sections compose
 * a handful of these rather than each page inventing its own glow markup.
 */
export function Glow({
  color,
  size = 480,
  className,
  animate = true,
}: {
  color: GlowColor
  size?: number
  className?: string
  /** Ambient slow pulse — always gated behind motion-safe. */
  animate?: boolean
}) {
  return (
    <div
      aria-hidden
      className={cx(
        'pointer-events-none absolute rounded-full blur-3xl',
        animate && 'motion-safe:animate-[glowPulse_9s_ease-in-out_infinite]',
        className
      )}
      style={{
        width: size,
        height: size,
        background: `radial-gradient(circle, ${COLOR_VAR[color]} 0%, transparent 70%)`,
        opacity: 0.55,
      }}
    />
  )
}
