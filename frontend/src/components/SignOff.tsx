import { useState } from 'react'
import { AGENTS, isAgent, money } from '../agents'
import type { PendingAction } from '../types'

function what(a: PendingAction) {
  if (a.kind === 'invoice') return `Pay invoice #${a.ref_id}`
  if (a.kind === 'rent') return `Pay rent · lease #${a.ref_id}`
  return `Order ${a.qty} × ${a.sku} size ${a.size}`
}

interface Props {
  actions: PendingAction[]
  onApprove: (id: number, maker: string, checker: string) => Promise<void>
  onReject: (id: number, by: string) => Promise<void>
}

export function SignOff({ actions, onApprove, onReject }: Props) {
  const [maker, setMaker] = useState(() => localStorage.getItem('cc.maker') ?? '')
  const [checker, setChecker] = useState(() => localStorage.getItem('cc.checker') ?? '')
  const [busy, setBusy] = useState<number | null>(null)
  const pending = actions.filter((a) => a.status === 'pending')
  const signed = actions.filter((a) => a.status !== 'pending').slice(-4).reverse()
  const same = maker.trim() !== '' && maker.trim().toLowerCase() === checker.trim().toLowerCase()
  const ready = maker.trim() !== '' && checker.trim() !== '' && !same

  const save = (k: string, v: string, set: (v: string) => void) => { set(v); localStorage.setItem(k, v) }

  return (
    <section className="signoff">
      <h2 className="section-title">Sign-off tray <span>{pending.length} waiting</span></h2>
      <p className="signoff-help">Agents only prepare money moves. Two different people sign here before cash leaves the till.</p>
      <div className="signers">
        <label>Maker<input value={maker} placeholder="your name" onChange={(e) => save('cc.maker', e.target.value, setMaker)} /></label>
        <label>Checker<input value={checker} placeholder="a second person" onChange={(e) => save('cc.checker', e.target.value, setChecker)} /></label>
      </div>
      {same && <p className="error small">Maker and checker have to be two different people.</p>}

      {pending.length === 0 && <p className="empty">Nothing waiting. When an agent prepares a payment or purchase it shows up here.</p>}
      {pending.map((a) => {
        const by = isAgent(a.prepared_by) ? AGENTS[a.prepared_by] : null
        return (
          <div key={a.id} className={`slip kind-${a.kind}`}>
            <div className="slip-top">
              <span className="slip-what">{what(a)}</span>
              <span className="slip-amt">{money(a.amount)}</span>
            </div>
            <div className="slip-meta">
              Ticket {a.ticket_id ?? '—'} · prepared by{' '}
              <b style={{ color: by?.color }}>{by?.title ?? a.prepared_by}</b>
              {a.kind === 'purchase' && ' · creates a vendor bill, no cash yet'}
            </div>
            <p className="slip-reason">{a.reason}</p>
            <div className="slip-actions">
              <button
                className="approve"
                disabled={!ready || busy === a.id}
                onClick={async () => { setBusy(a.id); try { await onApprove(a.id, maker.trim(), checker.trim()) } finally { setBusy(null) } }}
              >
                {busy === a.id ? 'Signing…' : a.kind === 'purchase' ? 'Approve order' : 'Approve & pay'}
              </button>
              <button
                className="reject"
                disabled={!maker.trim() || busy === a.id}
                onClick={async () => { setBusy(a.id); try { await onReject(a.id, maker.trim()) } finally { setBusy(null) } }}
              >
                Reject
              </button>
            </div>
          </div>
        )
      })}

      {signed.length > 0 && (
        <div className="signed">
          {signed.map((a) => (
            <div key={a.id} className={`signed-row ${a.status}`}>
              <span>{what(a)}</span>
              <span>{money(a.amount)}</span>
              <span className="signed-stamp">{a.status === 'approved' ? (a.kind === 'purchase' ? 'ordered' : 'paid') : a.status}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
