import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, ReactNode } from 'react'
import { cx } from '../../lib/utils'

/** Stitch: field backgrounds are Deep Black with a Midnight Navy border; on focus the
 * border glows Electric Blue. Deliberately distinct from the Indigo `--color-primary`
 * focus ring used on non-field interactive elements. */
const FIELD_BASE =
  'w-full rounded-lg border border-line bg-canvas-2 px-3.5 py-2.5 text-sm text-ink outline-none transition-colors placeholder:text-faint focus:border-electric focus:ring-2 focus:ring-cyan-bg disabled:cursor-not-allowed disabled:bg-canvas disabled:text-muted'

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cx(FIELD_BASE, className)} {...rest} />
}

export function Textarea({ className, ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cx(FIELD_BASE, 'resize-y', className)} {...rest} />
}

export function Select({
  className,
  children,
  ...rest
}: SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }) {
  return (
    <select className={cx(FIELD_BASE, className)} {...rest}>
      {children}
    </select>
  )
}
