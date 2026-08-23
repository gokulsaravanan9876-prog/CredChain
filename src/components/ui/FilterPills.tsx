import { cx } from '../../lib/utils'

export function FilterPills<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[]
  value: T
  onChange: (v: T) => void
}) {
  return (
    <div className="inline-flex items-center gap-1 rounded-lg bg-canvas-2 p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={cx(
            'rounded-md px-3 py-1.5 text-xs font-semibold transition-colors',
            value === opt.value ? 'bg-primary text-white shadow-sm' : 'text-muted hover:text-ink'
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
