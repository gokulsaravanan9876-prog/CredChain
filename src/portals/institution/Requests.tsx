import { Inbox } from 'lucide-react'
import { PageHeader, GlassPanel } from '../../components/ui'

// NOTE: This flow (students requesting issuance/correction from their
// institution) was not present in the Figma file — only a student→company
// credential-request flow was designed. Built as an honest empty state
// rather than inventing an unspecified request/approval flow; wire up
// real behavior here once the product spec for this screen exists.
//
// Visually reproduces Stitch's "incoming_requests_refined" glass-card frame
// (see stitch1/incoming_requests_refined/code.html: rounded-xl glass-card
// with a glow-edge top highlight and a centered icon-in-circle) so the
// honest empty state still reads as part of the same design system as the
// populated request cards elsewhere, rather than a plain placeholder box.
export function InstitutionRequests() {
  return (
    <div>
      <PageHeader title="Requests" eyebrow="Student Requests" icon={Inbox} description="Requests from students for new or corrected credentials." />
      <GlassPanel className="flex flex-col items-center gap-3 px-6 py-14 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full border border-line bg-surface-2">
          <Inbox className="h-6 w-6 text-faint" strokeWidth={1.75} />
        </div>
        <h3 className="text-sm font-semibold text-ink">No pending requests</h3>
        <p className="max-w-xs text-[13px] text-muted">
          Student-initiated issuance requests will appear here once that flow is defined.
        </p>
      </GlassPanel>
    </div>
  )
}
