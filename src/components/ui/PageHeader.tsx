import type { LucideIcon } from 'lucide-react'
import { IconTile, type IconTileTone } from './IconTile'

export function PageHeader({
  title,
  description,
  eyebrow,
  icon,
  tone = 'primary',
  action,
}: {
  title: string
  description?: string
  /** Small uppercase label above the title, e.g. "Academic Passport", "Trust & Verification" — gives every page a contextual identity without a full hero. */
  eyebrow?: string
  icon?: LucideIcon
  tone?: IconTileTone
  action?: React.ReactNode
}) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div className="flex items-start gap-3.5">
        {icon && (
          <div className="mt-0.5 hidden sm:block">
            <IconTile icon={icon} tone={tone} />
          </div>
        )}
        <div>
          {eyebrow && <p className="mb-1 text-[11px] font-bold uppercase tracking-wider text-primary">{eyebrow}</p>}
          <h1 className="text-2xl font-bold tracking-tight text-ink">{title}</h1>
          {description && <p className="mt-1 text-sm text-muted">{description}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
