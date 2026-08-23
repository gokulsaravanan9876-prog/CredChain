import { Link } from 'react-router-dom'
import { ShieldCheck, GraduationCap, Wallet, Share2, ScanSearch, ArrowRight, ShieldQuestion } from 'lucide-react'
import { Button, RoleBackground } from '../../components/ui'

/**
 * Reproduces the actual Stitch "credchain_cinematic_launch_page" screen 1:1 in
 * structure (fixed glass navbar -> hero with 3D glass frame -> "The Trustless
 * Pipeline" 4-card journey) rather than the generic marketing-page template —
 * see stitch1/credchain_cinematic_launch_page/code.html for the reference this
 * was built against. Stitch's own export has no role-card grid, feature-card
 * grid, closing CTA, or footer section below the journey — this intentionally
 * doesn't add them back in, to stay a faithful reproduction rather than a
 * "similar style" page. All copy is CredChain's real product description
 * (nothing from Stitch's own copy needed swapping — it was already accurate).
 */
const JOURNEY = [
  {
    icon: GraduationCap,
    title: 'Issue',
    description: 'Institutions cryptographically sign verified credentials directly into the student’s wallet.',
    accent: 'primary' as const,
    tilt: '-rotate-y-6',
    offset: '',
  },
  {
    icon: Wallet,
    title: 'Own',
    description: 'Students hold the real, signed proof in their own decentralized credential wallet.',
    accent: 'cyan' as const,
    tilt: '',
    offset: 'md:translate-y-4',
  },
  {
    icon: Share2,
    title: 'Share',
    description: 'The student chooses exactly which credential to share, with whom, and for how long.',
    accent: 'ai' as const,
    tilt: '',
    offset: 'md:-translate-y-2',
  },
  {
    icon: ScanSearch,
    title: 'Verify',
    description: 'Employers instantly check signature and status — authenticity, not just appearance.',
    accent: 'good' as const,
    tilt: 'rotate-y-6',
    offset: '',
  },
]

const ACCENT = {
  primary: { icon: 'text-primary', ring: 'group-hover:border-primary/50 group-hover:bg-primary-bg', glow: 'group-hover:shadow-[0_30px_60px_-20px_rgba(79,70,229,0.4)]' },
  cyan: { icon: 'text-cyan', ring: 'group-hover:border-cyan/50 group-hover:bg-cyan-bg', glow: 'group-hover:shadow-[0_30px_60px_-20px_rgba(76,215,246,0.4)]' },
  ai: { icon: 'text-ai', ring: 'group-hover:border-ai/50 group-hover:bg-ai-bg', glow: 'group-hover:shadow-[0_30px_60px_-20px_rgba(167,139,250,0.4)]' },
  good: { icon: 'text-good', ring: 'group-hover:border-good/50 group-hover:bg-good-bg', glow: 'group-hover:shadow-[0_30px_60px_-20px_rgba(78,222,163,0.4)]' },
}

export function Landing() {
  return (
    <div className="relative min-h-screen overflow-x-clip bg-canvas text-body">
      <RoleBackground role="landing" className="fixed" />
      {/* Stitch: three soft atmospheric light-leak blobs anchored to the viewport, not the scroll content */}
      <div aria-hidden className="pointer-events-none fixed -left-64 -top-64 -z-10 h-[800px] w-[800px] rounded-full bg-primary/10 blur-[120px]" />
      <div aria-hidden className="pointer-events-none fixed -bottom-48 -right-48 -z-10 h-[600px] w-[600px] rounded-full bg-cyan/10 blur-[100px]" />

      {/* ---- Fixed glass navbar ---- */}
      <header className="fixed top-0 z-50 w-full glass-surface">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-7 w-7 text-primary drop-shadow-[0_0_10px_rgba(79,70,229,0.5)]" strokeWidth={2.25} />
            <span className="text-2xl font-bold tracking-tight text-white font-[family-name:var(--font-display)] [text-shadow:0_0_30px_rgba(195,192,255,0.3)]">
              CredChain
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/sign-in">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/sign-up">
              <Button variant="solid" size="sm">
                Create Account
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="relative flex w-full flex-col px-5 pb-32 pt-32 md:px-8">
        {/* ---- Hero ---- */}
        <section className="mx-auto flex w-full max-w-7xl flex-col items-center gap-16 md:mt-20 md:flex-row md:items-center md:justify-between">
          {/* Left: badge, headline, subhead, CTAs, trust line */}
          <div className="z-10 flex w-full flex-col gap-8 md:w-1/2">
            <div className="inline-flex max-w-full items-center gap-3 rounded-full border border-white/10 bg-white/5 px-5 py-2 backdrop-blur-md shadow-[0_0_20px_-8px_var(--color-cyan)]">
              <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-cyan shadow-[0_0_12px_var(--color-cyan)]" />
              <span className="font-[family-name:var(--font-mono)] text-[11px] uppercase leading-snug tracking-[0.1em] text-cyan sm:text-[12px] sm:tracking-[0.15em] sm:whitespace-nowrap">
                Instant Transcript &amp; Migration Verification
              </span>
            </div>

            <h1 className="text-[40px] font-bold leading-[1.1] tracking-tight text-white font-[family-name:var(--font-display)] drop-shadow-2xl md:text-[64px] md:leading-[1.1]">
              Instant academic verification,{' '}
              <span className="animate-[gradient_8s_ease_infinite] bg-gradient-to-r from-primary via-cyan to-primary bg-[length:200%_auto] bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(195,192,255,0.4)]">
                owned by the student.
              </span>
            </h1>

            <p className="max-w-xl text-lg leading-relaxed text-body opacity-90 md:text-xl">
              Universities issue cryptographically signed transcripts, degrees and migration certificates. Students
              own and selectively share them. Employers and institutions verify authenticity in seconds.
            </p>

            <div className="mt-2 flex flex-col gap-4 sm:flex-row">
              <Link to="/sign-up">
                <Button variant="solid" className="w-full rounded-xl px-8 py-4 text-sm sm:w-auto" icon={<ArrowRight className="h-4 w-4" strokeWidth={2.5} />}>
                  Get Started
                </Button>
              </Link>
              <a href="#how-it-works" className="w-full sm:w-auto">
                <Button variant="outline" className="glass-surface w-full rounded-xl px-8 py-4 text-sm sm:w-auto">
                  See How It Works
                </Button>
              </a>
            </div>
          </div>

          {/* Right: 3D glass frame with the CredChain hologram/status badge (Stitch's exact "hologram-badge" motif) */}
          <div className="group relative z-10 h-[450px] w-full overflow-hidden rounded-3xl glass-surface transition-transform duration-700 md:h-[650px] md:w-1/2">
            <div aria-hidden className="pointer-events-none absolute inset-0 z-20 bg-gradient-to-tr from-transparent via-white/5 to-white/20 opacity-0 mix-blend-overlay transition-opacity duration-500 group-hover:opacity-100" />
            <div aria-hidden className="pointer-events-none absolute inset-0 z-10 shadow-[inset_0_0_100px_rgba(0,0,0,0.8)]" />
            <div aria-hidden className="absolute inset-0 flex items-center justify-center opacity-70">
              <div className="h-64 w-64 rounded-full bg-gradient-to-br from-primary/30 via-cyan/20 to-transparent blur-3xl motion-safe:animate-[glowPulse_6s_ease-in-out_infinite]" />
            </div>
            <div aria-hidden className="absolute inset-0 flex items-center justify-center">
              <ShieldCheck className="h-32 w-32 text-white/10" strokeWidth={1} />
            </div>

            {/* Holographic status badge — honest phrasing: this is marketing chrome illustrating the signature
                check every credential gets, not a claim that a specific credential is blockchain-anchored
                (the real app's default state is NOT ANCHORED and must never be contradicted here). */}
            <div className="motion-safe:animate-bounce absolute bottom-8 left-8 z-30 flex items-center gap-4 rounded-xl border border-good-line bg-gradient-to-br from-good-bg to-transparent p-4 backdrop-blur-md shadow-[0_0_20px_-4px_var(--color-good)]">
              <div className="relative flex h-10 w-10 items-center justify-center">
                <div className="absolute inset-0 rounded-full border-2 border-dashed border-good opacity-50 motion-safe:animate-spin [animation-duration:4s]" />
                <ShieldCheck className="h-6 w-6 text-good drop-shadow-[0_0_8px_rgba(78,222,163,0.8)]" strokeWidth={2.25} />
              </div>
              <div>
                <div className="mb-0.5 font-[family-name:var(--font-mono)] text-[11px] uppercase tracking-[0.15em] text-good/70">Status</div>
                <div className="text-sm font-bold tracking-wide text-good drop-shadow-[0_0_5px_rgba(78,222,163,0.5)]">Signature Valid</div>
              </div>
            </div>
          </div>
        </section>

        {/* ---- Journey: "The Trustless Pipeline" ---- */}
        <section id="how-it-works" className="relative z-10 mx-auto mt-40 w-full max-w-7xl md:mt-56">
          <div className="mb-24 flex flex-col items-center text-center">
            <h2 className="mb-6 text-[28px] font-semibold tracking-tight text-white font-[family-name:var(--font-display)] [text-shadow:0_0_30px_rgba(195,192,255,0.3)] md:text-4xl md:font-bold">
              The Trustless Pipeline
            </h2>
            <p className="max-w-2xl text-lg text-body">A frictionless journey from institution to employer, secured by cryptography.</p>
          </div>

          <div className="relative grid grid-cols-1 gap-8 md:grid-cols-4">
            <div aria-hidden className="absolute left-4 top-1/2 z-0 hidden h-px w-[calc(100%-2rem)] -translate-y-1/2 bg-gradient-to-r from-transparent via-primary/40 to-transparent blur-[2px] md:block" />
            {JOURNEY.map((step) => {
              const a = ACCENT[step.accent]
              return (
                <div
                  key={step.title}
                  className={`group relative z-10 rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-black/20 p-8 backdrop-blur-md transition-all duration-500 hover:-translate-y-4 ${a.glow} ${step.tilt} ${step.offset}`}
                >
                  <div className={`mb-8 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/5 transition-all duration-300 ${a.ring}`}>
                    <step.icon className={`h-7 w-7 ${a.icon} transition-transform group-hover:scale-110`} strokeWidth={1.75} />
                  </div>
                  <h3 className="mb-3 text-xl font-semibold tracking-wide text-white font-[family-name:var(--font-display)]">{step.title}</h3>
                  <p className="text-[15px] leading-relaxed text-body opacity-80">{step.description}</p>
                </div>
              )
            })}
          </div>
        </section>

        {/* Minimal wayfinding — Stitch's own export has no footer/CTA section below the journey;
            this single line replaces it purely so a lost visitor isn't stranded with zero navigation. */}
        <div className="relative z-10 mx-auto mt-24 flex items-center gap-2 text-[13px] text-faint">
          <ShieldQuestion className="h-3.5 w-3.5" strokeWidth={2} />
          Already verifying credentials?{' '}
          <Link to="/sign-in" className="font-semibold text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </main>
    </div>
  )
}
