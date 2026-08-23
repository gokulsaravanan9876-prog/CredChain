import { Check, X, AlertTriangle } from 'lucide-react'
import { cx, TONE_CLASSES } from '../../lib/utils'

const STATE_ICON = { pass: Check, fail: X, gap: AlertTriangle }
/** pass/fail/gap map onto the shared good/bad/warn status tones — same colors as Badge, StatCard, everywhere else a status renders. */
const STATE_TONE = { pass: 'good', fail: 'bad', gap: 'warn' } as const

export function CheckRow({
  label,
  state,
  description,
  size = 'md',
  bordered = false,
}: {
  label: string
  state: 'pass' | 'fail' | 'gap'
  /** Optional one-line explanation shown under the label — used by the verification-checks checklist. */
  description?: string
  size?: 'sm' | 'md'
  /** Tinted bordered row (Stitch "MATCH/MISSING" card treatment) — used by eligibility/AI-match lists where each check should read as its own evidence card, not just an inline line. */
  bordered?: boolean
}) {
  const Icon = STATE_ICON[state]
  const tone = TONE_CLASSES[STATE_TONE[state]]
  return (
    <div
      className={cx(
        'flex items-start gap-2.5',
        bordered && cx('rounded-lg border px-3 py-2.5', tone.border, tone.bg)
      )}
    >
      <Icon className={cx(size === 'sm' ? 'h-4 w-4' : 'h-[18px] w-[18px]', tone.text, 'mt-0.5 shrink-0')} strokeWidth={2.75} />
      <div>
        <div className={cx(size === 'sm' ? 'text-[13px]' : 'text-sm', 'font-medium text-body')}>{label}</div>
        {description && <div className="mt-0.5 text-[13px] leading-relaxed text-muted">{description}</div>}
      </div>
    </div>
  )
}
