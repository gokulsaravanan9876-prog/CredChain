import type { LucideIcon } from 'lucide-react'
import { cx, TONE_CLASSES, type Tone } from '../../lib/utils'

const GLOW: Record<Tone, string> = {
  good: 'shadow-glow-good',
  warn: 'shadow-glow-warn',
  bad: 'shadow-glow-bad',
  primary: 'shadow-glow-primary',
  neutral: '',
}

export function Timeline({ children }: { children: React.ReactNode }) {
  return <div className="relative">{children}</div>
}

export function TimelineItem({
  icon: Icon,
  tone = 'primary',
  title,
  subtitle,
  timestamp,
  last = false,
}: {
  icon: LucideIcon
  tone?: Tone
  title: string
  subtitle?: string
  timestamp: string
  /** Omits the connecting line below the last item in a group. */
  last?: boolean
}) {
  return (
    <div className="relative flex gap-3.5 px-5 py-3.5">
      {!last && <span aria-hidden className="absolute left-[31px] top-11 bottom-0 w-px bg-line" />}
      <div className={cx('z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border', TONE_CLASSES[tone].border, TONE_CLASSES[tone].bg, GLOW[tone])}>
        <Icon className={cx('h-3.5 w-3.5', TONE_CLASSES[tone].text)} strokeWidth={2.25} />
      </div>
      <div className="flex min-w-0 flex-1 items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-ink">{title}</p>
          {subtitle && <p className="truncate text-xs text-faint">{subtitle}</p>}
        </div>
        <span className="shrink-0 text-xs text-faint">{timestamp}</span>
      </div>
    </div>
  )
}
