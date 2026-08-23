import { AlertTriangle } from 'lucide-react'
import { Button } from './Button'

export function ErrorState({
  title = 'Something went wrong',
  description,
  action,
  onRetry,
}: {
  title?: string
  description: string
  action?: React.ReactNode
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-bad-line bg-bad-bg px-6 py-8 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface">
        <AlertTriangle className="h-5 w-5 text-bad" strokeWidth={2} />
      </div>
      <div>
        <p className="text-sm font-bold text-ink">{title}</p>
        <p className="mt-1 max-w-sm text-[13px] leading-relaxed text-body">{description}</p>
      </div>
      {action ?? (onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ))}
    </div>
  )
}
