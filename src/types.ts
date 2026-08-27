// ---------------------------------------------------------------------------
// CredChain — shared data model
//
// This file is the single source of truth for shapes used across all three
// portals (student / institution / verifier). Mock data and the mock API
// layer (src/lib/api.ts) both conform to these types, so swapping in a real
// backend later only means changing the *implementation* inside api.ts, not
// any of the UI code that consumes it.
// ---------------------------------------------------------------------------

export type Role = 'student' | 'institution' | 'verifier'

// ---------------------------------------------------------------------------
// Auth (real backend, Phase 3) — mirrors backend/app/schemas/auth.py exactly.
// ---------------------------------------------------------------------------

export interface AuthUser {
  id: string
  full_name: string
  email: string
  role: Role
  is_active: boolean
  student_id: string | null
  institution_id: string | null
  company_id: string | null
  org_name: string | null
  /** Only meaningful for students: the institution they're affiliated with (distinct from institution_id above). */
  student_institution_id: string | null
  student_institution_name: string | null
}

/**
 * Public-safe institution profile — GET /api/institutions (list) and
 * GET /api/institutions/{id} (detail). description/location/website/
 * institution_type are optional: a real institution that hasn't filled
 * them in (or a login-linked institution seeded before this field existed)
 * simply has them as null, never a fabricated placeholder.
 */
export interface InstitutionSummary {
  id: string
  name: string
  description: string | null
  location: string | null
  website: string | null
  institution_type: string | null
}

export interface AuthTokenResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

/** Mirrors backend/app/schemas/auth.py RegisterRequest exactly — only fields the backend actually accepts. */
export interface RegisterPayload {
  email: string
  password: string
  full_name: string
  role: Role
  student_identifier?: string
  /** Real institution id from GET /api/institutions — never a free-typed value. */
  institution_id?: string
  institution_name?: string
  institution_registration_number?: string
  company_name?: string
  company_industry?: string
  company_website?: string
}

// ---------------------------------------------------------------------------
// Credentials (real backend, Phase 4) — mirrors backend/app/schemas/credential.py.
// ---------------------------------------------------------------------------

export interface BackendCredential {
  id: string
  credential_identifier: string
  student_id: string
  student_name: string
  institution_id: string
  institution_name: string
  credential_type: CredentialType
  title: string
  degree: string | null
  graduation_year: number | null
  cgpa: number | null
  status: 'active' | 'revoked' | 'expired'
  issued_at: string
  revoked_at: string | null
  document_hash: string | null
  signature: string | null
  has_document: boolean
  // Phase 9D: public blockchain anchor metadata — never a private key or
  // RPC credential, those never leave the backend.
  blockchain_status: 'pending' | 'anchored' | 'failed' | null
  blockchain_network: string | null
  blockchain_contract_address: string | null
  blockchain_tx_hash: string | null
  blockchain_anchored_at: string | null
}

export interface BackendStudentSummary {
  id: string
  user_id: string
  full_name: string
  student_identifier: string
  credential_count: number
}

// ---------------------------------------------------------------------------
// Verification (real backend, Phase 5) — mirrors backend/app/schemas/verification.py.
// ---------------------------------------------------------------------------

export interface VerificationChecksResult {
  issuer: boolean
  signature: boolean
  integrity: boolean
  status: boolean
  access: boolean
}

export interface VerifiedCredentialPreview {
  credential_identifier: string
  credential_type: CredentialType
  title: string
  degree: string | null
  graduation_year: number | null
  cgpa: number | null
  institution_name: string
}

/** Phase 9C: status is one of ANCHORED / NOT_ANCHORED / MISMATCH / UNAVAILABLE. Every field is real data or null — nothing is ever fabricated client-side. */
export interface BlockchainVerificationResult {
  status: 'ANCHORED' | 'NOT_ANCHORED' | 'MISMATCH' | 'UNAVAILABLE'
  anchored: boolean
  hash_matches: boolean | null
  network: string | null
  contract_address: string | null
  transaction_hash: string | null
  anchored_at: string | null
}

export interface VerifyCredentialResponse {
  result: VerificationStatus
  checks: VerificationChecksResult
  credential: VerifiedCredentialPreview | null
  blockchain: BlockchainVerificationResult | null
  requested_credentials: string[] | null
}

// ---------------------------------------------------------------------------
// Credential requests + selective sharing (real backend, Phase 6) — mirrors
// backend/app/schemas/sharing.py exactly.
// ---------------------------------------------------------------------------

export type BackendRequestStatus = 'pending' | 'approved' | 'declined' | 'expired'

export interface BackendCredentialRequest {
  id: string
  company_id: string
  company_name: string
  student_id: string
  student_name: string
  purpose: string
  requested_credentials: string[]
  status: BackendRequestStatus
  created_at: string
  updated_at: string
  responded_at: string | null
  shared_credentials: ShareCredentialPreview[]
}

export type InstitutionRequestStatus = 'pending' | 'approved' | 'rejected' | 'fulfilled'

export interface InstitutionCertificateRequest {
  id: string
  batch_id: string | null
  student_id: string
  student_name: string
  student_identifier: string
  institution_id: string
  institution_name: string
  credential_type: CredentialType
  custom_credential_name: string | null
  reason: string | null
  status: InstitutionRequestStatus
  rejection_reason: string | null
  fulfilled_credential_id: string | null
  created_at: string
  responded_at: string | null
}

export type StudentDocumentStatus = 'unverified' | 'under_review' | 'approved' | 'rejected'

export interface StudentDocument {
  id: string
  student_id: string
  student_name: string
  student_identifier: string
  institution_id: string
  institution_name: string
  credential_type: CredentialType
  custom_credential_name: string | null
  original_filename: string
  status: StudentDocumentStatus
  rejection_reason: string | null
  resulting_credential_id: string | null
  created_at: string
  reviewed_at: string | null
}

export interface NotificationCounts {
  pending_company_requests: number | null
  pending_certificate_requests: number | null
  pending_document_reviews: number | null
  unverified_shared_credentials: number | null
  new_job_applications: number | null
}

export interface ShareCredentialPreview {
  id: string
  credential_type: CredentialType
  title: string
  degree: string | null
  graduation_year: number | null
  cgpa: number | null
  institution_name: string
}

export type ShareGrantStatus = 'active' | 'expired' | 'revoked'

export interface BackendShareGrant {
  id: string
  company_id: string
  company_name: string
  credentials: ShareCredentialPreview[]
  permission: string
  created_at: string
  expires_at: string
  revoked_at: string | null
  status: ShareGrantStatus
}

export interface ShareCreatedResult {
  share: BackendShareGrant
  /** Raw secure token — present only in this one response, at creation time. */
  share_token: string
  share_url: string
}

export interface ShareTokenAccessResult {
  company_name: string
  expires_at: string
  credentials: ShareCredentialPreview[]
  permission: string
}

// ---------------------------------------------------------------------------
// CredChain AI (real backend, Phase 7) — mirrors backend/app/schemas/ai.py.
// Every result carries analysis_mode: 'ai' | 'fallback' — the frontend must
// visibly distinguish real AI output from the deterministic fallback used
// when no AI provider is configured (never present fallback as if it were AI).
// ---------------------------------------------------------------------------

export type AiAnalysisMode = 'ai' | 'fallback'

export interface AiHealthResult {
  ai_enabled: boolean
  provider: string | null
  model: string | null
}

export interface AiDocumentRequirementItem {
  document: string
  status: 'required' | 'recommended'
  source: string
}

export interface AiWalletComparisonItem {
  document: string
  available: boolean
  matched_credential_title: string | null
}

export interface AiDocumentRequirementsResult {
  company: string
  job_title: string
  requirements: AiDocumentRequirementItem[]
  not_specified: string[]
  wallet_comparison: AiWalletComparisonItem[]
  analysis_mode: AiAnalysisMode
}

export interface AiPackageInfo {
  available: boolean
  amount: string | null
  currency: string | null
  year: number | null
  source: string | null
  message: string | null
}

export interface AiTrendItem {
  claim: string
  source: string
  year: number
}

export interface AiCompanyIntelligenceResult {
  company: string
  overview: string
  common_roles: string[]
  eligibility: string[]
  skills: string[]
  recruitment_process: string[]
  package_information: AiPackageInfo
  trends: AiTrendItem[]
  sources: string[]
  analysis_mode: AiAnalysisMode
}

export interface AiMatchSummary {
  matched: number
  missing: number
  total: number
  score: number
}

export interface AiCredentialMatchResult {
  match_summary: AiMatchSummary
  matched: string[]
  missing: string[]
  recommendations: string[]
  analysis_mode: AiAnalysisMode
}

/** A credential's own lifecycle state, as tracked by the issuing institution. */
export type CredentialStatus = 'verified' | 'pending' | 'revoked'

/** The outcome of a point-in-time verification check run by a verifier. */
// Widened in Phase 5 to match the real backend's possible verification
// results exactly (backend/app/models/enums.py's VerificationResultStatus,
// plus NOT_FOUND which is API-level rather than a stored enum value).
export type VerificationStatus = 'VERIFIED' | 'INVALID' | 'REVOKED' | 'EXPIRED' | 'UNAUTHORIZED' | 'NOT_FOUND' | 'TYPE_MISMATCH'

export type CredentialType =
  | 'degree'
  | 'transcript'
  | 'migration'
  | 'internship'
  | 'certification'
  | 'course'
  | 'other'

export interface User {
  id: string
  name: string
  initials: string
  role: Role
  /** Institution/company users belong to an org; students do not. */
  orgName?: string
}

export interface Credential {
  id: string
  type: CredentialType
  title: string
  issuer: string
  issuedTo: string /** student user id */
  issuedDate: string /** e.g. "2026" */
  status: CredentialStatus
  cgpa?: number
  /** Ground-truth value recorded at issuance time, used to detect tampering. */
  originalCgpa?: number
  documentUrl: string
  fields: { label: string; value: string }[]
  /** Populated for institution-issued-credentials views (real backend); undefined for mock-only data. */
  studentName?: string
  /** Phase 9D — undefined only for mock-only data; a real credential always has one (possibly all-null, meaning never anchored). */
  blockchain?: CredentialBlockchainInfo
}

/** Phase 9D: public blockchain anchor metadata for one credential — mirrors BackendCredential's blockchain_* fields. */
export interface CredentialBlockchainInfo {
  status: 'pending' | 'anchored' | 'failed' | null
  network: string | null
  contractAddress: string | null
  transactionHash: string | null
  anchoredAt: string | null
}

export interface CredentialRequest {
  id: string
  requesterOrg: string
  requesterRole: string /** e.g. "Software Engineer Application" */
  credentialIds: string[]
  status: 'pending' | 'approved' | 'declined'
  requestedAt: string
}

export interface AccessLogEntry {
  id: string
  category: 'sharing' | 'verification' | 'requests' | 'credential' | 'ai'
  actor: string /** e.g. "ABC Technologies" or "XYZ University" — shown as the row subtitle */
  action: string /** short bold title, e.g. "Transcript verified" */
  timestamp: string /** display string, e.g. "10:42 AM" or "Yesterday" */
  icon: 'shield' | 'mail' | 'check'
}

/** Phase 8B: real activity feed row from GET /api/{role}/me/activity. */
export interface BackendActivityEvent {
  id: string
  action: string
  message: string
  entity_type: string | null
  entity_id: string | null
  created_at: string
}

export interface VerificationCheck {
  label: string
  passed: boolean
  description?: string
}

export interface BundleVerificationResult {
  status: VerificationStatus
  candidateName?: string
  credentials: Credential[]
  checks: VerificationCheck[]
  tamperDiff?: { credentialTitle: string; field: string; original: string; presented: string }
  /** Phase 9D — undefined only for the page's pre-existing mock-data candidates; a real backend verify always sets it (possibly null). */
  blockchain?: BlockchainVerificationResult | null
  /** PS3 Phase F — the original request's requested-credential labels, when this credential came from a request-linked share. */
  requestedCredentials?: string[] | null
}

/** A REAL company profile — every field is a genuine database column (see backend/app/schemas/company.py). Never fabricated. */
export interface Company {
  id: string
  name: string
  industry: string | null
  website: string | null
  description: string | null
  location: string | null
  company_size: string | null
  created_at: string
  /** Real count of this company's currently-OPEN jobs, computed server-side. */
  open_positions_count: number
}

export interface UpdateCompanyProfileInput {
  industry?: string
  website?: string
  description?: string
  location?: string
  company_size?: string
}

export type JobEmploymentType = 'full_time' | 'part_time' | 'internship' | 'contract'
export type JobStatus = 'draft' | 'open' | 'closed'

export type EligibilityCheckStatus = 'met' | 'not_met' | 'incomplete'
export type EligibilityOverallStatus = 'eligible' | 'not_eligible' | 'incomplete'

export interface EligibilityCheckItem {
  label: string
  met: boolean
  mandatory: boolean
  /** Distinguishes a real failed requirement from "no student data exists to check this at all" — never silently the same thing. */
  status: EligibilityCheckStatus
}

export interface EligibilityResult {
  is_eligible: boolean
  checks: EligibilityCheckItem[]
  status: EligibilityOverallStatus
}

export interface Job {
  id: string
  company_id: string
  company_name: string
  title: string
  description: string
  location: string | null
  employment_type: JobEmploymentType
  required_degree: string | null
  minimum_cgpa: number | null
  graduation_year_requirement: number | null
  required_skills: string[]
  required_certifications: string[]
  required_documents: string[]
  status: JobStatus
  application_deadline: string | null
  created_at: string
  eligibility: EligibilityResult | null
}

export interface CreateJobInput {
  title: string
  description: string
  location?: string
  employment_type: JobEmploymentType
  required_degree?: string
  minimum_cgpa?: number
  graduation_year_requirement?: number
  required_skills: string[]
  required_certifications: string[]
  required_documents: string[]
  application_deadline?: string
}

export type ApplicationStatus = 'applied' | 'under_review' | 'shortlisted' | 'rejected' | 'accepted' | 'withdrawn'

export interface StudentJobApplication {
  id: string
  job_id: string
  job_title: string
  company_id: string
  company_name: string
  status: ApplicationStatus
  rejection_reason: string | null
  created_at: string
}

export interface CompanyJobApplication {
  id: string
  job_id: string
  job_title: string
  student_id: string
  student_name: string
  student_identifier: string
  status: ApplicationStatus
  rejection_reason: string | null
  created_at: string
  credential_request: BackendCredentialRequest | null
  eligibility: EligibilityResult
}

export interface JobAIAnalysisResult {
  job_id: string
  company_name: string
  job_title: string
  document_requirements: AiDocumentRequirementsResult
  company_intelligence: AiCompanyIntelligenceResult
  credential_match: AiCredentialMatchResult
  eligibility: EligibilityResult
}

export interface RequirementMatch {
  label: string
  status: 'matched' | 'gap'
  /** id of the credential that satisfies this requirement, if matched */
  credentialId?: string
}

export interface AIAnalysis {
  companyName: string
  roleName: string
  matchedCount: number
  totalCount: number
  requirements: RequirementMatch[]
  guidance: string
}

export interface Candidate {
  id: string
  name: string
  initials: string
  role: string
  status: VerificationStatus | 'pending'
}

export interface DashboardStats {
  label: string
  value: number
  tone: 'neutral' | 'good' | 'warn' | 'bad'
}
