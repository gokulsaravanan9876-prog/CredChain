import type { CredentialType, CredentialStatus, VerificationStatus } from '../types'
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
