import type { CredentialType, CredentialStatus, VerificationStatus, Role } from '../types'
import { GraduationCap, FileText, Stamp, Briefcase, Award, BookOpen, FileQuestion, type LucideIcon } from 'lucide-react'

/** One lookup table for credential-type icons, used everywhere a credential renders. */
export const CREDENTIAL_TYPE_ICON: Record<CredentialType, LucideIcon> = {
  degree: GraduationCap,
  transcript: FileText,
  migration: Stamp,
  internship: Briefcase,
  certification: Award,
  course: BookOpen,
  other: FileQuestion,
}

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

/** Known public block explorers, keyed by the backend's blockchain_network value. Only Polygon Amoy exists in this phase. */
const BLOCK_EXPLORER_TX_BASE_URL: Record<string, string> = {
  'polygon-amoy': 'https://amoy.polygonscan.com/tx/',
}

/** Builds a public explorer URL for a transaction hash — never fabricates one; returns null unless both a known network and a real hash are present. */
export function blockchainExplorerTxUrl(network: string | null | undefined, txHash: string | null | undefined): string | null {
  if (!network || !txHash) return null
  const base = BLOCK_EXPLORER_TX_BASE_URL[network]
  return base ? `${base}${txHash}` : null
}

export function shortHash(hash: string, lead = 6, trail = 4): string {
  if (hash.length <= lead + trail + 3) return hash
  return `${hash.slice(0, lead)}...${hash.slice(-trail)}`
}

/**
 * Time-of-day greeting using the browser's local clock — never hardcodes
 * "Morning". Uses only the authenticated user's real first name; falls back
 * to a neutral greeting (never another person's name) when unavailable.
 */
export function timeBasedGreeting(fullName: string | null | undefined): string {
  const hour = new Date().getHours()
  let period: string
  if (hour >= 5 && hour < 12) period = 'Good Morning'
  else if (hour >= 12 && hour < 17) period = 'Good Afternoon'
  else if (hour >= 17 && hour < 21) period = 'Good Evening'
  else period = 'Good Night'

  const firstName = fullName?.trim().split(/\s+/)[0]
  return firstName ? `${period}, ${firstName}` : 'Welcome back'
}

export type Tone = 'good' | 'warn' | 'bad' | 'neutral' | 'primary'

export function credentialStatusTone(status: CredentialStatus): Tone {
  if (status === 'verified') return 'good'
  if (status === 'pending') return 'warn'
  return 'bad'
}

export function verificationStatusTone(status: VerificationStatus): Tone {
  if (status === 'VERIFIED') return 'good'
  if (status === 'REVOKED') return 'warn'
  return 'bad'
}

export const TONE_CLASSES: Record<Tone, { bg: string; text: string; border: string }> = {
  good: { bg: 'bg-good-bg', text: 'text-good', border: 'border-good-line' },
  warn: { bg: 'bg-warn-bg', text: 'text-warn', border: 'border-warn-line' },
  bad: { bg: 'bg-bad-bg', text: 'text-bad', border: 'border-bad-line' },
  neutral: { bg: 'bg-canvas-2', text: 'text-muted', border: 'border-line' },
  primary: { bg: 'bg-primary-bg', text: 'text-primary', border: 'border-primary-line' },
}

export function credentialStatusLabel(status: CredentialStatus): string {
  if (status === 'verified') return 'Verified'
  if (status === 'pending') return 'Pending'
  return 'Revoked'
}

/**
 * Maps a notification's (link_entity_type, link_entity_id) onto an EXISTING
 * route, for the viewer's own role — never a route that doesn't exist, and
 * never a raw URL carried on the notification itself (see
 * backend/app/models/notification.py's docstring for the same rule at the
 * write boundary). The same entity_type can mean a different real
 * destination for different roles (e.g. "company" opens the admin
 * verification queue for an admin, but the company's own profile page for
 * that company) — so this always takes the current viewer's role into
 * account. Returns null when there's no real, existing page for this
 * (role, entity_type) pair — the notification stays fully readable with no
 * link, never a broken/guessed one.
 */
export function notificationLink(role: Role, entityType: string | null, entityId: string | null): string | null {
  if (!entityType || !entityId) return null
  switch (entityType) {
    case 'credential':
      return role === 'student' ? `/student/credentials/${entityId}` : null
    case 'credential_request':
      if (role === 'student') return '/student/requests'
      if (role === 'verifier') return '/verifier/requests'
      return null
    case 'share_grant':
      if (role === 'student') return '/student/shares'
      if (role === 'verifier') return '/verifier/requests'
      return null
    case 'job_application':
      if (role === 'student') return '/student/my-applications'
      if (role === 'verifier') return '/verifier/applications'
      return null
    case 'institution_certificate_request':
      if (role === 'student') return '/student/certificate-requests'
      if (role === 'institution') return '/institution/certificate-requests'
      return null
    case 'student_document':
      if (role === 'student') return '/student/documents'
      if (role === 'institution') return '/institution/documents'
      return null
    case 'institution':
      if (role === 'admin') return '/admin'
      if (role === 'institution') return '/institution'
      return null
    case 'company':
      if (role === 'admin') return '/admin'
      if (role === 'verifier') return '/verifier/profile'
      return null
    default:
      return null
  }
}

/** Short, human-readable relative time ("2m ago", "3h ago", "5d ago"), falling back to a real date once it's far enough in the past to stop being useful as "recent". */
export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000))
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}
