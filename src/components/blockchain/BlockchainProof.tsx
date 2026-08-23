import { Link2, ShieldCheck, ShieldAlert, ShieldQuestion, ExternalLink } from 'lucide-react'
import type { BlockchainVerificationResult, CredentialBlockchainInfo } from '../../types'
import { blockchainExplorerTxUrl, shortHash } from '../../lib/utils'

function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

function ExplorerLink({ network, txHash }: { network: string | null; txHash: string | null }) {
  const url = blockchainExplorerTxUrl(network, txHash)
  if (!url) return null
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-2 inline-flex items-center gap-1 text-[12px] font-semibold text-primary hover:underline"
    >
      View blockchain proof
      <ExternalLink className="h-3 w-3" />
    </a>
  )
}

/**
 * The result of a live verification check (Phase 9C) — one of four states.
 * Never claims "verified" beyond what the backend actually reported;
 * NOT_ANCHORED and UNAVAILABLE are explicitly not failures of the
 * credential itself, only of blockchain proof availability.
 */
export function VerificationBlockchainProof({ blockchain }: { blockchain: BlockchainVerificationResult | null | undefined }) {
  if (!blockchain) return null

  return (
    <div className="mt-5 space-y-2 border-t border-line pt-5 text-left">
      <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-faint">
        <Link2 className="h-3.5 w-3.5" strokeWidth={2.25} />
        Blockchain Proof
      </div>

      {blockchain.status === 'ANCHORED' && (
        <div className="rounded-lg border border-good-line bg-good-bg px-3.5 py-3 text-[13px]">
          <div className="flex items-center gap-1.5 font-semibold text-good">
            <ShieldCheck className="h-4 w-4" strokeWidth={2.25} />
            Blockchain proof verified
          </div>
          <dl className="mt-2 space-y-1 text-muted">
            {blockchain.network && (
              <div className="flex justify-between gap-3">
                <dt>Network</dt>
                <dd className="font-medium text-ink">Polygon Amoy</dd>
              </div>
            )}
            {blockchain.transaction_hash && (
              <div className="flex justify-between gap-3">
                <dt>Transaction</dt>
                <dd className="font-mono font-medium text-ink">{shortHash(blockchain.transaction_hash)}</dd>
              </div>
            )}
            {blockchain.anchored_at && (
              <div className="flex justify-between gap-3">
                <dt>Anchored</dt>
                <dd className="font-medium text-ink">{formatDate(blockchain.anchored_at)}</dd>
              </div>
            )}
          </dl>
          <ExplorerLink network={blockchain.network} txHash={blockchain.transaction_hash} />
        </div>
      )}

      {blockchain.status === 'NOT_ANCHORED' && (
        <div className="rounded-lg border border-line bg-canvas-2/50 px-3.5 py-3 text-[13px]">
          <div className="flex items-center gap-1.5 font-semibold text-muted">
            <ShieldQuestion className="h-4 w-4" strokeWidth={2.25} />
            Blockchain proof not available
          </div>
          <p className="mt-1 text-muted">This credential has not been anchored to the blockchain.</p>
        </div>
      )}

      {blockchain.status === 'MISMATCH' && (
        <div className="rounded-lg border border-bad-line bg-bad-bg px-3.5 py-3 text-[13px]">
          <div className="flex items-center gap-1.5 font-semibold text-bad">
            <ShieldAlert className="h-4 w-4" strokeWidth={2.25} />
            Blockchain hash mismatch
          </div>
          <p className="mt-1 text-muted">The credential data does not match its blockchain anchor.</p>
        </div>
      )}

      {blockchain.status === 'UNAVAILABLE' && (
        <div className="rounded-lg border border-warn-line bg-warn-bg px-3.5 py-3 text-[13px]">
          <div className="flex items-center gap-1.5 font-semibold text-warn">
            <ShieldQuestion className="h-4 w-4" strokeWidth={2.25} />
            Blockchain verification unavailable
          </div>
          <p className="mt-1 text-muted">The blockchain proof could not be checked at this time.</p>
        </div>
      )}

      <p className="pt-1 text-[11px] leading-relaxed text-faint">
        Blockchain proof confirms that this credential's hash was anchored and can be independently checked — it
        does not by itself prove the student's academic achievement.
      </p>
      <p className="text-[11px] leading-relaxed text-faint">
        Digital signatures prove who issued this credential and whether its signed data has changed. Blockchain
        anchoring adds an independent, immutable timestamped proof of the credential's hash, on a network CredChain
        doesn't control.
      </p>
    </div>
  )
}

/** Compact anchor status for a credential detail page (Phase 9D) — the stored anchor record, not a live re-check. */
export function CredentialBlockchainBadge({ blockchain }: { blockchain: CredentialBlockchainInfo | null | undefined }) {
  const isAnchored = blockchain?.status === 'anchored'

  return (
    <div className="w-full rounded-lg border border-line bg-canvas-2/40 px-3.5 py-3 text-[13px]">
      <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-faint">
        <Link2 className="h-3.5 w-3.5" strokeWidth={2.25} />
        Blockchain Proof
      </div>

      {isAnchored ? (
        <>
          <div className="flex items-center gap-1.5 font-semibold text-good">
            <ShieldCheck className="h-4 w-4" strokeWidth={2.25} />
            Anchored
          </div>
          <dl className="mt-2 space-y-1 text-muted">
            {blockchain?.network && (
              <div className="flex justify-between gap-3">
                <dt>Network</dt>
                <dd className="font-medium text-ink">Polygon Amoy</dd>
              </div>
            )}
            {blockchain?.transactionHash && (
              <div className="flex justify-between gap-3">
                <dt>Transaction</dt>
                <dd className="font-mono font-medium text-ink">{shortHash(blockchain.transactionHash)}</dd>
              </div>
            )}
          </dl>
          <ExplorerLink network={blockchain?.network ?? null} txHash={blockchain?.transactionHash ?? null} />
        </>
      ) : (
        <span className="font-medium text-muted">Not anchored</span>
      )}

      <p className="mt-2 text-[11px] leading-relaxed text-faint">
        Digital signatures prove who issued this credential and whether its signed data has changed. Blockchain
        anchoring adds an independent, immutable timestamped proof of the credential's hash, on a network CredChain
        doesn't control.
      </p>
    </div>
  )
}
