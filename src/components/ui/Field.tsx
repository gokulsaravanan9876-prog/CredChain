import type { ReactNode } from 'react'

export function Field({
  label,
  hint,
  error,
  required,
  children,
}: {
  label: string
  /** Short helper text under the label, e.g. "Applicants below this value are marked not eligible." */
  hint?: string
  error?: string | null
  required?: boolean
  children: ReactNode
}) {
  return (
    <label className="block">
      <span className="text-[13px] font-semibold text-ink">
        {label}
        {required && <span className="ml-0.5 text-bad">*</span>}
      </span>
      {hint && <span className="mt-0.5 block text-[12px] leading-relaxed text-muted">{hint}</span>}
      <div className="mt-1.5">{children}</div>
      {error && <span className="mt-1 block text-[12px] font-medium text-bad">{error}</span>}
    </label>
  )
}
