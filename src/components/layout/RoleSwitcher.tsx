import { useNavigate, useLocation } from 'react-router-dom'
import { GraduationCap, Building2, ShieldCheck } from 'lucide-react'
import { cx } from '../../lib/utils'
import type { Role } from '../../types'

const OPTIONS: { role: Role; label: string; icon: typeof GraduationCap; to: string }[] = [
  { role: 'student', label: 'Student', icon: GraduationCap, to: '/student' },
  { role: 'institution', label: 'Institution', icon: Building2, to: '/institution' },
  { role: 'verifier', label: 'Verifier', icon: ShieldCheck, to: '/verifier' },
]

/**
 * DEV ONLY — a route-jump shortcut, not authentication. It never grants a
 * session: with real auth in place (Phase 3), navigating to another role's
 * portal while logged in just bounces straight back to your own dashboard
 * via ProtectedRoute, and navigating while logged out bounces to /login.
 * There is no code path from clicking this button to "become another role."
 * Rendered only in dev builds (import.meta.env.DEV) — see App.tsx.
 */
export function RoleSwitcher() {
  const navigate = useNavigate()
  const location = useLocation()
  const activeRole = location.pathname.startsWith('/institution')
    ? 'institution'
    : location.pathname.startsWith('/verifier')
    ? 'verifier'
    : 'student'

  return (
    <div className="fixed bottom-4 right-4 z-50 flex items-center gap-1 rounded-full border border-white/10 bg-ink-9 px-1.5 py-1.5 shadow-lg shadow-black/40">
      <span className="pl-2 pr-1 text-[10px] font-bold uppercase tracking-wider text-white/40">Dev nav</span>
      {OPTIONS.map((opt) => {
        const active = opt.role === activeRole
        return (
          <button
            key={opt.role}
            onClick={() => navigate(opt.to)}
            className={cx(
              'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-colors',
              active ? 'bg-primary text-white' : 'text-white/70 hover:text-white'
            )}
          >
            <opt.icon className="h-3.5 w-3.5" strokeWidth={2.25} />
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
