import { useNavigate } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import { Button, CheckRow, GlassPanel, Glow } from '../../components/ui'

export function CredentialIssued() {
  const navigate = useNavigate()

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-ink font-[family-name:var(--font-display)]">Credential Issued</h1>

      <GlassPanel className="relative max-w-md overflow-hidden p-8 text-center">
        <Glow color="good" size={280} className="left-1/2 -top-20 -translate-x-1/2" animate={false} />
        <div className="relative mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-good-line bg-good-bg shadow-glow-good">
          <CheckCircle2 className="h-8 w-8 text-good" strokeWidth={1.75} />
        </div>
        <h2 className="relative text-xl font-extrabold tracking-tight text-good font-[family-name:var(--font-display)]">Credential Issued</h2>

        <div className="relative mt-5 space-y-2.5 text-left">
          <CheckRow label="Digitally Signed" state="pass" bordered />
          <CheckRow label="Credential Record Created" state="pass" bordered />
          <CheckRow label="Status: Active" state="pass" bordered />
        </div>

        <p className="relative mt-5 text-[13px] text-muted">The credential is now available in the student's CredChain wallet.</p>

        <Button variant="solid" className="relative mt-6 w-full" onClick={() => navigate('/institution')}>
          Back to Dashboard
        </Button>
      </GlassPanel>
    </div>
  )
}
