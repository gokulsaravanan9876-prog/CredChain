import { useEffect, useMemo, useState } from 'react'
import { Wallet } from 'lucide-react'
import { getCredentials } from '../../lib/api'
import type { Credential, CredentialStatus } from '../../types'
import { PageHeader, SearchInput, FilterPills, EmptyState } from '../../components/ui'
import { SkeletonGrid } from '../../components/ui/Skeleton'
import { CredentialCard } from './components/CredentialCard'

type Filter = 'all' | CredentialStatus

export function CredentialsList() {
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<Filter>('all')

  useEffect(() => {
    getCredentials().then(setCredentials).finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    return credentials.filter((c) => {
      const matchesFilter = filter === 'all' || c.status === filter
      const matchesQuery = c.title.toLowerCase().includes(query.toLowerCase()) || c.issuer.toLowerCase().includes(query.toLowerCase())
      return matchesFilter && matchesQuery
    })
  }, [credentials, query, filter])

  return (
    <div>
      <PageHeader title="Digital Vault" eyebrow="Academic Passport" icon={Wallet} description="Your cryptographically verified academic credentials, secured on-chain where anchored." />

      <div className="mb-5 flex items-center gap-4">
        <SearchInput
          placeholder="Search credentials…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-xs"
        />
        <FilterPills
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'all', label: 'All' },
            { value: 'verified', label: 'Verified' },
            { value: 'pending', label: 'Pending' },
            { value: 'revoked', label: 'Revoked' },
          ]}
        />
        <span className="ml-auto text-xs font-medium text-muted">{filtered.length} credentials</span>
      </div>

      {loading ? (
        <SkeletonGrid count={6} />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Wallet}
          title="No credentials found"
          description="Try a different search term or filter — or check back after your institution issues something new."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <CredentialCard key={c.id} credential={c} />
          ))}
        </div>
      )}
    </div>
  )
}
