import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'
import { cx } from '../../lib/utils'

type ToastTone = 'good' | 'bad' | 'info'
type ToastItem = { id: number; message: string; tone: ToastTone }

const TOAST_ICON = { good: CheckCircle2, bad: XCircle, info: Info }
const TOAST_CLASSES: Record<ToastTone, string> = {
  good: 'border-good-line glass-surface text-ink [&_svg]:text-good',
  bad: 'border-bad-line glass-surface text-ink [&_svg]:text-bad',
  info: 'border-primary-line glass-surface text-ink [&_svg]:text-primary',
}

const ToastContext = createContext<((message: string, tone?: ToastTone) => void) | null>(null)

let nextId = 1

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const showToast = useCallback((message: string, tone: ToastTone = 'good') => {
    const id = nextId++
    setToasts((prev) => [...prev, { id, message, tone }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000)
  }, [])

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-[60] flex flex-col gap-2">
        {toasts.map((t) => {
          const Icon = TOAST_ICON[t.tone]
          return (
            <div
              key={t.id}
              role="status"
              className={cx(
                'pointer-events-auto flex items-center gap-2.5 rounded-xl border px-4 py-3 text-sm font-medium shadow-2xl shadow-black/50 motion-safe:animate-[toastIn_200ms_ease-out]',
                TOAST_CLASSES[t.tone]
              )}
            >
              <Icon className="h-4.5 w-4.5 shrink-0" strokeWidth={2.25} />
              <span>{t.message}</span>
              <button
                type="button"
                aria-label="Dismiss"
                onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
                className="ml-1 rounded p-0.5 text-faint hover:text-ink"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

/** Call as toast("Application submitted") or toast("Could not save changes", "bad"). */
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return ctx
}
