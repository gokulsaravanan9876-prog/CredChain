import { cx } from '../../lib/utils'

/** Base shimmer block — compose the exported helpers below rather than using this directly in page code. */
function SkeletonBlock({ className }: { className?: string }) {
  return <div className={cx('animate-pulse rounded-md bg-white/8', className)} />
}

export function SkeletonText({ width = 'full', className }: { width?: 'full' | '3/4' | '1/2' | '1/4'; className?: string }) {
  const widthClass = { full: 'w-full', '3/4': 'w-3/4', '1/2': 'w-1/2', '1/4': 'w-1/4' }[width]
  return <SkeletonBlock className={cx('h-3.5', widthClass, className)} />
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-5">
      <SkeletonBlock className="h-4 w-1/3" />
      <div className="mt-4 space-y-2.5">
        {Array.from({ length: lines }).map((_, i) => (
          <SkeletonText key={i} width={i === lines - 1 ? '1/2' : 'full'} />
        ))}
      </div>
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-line bg-surface px-5 py-4">
      <SkeletonBlock className="h-9 w-9 shrink-0 rounded-lg" />
      <div className="flex-1 space-y-2">
        <SkeletonText width="1/2" />
        <SkeletonText width="1/4" />
      </div>
    </div>
  )
}

/** A grid of SkeletonCard, matching the common metric/list-card page layout. */
export function SkeletonGrid({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} lines={2} />
      ))}
    </div>
  )
}
