import { AGENTS, SPECIALISTS } from '../agents'
import type { FloorView } from '../floor'
import type { AgentName } from '../types'

export function ShiftReport({ view, ticketId }: { view: FloorView; ticketId: number | null }) {
  const order: AgentName[] = ['boss', ...SPECIALISTS]
  const worked = order.filter((n) => view.stations[n].state !== 'idle')
  const outcome = view.report?.tickets.find((t) => t.ticket_id === ticketId) ?? view.report?.tickets[0]
  if (!view.runId) return null
  return (
    <section className="report">
      <h2 className="section-title">Shift report <span>{view.running ? 'in progress' : 'what each agent did'}</span></h2>
      {view.report && (
        <div className="report-lead">
          <p>{view.report.summary}</p>
          {outcome?.customer_reply && (
            <blockquote className="reply-card">
              <div className="reply-label">Draft reply to the requester</div>
              {outcome.customer_reply}
            </blockquote>
          )}
        </div>
      )}
      <div className="report-grid">
        {worked.map((n) => {
          const s = view.stations[n]
          const a = AGENTS[n]
          return (
            <div key={n} className="report-card" style={{ ['--ink' as string]: a.color, ['--tint' as string]: a.tint }}>
              <div className="report-who"><span className="monogram sm">{a.monogram}</span>{a.title}</div>
              <p>{s.summary ?? (s.state === 'working' ? 'Still working…' : '—')}</p>
              <div className="report-meta">
                {s.calledBy.length > 0 && <span>called by {s.calledBy.map((c) => AGENTS[c].title).join(', ')}</span>}
                <span>{s.toolCalls} tool call{s.toolCalls === 1 ? '' : 's'}</span>
              </div>
            </div>
          )
        })}
      </div>
      {view.error && <p className="error">{view.error}</p>}
    </section>
  )
}
