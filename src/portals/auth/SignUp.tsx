import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate, Link } from 'react-router-dom'
import { ShieldCheck, Search, Mail, KeyRound, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { ApiError } from '../../lib/apiClient'
import { getInstitutions } from '../../lib/api'
import { Button, RoleBackground, CredentialCard3D } from '../../components/ui'
import { Select } from '../../components/ui/Input'
import type { Role, RegisterPayload, InstitutionSummary } from '../../types'
import { cx } from '../../lib/utils'

const ROLE_HOME: Record<Role, string> = {
  student: '/student',
  institution: '/institution',
  verifier: '/verifier',
}

const ROLE_TABS: { role: Role; label: string }[] = [
  { role: 'student', label: 'Student' },
  { role: 'institution', label: 'Institution' },
  { role: 'verifier', label: 'Company' },
]

const WORLD_COPY: Record<Role, { headline: string; sub: string }> = {
  student: { headline: 'Your academic identity belongs to you.', sub: 'Every credential you receive lands directly in your own wallet — you decide what gets shared, with whom, and for how long.' },
  institution: { headline: 'Issue credentials people can trust.', sub: 'Sign transcripts, degrees, and certificates with your institution’s own key — every issuance is auditable and tamper-evident.' },
  verifier: { headline: 'Verify talent with confidence.', sub: 'Check a candidate’s real, signed academic record in seconds — no phone calls, no waiting on a registrar.' },
}

/**
 * Reproduces the actual Stitch "credchain_cinematic_auth_portal" screen: a
 * centered logo/tagline header, a pill-shaped "tactile switch" role selector,
 * and one glass-panel-3d "Access Portal" card with icon-prefixed recessed
 * inputs — all in a single view, not a two-step "pick a card, then see a
 * form" flow (see stitch1/credchain_cinematic_auth_portal/code.html). `role`
 * now defaults to 'student' instead of being nullable, matching Stitch's
 * always-a-role-selected interaction model; `register()` and its payload
 * construction are unchanged. The real per-role background/CredentialCard3D
 * "world" pairing built in an earlier phase is kept (genuine, working
 * functionality Stitch's own single auth screen doesn't need to express,
 * since Stitch's reference is mobile-only and has no room for it) — restyled
 * to sit behind the same centered composition rather than a desktop split.
 */
export function SignUp() {
  const { user, register } = useAuth()
  const navigate = useNavigate()

  const [role, setRole] = useState<Role>('student')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [studentIdentifier, setStudentIdentifier] = useState('')
  const [institutions, setInstitutions] = useState<InstitutionSummary[]>([])
  const [institutionId, setInstitutionId] = useState('')
  const [institutionSearch, setInstitutionSearch] = useState('')
  const [institutionName, setInstitutionName] = useState('')
  const [institutionRegistrationNumber, setInstitutionRegistrationNumber] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [companyIndustry, setCompanyIndustry] = useState('')
  const [companyWebsite, setCompanyWebsite] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [institutionsLoading, setInstitutionsLoading] = useState(false)
  const [institutionsError, setInstitutionsError] = useState<string | null>(null)

  // Debounced, backend-searched (not a client-side filter over a fixed snapshot — the directory
  // now holds 10,000+ real institutions, so only the matching page is ever fetched). Mirrors the
  // debounce pattern already used by the full Institutions directory page.
  useEffect(() => {
    if (role !== 'student') return
    const handle = setTimeout(() => {
      setInstitutionsLoading(true)
      setInstitutionsError(null)
      getInstitutions({ search: institutionSearch.trim() || undefined })
        .then(setInstitutions)
        .catch((err) => setInstitutionsError(err instanceof ApiError ? err.message : 'Could not load institutions.'))
        .finally(() => setInstitutionsLoading(false))
    }, 300)
    return () => clearTimeout(handle)
  }, [role, institutionSearch])

  if (user) return <Navigate to={ROLE_HOME[user.role]} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    const payload: RegisterPayload = { email, password, full_name: fullName, role }
    if (role === 'student') {
      payload.student_identifier = studentIdentifier
      if (institutionId) payload.institution_id = institutionId
    }
    if (role === 'institution') {
      payload.institution_name = institutionName
      if (institutionRegistrationNumber) payload.institution_registration_number = institutionRegistrationNumber
    }
    if (role === 'verifier') {
      payload.company_name = companyName
      if (companyIndustry) payload.company_industry = companyIndustry
      if (companyWebsite) payload.company_website = companyWebsite
    }

    try {
      let registeredUser
      try {
        registeredUser = await register(payload)
      } catch (err) {
        // A status-0 ApiError means fetch() itself never got a response — a one-off network
        // blip, not a real backend failure. One retry avoids a false "Server unavailable" for
        // an account creation attempt that would otherwise have succeeded a moment later.
        if (err instanceof ApiError && err.status === 0) {
          registeredUser = await register(payload)
        } else {
          throw err
        }
      }
      navigate(ROLE_HOME[registeredUser.role], { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 0) setError('Server unavailable. Please try again in a moment.')
        else if (err.status === 409) setError('An account with this email already exists.')
        else if (err.status === 422) setError('Please check that all required fields are filled in correctly.')
        else setError('Something went wrong. Please try again.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const copy = WORLD_COPY[role]

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-canvas px-5 py-16">
      <RoleBackground key={role} role={role} className="motion-safe:animate-[fadeIn_600ms_ease-out]" />
      <div aria-hidden className="pointer-events-none absolute inset-0 bg-grid-faint opacity-[0.05]" />

      <main className="relative z-10 flex w-full max-w-lg flex-col items-center">
        <div className="mb-8 flex flex-col items-center text-center">
          <h1 className="flex items-center justify-center gap-2 text-[32px] font-bold tracking-tight text-primary drop-shadow-[0_0_15px_rgba(79,70,229,0.4)] font-[family-name:var(--font-display)]">
            <ShieldCheck className="h-9 w-9" strokeWidth={2.25} />
            CredChain
          </h1>
          <p className="mt-2 text-base tracking-wide text-cyan opacity-80">Create your account</p>
        </div>

        {/* Pill role switcher — Stitch's "tactile switch" */}
        <div className="mb-6 flex w-full rounded-full border border-line bg-canvas p-1 shadow-[inset_0_2px_5px_rgba(0,0,0,0.6)]">
          {ROLE_TABS.map((tab) => (
            <button
              key={tab.role}
              type="button"
              onClick={() => setRole(tab.role)}
              className={cx(
                'flex-1 rounded-full px-4 py-2 text-[13px] font-semibold transition-all duration-300',
                role === tab.role
                  ? 'bg-gradient-to-b from-cyan-bg to-transparent text-cyan shadow-[0_0_20px_-4px_var(--color-cyan)] [text-shadow:0_0_10px_rgba(76,215,246,0.6)]'
                  : 'text-faint hover:text-ink'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Access Portal card */}
        <div className="glass-surface w-full rounded-2xl p-6">
          <div className="mb-4 flex items-center gap-3">
            <CredentialCard3D issuer={role === 'institution' ? 'Your Institution' : role === 'verifier' ? 'Talent Network' : 'VITC'} title={ROLE_TABS.find((t) => t.role === role)!.label} subtitle="CredChain account" size="sm" className="hidden sm:block" />
            <div>
              <h2 className="text-xl font-semibold text-ink">Access Portal</h2>
              <p className="text-[13px] leading-relaxed text-muted">{copy.headline}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <RecessedField label={role === 'institution' || role === 'verifier' ? 'Contact Name' : 'Name'} icon={User}>
              <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required autoComplete="name" className="w-full bg-transparent text-sm text-ink outline-none" />
            </RecessedField>

            <RecessedField label={role === 'institution' ? 'Official Email' : role === 'verifier' ? 'Business Email' : 'Email'} icon={Mail}>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" className="w-full bg-transparent text-sm text-ink outline-none" />
            </RecessedField>

            <RecessedField label="Password" icon={KeyRound}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                className="w-full bg-transparent text-sm tracking-[0.2em] text-ink outline-none"
              />
            </RecessedField>

            {role === 'student' && (
              <>
                <RecessedField label="Student Identifier" icon={User}>
                  <input type="text" value={studentIdentifier} onChange={(e) => setStudentIdentifier(e.target.value)} required className="w-full bg-transparent text-sm text-ink outline-none" />
                </RecessedField>

                <div className="flex flex-col gap-1.5">
                  <label className="ml-1 text-[11px] font-medium uppercase tracking-[0.1em] text-faint">Institution (optional — link later)</label>
                  <div className="flex items-center gap-3 rounded-xl border border-line bg-canvas px-4 py-3 shadow-[inset_0_4px_10px_rgba(0,0,0,0.5)]">
                    <Search className="h-[18px] w-[18px] shrink-0 text-faint" strokeWidth={2} />
                    <input
                      value={institutionSearch}
                      onChange={(e) => setInstitutionSearch(e.target.value)}
                      placeholder="Search institutions"
                      className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-faint"
                    />
                  </div>
                  <Select value={institutionId} onChange={(e) => setInstitutionId(e.target.value)} className="mt-1">
                    <option value="">No institution selected</option>
                    {institutions.map((i) => (
                      <option key={i.id} value={i.id}>
                        {i.name}
                      </option>
                    ))}
                  </Select>
                  {institutionsLoading && <p className="ml-1 text-[12px] text-faint">Searching institutions…</p>}
                  {!institutionsLoading && !institutionsError && institutionSearch.trim() && institutions.length === 0 && (
                    <p className="ml-1 text-[12px] text-faint">No institutions matched "{institutionSearch.trim()}" — you can still create your account and link one later.</p>
                  )}
                  {institutionsError && <p className="ml-1 text-[12px] text-bad">{institutionsError} — you can still create your account and link one later.</p>}
                </div>
              </>
            )}

            {role === 'institution' && (
              <>
                <RecessedField label="Institution Name" icon={User}>
                  <input type="text" value={institutionName} onChange={(e) => setInstitutionName(e.target.value)} required className="w-full bg-transparent text-sm text-ink outline-none" />
                </RecessedField>
                <RecessedField label="Registration Number (optional)" icon={User}>
                  <input type="text" value={institutionRegistrationNumber} onChange={(e) => setInstitutionRegistrationNumber(e.target.value)} className="w-full bg-transparent text-sm text-ink outline-none" />
                </RecessedField>
              </>
            )}

            {role === 'verifier' && (
              <>
                <RecessedField label="Company Name" icon={User}>
                  <input type="text" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required className="w-full bg-transparent text-sm text-ink outline-none" />
                </RecessedField>
                <RecessedField label="Industry (optional)" icon={User}>
                  <input type="text" value={companyIndustry} onChange={(e) => setCompanyIndustry(e.target.value)} className="w-full bg-transparent text-sm text-ink outline-none" />
                </RecessedField>
                <RecessedField label="Website (optional)" icon={User}>
                  <input type="text" value={companyWebsite} onChange={(e) => setCompanyWebsite(e.target.value)} className="w-full bg-transparent text-sm text-ink outline-none" />
                </RecessedField>
              </>
            )}

            {error && (
              <div role="alert" className="rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">
                {error}
              </div>
            )}

            <Button type="submit" variant="solid" className="mt-2 w-full rounded-xl py-3.5 text-base" loading={submitting}>
              Create Account
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-muted">
          Already have an account?{' '}
          <Link to="/sign-in" className="font-semibold text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </main>
    </div>
  )
}

function RecessedField({ label, icon: Icon, children }: { label: string; icon: typeof User; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="ml-1 text-[11px] font-medium uppercase tracking-[0.1em] text-faint">{label}</label>
      <div className="flex items-center gap-3 rounded-xl border border-line bg-canvas px-4 py-3 shadow-[inset_0_4px_10px_rgba(0,0,0,0.5)] transition-colors focus-within:border-electric focus-within:shadow-[inset_0_4px_10px_rgba(0,0,0,0.5),0_0_20px_-6px_var(--color-electric)]">
        <Icon className="h-[18px] w-[18px] shrink-0 text-faint" strokeWidth={2} />
        {children}
      </div>
    </div>
  )
}
