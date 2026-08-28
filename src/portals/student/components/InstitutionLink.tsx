import { useEffect, useState } from 'react'
import { Landmark } from 'lucide-react'
import { useAuth } from '../../../context/AuthContext'
import { getInstitutions, linkInstitution } from '../../../lib/api'
import { ApiError } from '../../../lib/apiClient'
import type { InstitutionSummary } from '../../../types'
import { Button } from '../../../components/ui'
import { IconTile } from '../../../components/ui/IconTile'

/** Compact "which institution am I linked to" card — shows the real linked institution, or a real link action backed by GET /api/institutions + POST /students/me/institution. Never fabricates a name. */
export function InstitutionLink() {
  const { user, refreshUser } = useAuth()
  const [linking, setLinking] = useState(false)
  const [institutions, setInstitutions] = useState<InstitutionSummary[]>([])
  const [selected, setSelected] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (linking) {
      setError(null)
      getInstitutions()
        .then(setInstitutions)
        .catch((err) => setError(err instanceof ApiError ? err.message : 'Unable to load institutions. Please try again.'))
    }
  }, [linking])

  async function handleLink() {
    if (!selected) return
    setSubmitting(true)
    setError(null)
    try {
      await linkInstitution(selected)
      await refreshUser()
      setLinking(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not link this institution.')
    } finally {
      setSubmitting(false)
    }
  }

  if (user?.student_institution_name && !linking) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-line bg-surface px-4 py-3">
        <IconTile icon={Landmark} tone="primary" size="sm" />
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-faint">Institution</p>
          <p className="text-sm font-semibold text-ink">{user.student_institution_name}</p>
        </div>
      </div>
    )
  }

  if (!linking) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-xl border border-dashed border-line bg-canvas-2/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <IconTile icon={Landmark} tone="neutral" size="sm" />
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-faint">Institution</p>
            <p className="text-sm font-semibold text-muted">Not linked yet</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => setLinking(true)}>
          Link your institution
        </Button>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-faint">Select your institution</p>
      <div className="flex items-center gap-2">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full rounded-lg border border-line bg-surface px-3.5 py-2 text-sm text-ink outline-none focus:border-primary"
        >
          <option value="">Choose an institution…</option>
          {institutions.map((i) => (
            <option key={i.id} value={i.id}>
              {i.name}
            </option>
          ))}
        </select>
        <Button variant="solid" size="sm" loading={submitting} disabled={!selected} onClick={handleLink}>
          Link
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setLinking(false)}>
          Cancel
        </Button>
      </div>
      {error && <p className="mt-2 text-[13px] text-bad">{error}</p>}
    </div>
  )
}
