import { useEffect, useState } from 'react'
import { Building2, Network } from 'lucide-react'
import { getMyCompanyProfile, updateMyCompanyProfile } from '../../lib/api'
import { ApiError } from '../../lib/apiClient'
import type { Company } from '../../types'
import { PageHeader, Badge, Button, Field, GlassPanel, Glow } from '../../components/ui'
import { Input, Textarea } from '../../components/ui/Input'
import { SkeletonCard } from '../../components/ui/Skeleton'

/**
 * Reproduces the actual Stitch "company_profile_settings" screen's two-tier
 * structure — a centered glowing identity hero, then a "Core Profile"
 * read-only info card, then the editable settings form — see
 * stitch2/company_profile_settings/code.html + screen.png. Stitch's own
 * screen also shows an "API & Integration" (webhooks/access keys) and "Team
 * Management" section — CredChain has no such backend capability, so those
 * are intentionally NOT reproduced (would be inventing functionality); every
 * value shown below is the real `Company` record already fetched here.
 */

export function Profile() {
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const [industry, setIndustry] = useState('')
  const [website, setWebsite] = useState('')
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [companySize, setCompanySize] = useState('')

  useEffect(() => {
    getMyCompanyProfile()
      .then((c) => {
        setCompany(c)
        setIndustry(c.industry ?? '')
        setWebsite(c.website ?? '')
        setDescription(c.description ?? '')
        setLocation(c.location ?? '')
        setCompanySize(c.company_size ?? '')
      })
      .finally(() => setLoading(false))
  }, [])

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const updated = await updateMyCompanyProfile({
        industry: industry || undefined,
        website: website || undefined,
        description: description || undefined,
        location: location || undefined,
        company_size: companySize || undefined,
      })
      setCompany(updated)
      setSaved(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="space-y-4"><SkeletonCard lines={3} /><SkeletonCard lines={3} /></div>
  if (!company) return null

  return (
    <div>
      <PageHeader title="Company Profile" eyebrow="Public Presentation" icon={Building2} description="This is what students see when they view your company." />

      {/* Identity hero — Stitch's centered glowing avatar + name + ID */}
      <GlassPanel className="relative mb-6 flex flex-col items-center overflow-hidden p-8 text-center">
        <Glow color="ai" size={300} animate={false} className="left-1/2 top-0 -translate-x-1/2" />
        <div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-ai-line bg-ai-bg text-ai shadow-glow-ai">
          <Network className="h-9 w-9" strokeWidth={1.75} />
        </div>
        <h2 className="relative mt-4 text-xl font-bold text-ink font-[family-name:var(--font-display)]">{company.name}</h2>
        <p className="relative mt-1 font-[family-name:var(--font-mono)] text-[12px] text-faint">ID: {company.id.slice(0, 8)}…</p>
      </GlassPanel>

      {/* Core Profile — real, read-only summary of the current record */}
      <GlassPanel className="mb-6 p-6">
        <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-cyan">Core Profile</p>
        <dl className="divide-y divide-line">
          <div className="flex items-center justify-between py-2.5 text-sm">
            <dt className="text-muted">Industry</dt>
            <dd className="font-semibold text-ink">{company.industry || 'Not set'}</dd>
          </div>
          <div className="flex items-center justify-between py-2.5 text-sm">
            <dt className="text-muted">Location</dt>
            <dd className="font-semibold text-ink">{company.location || 'Not set'}</dd>
          </div>
          <div className="flex items-center justify-between py-2.5 text-sm">
            <dt className="text-muted">Status</dt>
            <dd>
              <Badge tone="good" size="sm">Active</Badge>
            </dd>
          </div>
        </dl>
      </GlassPanel>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <GlassPanel className="relative overflow-hidden p-6 lg:col-span-2">
          <Glow color="ai" size={280} className="-right-14 -top-16" animate={false} />
          <h3 className="relative mb-5 text-base font-semibold text-ink">Edit Details</h3>

          <div className="relative space-y-4">
            <Field label="Industry">
              <Input value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="e.g. Software" />
            </Field>
            <Field label="Website">
              <Input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://…" />
            </Field>
            <Field label="Location">
              <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Bengaluru, India" />
            </Field>
            <Field label="Company Size">
              <Input value={companySize} onChange={(e) => setCompanySize(e.target.value)} placeholder="e.g. 51-200" />
            </Field>
            <Field label="Description">
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                placeholder="What does your company do?"
              />
            </Field>
          </div>

          {error && <div className="relative mt-4 rounded-lg bg-bad-bg px-3.5 py-2.5 text-[13px] text-bad">{error}</div>}
          {saved && <div className="relative mt-4 rounded-lg bg-good-bg px-3.5 py-2.5 text-[13px] text-good">Profile updated.</div>}

          <Button variant="solid" className="relative mt-5" loading={saving} onClick={handleSave}>
            Save Changes
          </Button>
        </GlassPanel>
      </div>
    </div>
  )
}
