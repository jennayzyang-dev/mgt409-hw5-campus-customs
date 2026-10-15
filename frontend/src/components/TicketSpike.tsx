import type { PendingAction, Ticket } from '../types'

const TYPE_LABEL: Record<string, string> = {
  customer_order: 'Customer order',
  rent_notice: 'Rent notice',
  price_override: 'Price override',
}

const time = (iso: string) =>
  new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York' })

function itemLine(t: Ticket) {
  if (t.sku) return `${t.qty ?? 1} × ${t.sku} · size ${t.size}`
  if (t.lease_id) return `Lease #${t.lease_id}`
  return t.subject
}

interface Props {
  tickets: Ticket[]
  selectedId: number | null
  runningTicketId: number | null
  pending: PendingAction[]
  onSelect: (id: number) => void
  onRun: (id: number) => void
}

export function TicketSpike({ tickets, selectedId, runningTicketId, pending, onSelect, onRun }: Props) {
  return (
    <section className="spike">
      <h2 className="section-title">Ticket spike <span>{tickets.filter((t) => t.state === 'open').length} open</span></h2>
      <div className="receipts">
        {tickets.map((t, i) => {
          const waiting = pending.filter((a) => a.ticket_id === t.id && a.status === 'pending').length
          const running = runningTicketId === t.id
          return (
            <article
              key={t.id}
              className={`receipt ${selectedId === t.id ? 'selected' : ''} ${t.state} ${running ? 'running' : ''}`}
              style={{ ['--tilt' as string]: `${[-1.2, 0.8, -0.5][i % 3]}deg` }}
              onClick={() => onSelect(t.id)}
            >
              <div className="receipt-head">
                <span className="receipt-no">No. {t.id}</span>
                <span className="receipt-time">{time(t.created_at)}</span>
              </div>
              <div className="receipt-type">{TYPE_LABEL[t.type] ?? t.type}</div>
              <div className="receipt-from">{t.requester}</div>
              <div className="receipt-item">{itemLine(t)}</div>
              <p className="receipt-note">“{(t.notes ?? '').split('\n')[0]}”</p>
              <div className="receipt-foot">
                <span className={`pill status-${t.status}`}>{t.status.replace('_', ' ')}</span>
                {waiting > 0 && <span className="pill waiting">{waiting} to sign</span>}
                {t.state === 'open' && (
                  <button
                    className="run-btn"
                    disabled={runningTicketId !== null}
                    onClick={(e) => { e.stopPropagation(); onRun(t.id) }}
                  >
                    {running ? 'Team on it…' : 'Send to team →'}
                  </button>
                )}
              </div>
              {t.state === 'resolved' && <div className="stamp">Resolved</div>}
            </article>
          )
        })}
      </div>
    </section>
  )
}
