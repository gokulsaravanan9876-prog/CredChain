import type { LucideIcon } from 'lucide-react'
import { cx, TONE_CLASSES } from '../../lib/utils'

/** Surface tone (what visual "material" the tile is), not status tone — good/warn/bad reuse the same status colors as Badge/StatCard/CheckRow for status-icon tiles (e.g. a verification-check row). */
export type IconTileTone = 'neutral' | 'primary' | 'ai' | 'ink' | 'good' | 'warn' | 'bad'

export function IconTile({
  icon: Icon,
  tone = 'neutral',
  size = 'md',
}: {
  icon: LucideIcon
  tone?: IconTileTone
  size?: 'sm' | 'md'
}) {
  const toneClasses = {
    neutral: 'bg-surface-2 text-muted border border-line',
    primary: 'bg-primary-bg text-primary',
    ai: 'bg-ai-bg text-ai',
    ink: 'bg-gradient-to-br from-primary to-ai text-white shadow-[0_0_0_1px_rgba(255,255,255,0.08)_inset]',
    good: cx(TONE_CLASSES.good.bg, TONE_CLASSES.good.text),
    warn: cx(TONE_CLASSES.warn.bg, TONE_CLASSES.warn.text),
    bad: cx(TONE_CLASSES.bad.bg, TONE_CLASSES.bad.text),
  }[tone]
  const sizeClasses = size === 'sm' ? 'h-8 w-8 rounded-lg' : 'h-10 w-10 rounded-xl'
  const iconSize = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'
  return (
    <div className={cx('flex shrink-0 items-center justify-center', sizeClasses, toneClasses)}>
      <Icon className={iconSize} strokeWidth={2} />
    </div>
  )
}

export function InitialsAvatar({
  initials,
  size = 'md',
  tone = 'ink',
}: {
  initials: string
  size?: 'sm' | 'md'
  tone?: 'ink' | 'primary'
}) {
  const sizeClasses = size === 'sm' ? 'h-8 w-8 text-[11px] rounded-lg' : 'h-9 w-9 text-xs rounded-lg'
  const toneClasses = tone === 'ink' ? 'bg-gradient-to-br from-primary to-ai text-white' : 'bg-primary-bg text-primary'
  return (
    <div className={cx('flex shrink-0 items-center justify-center font-bold', sizeClasses, toneClasses)}>
      {initials}
    </div>
  )
}
