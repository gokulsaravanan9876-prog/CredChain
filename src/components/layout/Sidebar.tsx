import { NavLink } from 'react-router-dom'
import { ShieldCheck, X } from 'lucide-react'
import { NAV_CONFIG } from './nav.config'
import { cx } from '../../lib/utils'
import type { Role } from '../../types'

function NavRow({ item, badge, onNavigate }: { item: (typeof NAV_CONFIG)['student']['primary'][number]; badge?: number; onNavigate?: () => void }) {
  return (
    <NavLink
      to={item.to}
      end={item.to.split('/').length <= 2}
      onClick={onNavigate}
      className={({ isActive }) =>
        cx(
          'group relative flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
          isActive ? 'bg-primary-bg text-primary shadow-[0_0_0_1px_var(--color-primary-line)_inset]' : 'text-muted hover:bg-surface-2 hover:text-ink'
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && <span className="absolute -left-3 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-primary shadow-[0_0_8px_var(--color-primary)]" />}
          <span className="flex items-center gap-2.5">
            <item.icon className={cx('h-4 w-4', isActive ? 'text-primary' : 'text-faint group-hover:text-muted')} strokeWidth={2} />
            {item.label}
          </span>
          {!!badge && (
            <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-white shadow-glow-primary">
              {badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

export function Sidebar({
  role,
  orgName,
  badges,
  mobileOpen = false,
  onMobileClose,
}: {
  role: Role
  orgName?: string
  badges?: Record<string, number>
  /** Below the lg breakpoint the sidebar renders as an off-canvas drawer instead of a static column. */
  mobileOpen?: boolean
  onMobileClose?: () => void
}) {
  const nav = NAV_CONFIG[role]
  return (
    <>
      {mobileOpen && (
        <div
          aria-hidden
          onClick={onMobileClose}
          className="fixed inset-0 z-30 bg-black/70 motion-safe:animate-[fadeIn_150ms_ease-out] lg:hidden"
        />
      )}
      <aside
        className={cx(
          'relative z-10 flex h-full w-60 shrink-0 flex-col border-r border-line glass-surface transition-transform duration-200',
          'fixed inset-y-0 left-0 z-40 lg:static lg:translate-x-0',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
      <div className="flex h-16 items-center gap-2.5 border-b border-line px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-ai text-white shadow-[0_0_16px_-2px_var(--color-primary)]">
          <ShieldCheck className="h-4 w-4" strokeWidth={2.5} />
        </div>
        <span className="text-[15px] font-bold tracking-tight text-ink font-[family-name:var(--font-display)]">CredChain</span>
        <button
          type="button"
          onClick={onMobileClose}
          aria-label="Close navigation"
          className="ml-auto rounded-lg p-1 text-faint hover:bg-surface-2 hover:text-ink lg:hidden"
        >
          <X className="h-4.5 w-4.5" strokeWidth={2.25} />
        </button>
      </div>

      {orgName && (
        <div className="px-5 pb-1 pt-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-faint">{orgName}</span>
        </div>
      )}

      <nav className={cx('flex-1 space-y-0.5 px-3', orgName ? 'pt-2' : 'pt-4')}>
        {nav.primary.map((item) => (
          <NavRow key={item.to} item={item} badge={badges?.[item.to]} onNavigate={onMobileClose} />
        ))}
      </nav>

      {nav.secondary.length > 0 && (
        <div className="space-y-0.5 border-t border-line px-3 py-3">
          {nav.secondary.map((item) => (
            <NavRow key={item.to} item={item} badge={badges?.[item.to]} onNavigate={onMobileClose} />
          ))}
        </div>
      )}
      </aside>
    </>
  )
}
