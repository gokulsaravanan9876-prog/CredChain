import { Search } from 'lucide-react'
import { cx } from '../../lib/utils'
import type { InputHTMLAttributes } from 'react'

export function SearchInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className={cx('relative', className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-faint" strokeWidth={2} />
      <input
        type="text"
        className="w-full rounded-lg border border-line bg-canvas-2/60 py-2 pl-9 pr-3 text-sm text-ink placeholder:text-faint outline-none focus:border-primary focus:bg-surface focus:ring-2 focus:ring-primary-bg"
        {...rest}
      />
    </div>
  )
}
