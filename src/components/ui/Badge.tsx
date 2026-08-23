import { Check, X, Clock, Sparkles } from 'lucide-react'
import { cx, TONE_CLASSES } from '../../lib/utils'

type Tone = 'good' | 'warn' | 'bad' | 'neutral' | 'primary'

const ICONS = { good: Check, warn: Clock, bad: X, neutral: null, primary: Sparkles }

export function Badge({
  tone,
  children,
  withIcon = true,
  size = 'md',
}: {
  tone: Tone
  children: React.ReactNode
  withIcon?: boolean
  size?: 'sm' | 'md'
}) {
  const t = TONE_CLASSES[tone]
  const Icon = ICONS[tone]
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-full border font-semibold whitespace-nowrap',
        t.bg,
        t.text,
        t.border,
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'
      )}
    >
      {withIcon && Icon && <Icon className={size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'} strokeWidth={2.75} />}
      {children}
    </span>
  )
}
