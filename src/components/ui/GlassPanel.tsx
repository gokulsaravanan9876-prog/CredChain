import type { HTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

/**
 * The base dark/glass surface every premium panel builds on — translucent
 * blurred background, subtle gradient-tinted border, soft depth shadow.
 * `Card` stays the plain flat surface for dense list/table contexts; reach
 * for `GlassPanel` on hero sections, AI panels, and anything that should
 * read as "floating" rather than "flat."
 */
export function GlassPanel({ className, glow = false, ...rest }: HTMLAttributes<HTMLDivElement> & { glow?: boolean }) {
  return (
    <div
      className={cx(
        'glass-surface rounded-2xl shadow-2xl shadow-black/40',
        glow && 'shadow-[0_0_60px_-20px_var(--color-primary)]',
        className
      )}
      {...rest}
    />
  )
}
