import type { HTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

type CardVariant = 'surface' | 'feature'

const VARIANT_CLASSES: Record<CardVariant, string> = {
  /** Stitch "Level 1 — bordered dark surface": the default, dense/list-context card. */
  surface: 'border-line bg-surface',
  /** Stitch "feature gradient surface": a subtle indigo->violet tinted wash for a card
   * that should read as a highlighted/featured item among plainer surface cards
   * (not a replacement for GlassPanel's blurred Level-2 float treatment). */
  feature: 'border-primary-line bg-gradient-to-br from-primary-bg via-surface to-surface',
}

export function Card({ className, variant = 'surface', ...rest }: HTMLAttributes<HTMLDivElement> & { variant?: CardVariant }) {
  return (
    <div
      className={cx('rounded-xl border', VARIANT_CLASSES[variant], className)}
      {...rest}
    />
  )
}
