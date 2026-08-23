import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Inbox, UserSearch, Briefcase, FileCheck2 } from 'lucide-react'
import { sendCredentialRequest } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import { PageHeader, Button } from '../../components/ui'

const CREDENTIAL_OPTIONS = ['Degree', 'Transcript', 'Migration Certificate', 'Internship Certificate']

/**
 * No dedicated Stitch screen exists for this form — per this task's own
 * instruction, it inherits the "Access Portal" glass-card language already
 * established in src/portals/auth/Login.tsx (recessed icon-prefixed inputs,
 * inset shadow, electric-blue focus glow, gradient 3D submit button) rather
 * than a generic dashboard form.
 */
export function RequestCredentials() {
  const navigate = useNavigate()
  const [studentIdentifier, setStudentIdentifier] = useState('')
  const [purpose, setPurpose] = useState('Software Engineer Application')
  const [selected, setSelected] = useState<Set<string>>(new Set(['Degree', 'Transcript']))
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function toggle(title: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(title)) {
        next.delete(title)
      } else {
        next.add(title)
      }
      return next
    })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await sendCredentialRequest({
        studentIdentifier: studentIdentifier.trim(),
        purpose,
        requestedCredentials: Array.from(selected),
      })
      navigate('/verifier')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not send this request.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <PageHeader title="Request Credentials" eyebrow="Credential Requests" icon={Inbox} description="Ask a candidate to share specific credentials for review." />

      <div className="glass-surface w-full max-w-lg rounded-2xl p-6">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="studentIdentifier" className="ml-1 text-[11px] font-medium uppercase tracking-[0.1em] text-faint">
              Student Identifier
            </label>
            <div className="flex items-center gap-3 rounded-xl border border-line bg-canvas px-4 py-3 shadow-[inset_0_4px_10px_rgba(0,0,0,0.5)] transition-colors focus-within:border-electric focus-within:shadow-[inset_0_4px_10px_rgba(0,0,0,0.5),0_0_20px_-6px_var(--color-electric)]">
              <UserSearch className="h-[20px] w-[20px] shrink-0 text-faint" strokeWidth={2} />
              <input
                id="studentIdentifier"
                value={studentIdentifier}
                onChange={(e) => setStudentIdentifier(e.target.value)}
                placeholder="Ask the candidate for their CredChain student identifier"
                required
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-faint"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="purpose" className="ml-1 text-[11px] font-medium uppercase tracking-[0.1em] text-faint">
              Application / Role
            </label>
            <div className="flex items-center gap-3 rounded-xl border border-line bg-canvas px-4 py-3 shadow-[inset_0_4px_10px_rgba(0,0,0,0.5)] transition-colors focus-within:border-electric focus-within:shadow-[inset_0_4px_10px_rgba(0,0,0,0.5),0_0_20px_-6px_var(--color-electric)]">
              <Briefcase className="h-[20px] w-[20px] shrink-0 text-faint" strokeWidth={2} />
              <input
                id="purpose"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                required
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-faint"
              />
            </div>
          </div>

          <div>
            <label className="mb-1.5 ml-1 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.1em] text-faint">
              <FileCheck2 className="h-3.5 w-3.5" strokeWidth={2} />
              Credentials to Request
            </label>
            <div className="space-y-2">
              {CREDENTIAL_OPTIONS.map((title) => (
                <label
                  key={title}
                  className="flex cursor-pointer items-center gap-3 rounded-xl border border-line bg-canvas px-4 py-3 shadow-[inset_0_4px_10px_rgba(0,0,0,0.5)] transition-colors hover:border-line-strong"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(title)}
                    onChange={() => toggle(title)}
                    className="h-4 w-4 rounded border-line accent-primary"
                  />
                  <span className="text-sm font-medium text-ink">{title}</span>
                </label>
              ))}
            </div>
          </div>

          {error && <div className="rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">{error}</div>}

          <Button type="submit" variant="solid" className="mt-2 w-full rounded-xl py-3.5 text-base" loading={submitting} disabled={selected.size === 0}>
            Send Request
          </Button>
        </form>
      </div>
    </div>
  )
}
