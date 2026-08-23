import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import type { User } from '../../types'
import { getNotificationCounts } from '../../lib/api'
import { RoleBackground } from '../ui/RoleBackground'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

/** Maps this role's real notification counts onto the nav item `to` paths that should show them. */
function badgesForRole(role: User['role'], counts: Awaited<ReturnType<typeof getNotificationCounts>>): Record<string, number> {
  const badges: Record<string, number> = {}
  if (role === 'student' && counts.pending_company_requests) badges['/student/requests'] = counts.pending_company_requests
  if (role === 'institution') {
    if (counts.pending_certificate_requests) badges['/institution/certificate-requests'] = counts.pending_certificate_requests
    if (counts.pending_document_reviews) badges['/institution/documents'] = counts.pending_document_reviews
  }
  if (role === 'verifier' && counts.new_job_applications) badges['/verifier/applications'] = counts.new_job_applications
  return badges
}

export function AppShell({ user, children }: { user: User; children: React.ReactNode }) {
  const [badges, setBadges] = useState<Record<string, number>>({})
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    getNotificationCounts()
      .then((counts) => setBadges(badgesForRole(user.role, counts)))
      .catch(() => {})
    // Re-fetch on navigation so a badge clears right after the user acts (approve/reject/verify) and returns to the list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.role, location.pathname])

  // A route change (including one triggered by a sidebar nav click) always closes the mobile drawer.
  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  return (
    <div className="flex h-screen w-full overflow-hidden bg-canvas">
      <Sidebar
        role={user.role}
        orgName={user.orgName}
        badges={badges}
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
      />
      <div className="relative flex min-w-0 flex-1 flex-col">
        <TopBar user={user} onMenuClick={() => setMobileNavOpen(true)} />
        <div className="relative flex-1 overflow-hidden">
          {/* One shared ambient background engine, tinted per role — see RoleBackground for the
              palette-per-world mapping. Gives every authenticated page the same visual universe. */}
          <RoleBackground role={user.role} />
          <main className="scrollbar-thin relative h-full overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-7">{children}</main>
        </div>
      </div>
    </div>
  )
}
