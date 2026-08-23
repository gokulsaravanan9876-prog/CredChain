import type { LucideIcon } from 'lucide-react'
import { cx } from '../../lib/utils'

export interface FlowStep {
  icon: LucideIcon
  label: string
  description: string
}

/**
 * Illuminated node + connecting line primitive for lifecycle/journey
 * visualizations — the Landing "Issue -> Own -> Share -> Verify" story, and
 * reusable anywhere else a step sequence needs the same treatment (kept
 * generic on purpose rather than one-off per page).
 */
export function ConnectionFlow({ steps, className }: { steps: FlowStep[]; className?: string }) {
  return (
    <div className={cx('grid grid-cols-1 gap-0 sm:grid-cols-4', className)}>
      {steps.map((step, i) => (
        <div key={step.label} className="relative flex flex-col items-center px-2 text-center sm:items-center">
          {i < steps.length - 1 && (
            <div
              aria-hidden
              className="absolute left-1/2 top-7 hidden h-px w-full bg-gradient-to-r from-primary/60 via-ai/40 to-transparent sm:block"
            />
          )}
          <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-2xl border border-primary-line bg-primary-bg shadow-[0_0_24px_-6px_var(--color-primary)]">
            <step.icon className="h-6 w-6 text-primary" strokeWidth={2} />
          </div>
          <p className="mt-3 text-sm font-bold text-ink">{step.label}</p>
          <p className="mt-1 max-w-[15rem] text-xs leading-relaxed text-muted">{step.description}</p>
        </div>
      ))}
    </div>
  )
}
