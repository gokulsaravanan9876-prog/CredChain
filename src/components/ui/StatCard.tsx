import type { LucideIcon } from 'lucide-react'
import { Card } from './Card'
import { cx, TONE_CLASSES, type Tone } from '../../lib/utils'

/** neutral renders in ink (not the neutral-tone gray) — a stat's headline number should read as primary content, not a muted status. */
const STAT_TEXT: Record<Tone, string> = {
  neutral: 'text-ink',
  good: TONE_CLASSES.good.text,
  warn: TONE_CLASSES.warn.text,
  bad: TONE_CLASSES.bad.text,
  primary: TONE_CLASSES.primary.text,
}

/** A faint tone-colored left accent — gives each metric its own identity at a glance
 * (Stitch: dashboard stat cards carry a colored rail matching their status). */
const STAT_RAIL: Record<Tone, string> = {
  neutral: 'border-l-line-strong',
  good: 'border-l-good',
  warn: 'border-l-warn',
  bad: 'border-l-bad',
  primary: 'border-l-primary',
}

/** Icon-chip tint per tone — mirrors Stitch's bento metric cards (icon in a translucent
 * tone-colored chip, top-left, above the value rather than beside it). */
const STAT_CHIP: Record<Tone, string> = {
  neutral: 'bg-line-strong/40 text-muted',
  good: cx(TONE_CLASSES.good.bg, TONE_CLASSES.good.text),
  warn: cx(TONE_CLASSES.warn.bg, TONE_CLASSES.warn.text),
  bad: cx(TONE_CLASSES.bad.bg, TONE_CLASSES.bad.text),
  primary: cx(TONE_CLASSES.primary.bg, TONE_CLASSES.primary.text),
}

export function StatCard({
  value,
  label,
  tone = 'neutral',
  icon: Icon,
  /** Small pulsing dot in the top-right corner — Stitch uses this on a metric that represents
   * something new/unread (e.g. incoming requests). Purely presentational; caller decides when. */
  pulse = false,
}: {
  value: number | string
  label: string
  tone?: Tone
  icon?: LucideIcon
  pulse?: boolean
}) {
  return (
    <Card className={cx('flex h-[132px] flex-col justify-between border-l-[3px] p-4', STAT_RAIL[tone])}>
      <div className="flex items-start justify-between">
        {Icon && (
          <div className={cx('flex h-8 w-8 items-center justify-center rounded-lg', STAT_CHIP[tone])}>
            <Icon className="h-4 w-4" strokeWidth={2} />
          </div>
        )}
        {pulse && (
          <span className="relative flex h-2.5 w-2.5">
            <span className={cx('absolute inline-flex h-full w-full animate-ping rounded-full opacity-75', STAT_TEXT[tone].replace('text-', 'bg-'))} />
            <span className={cx('relative inline-flex h-2.5 w-2.5 rounded-full', STAT_TEXT[tone].replace('text-', 'bg-'))} />
          </span>
        )}
      </div>
      <div>
        <div className={cx('text-2xl font-bold tabular-nums font-[family-name:var(--font-display)]', STAT_TEXT[tone])}>{value}</div>
        <div className="mt-0.5 text-sm text-muted">{label}</div>
      </div>
    </Card>
  )
}
