import { useEffect, useRef } from 'react'
import { AGENTS, TOOL_LABELS, isAgent, label } from '../agents'
import type { AgentEvent } from '../types'

function line(e: AgentEvent): string | null {
  switch (e.type) {
    case 'start': return `picked up: “${e.text}”`
    case 'said': return e.text ?? null
    case 'tool_call': return e.tool === 'delegate' || e.tool === 'final_result' ? null : `${TOOL_LABELS[e.tool ?? ''] ?? e.tool}`
    case 'delegate': return `handed off to ${label(e.to ?? '')}: “${e.text}”`
    case 'done': return `finished: ${e.text}`
    case 'run_start': return 'Ticket sent to the team.'
    case 'run_end': return 'Team run finished.'
    case 'run_error': return `Run failed: ${e.text}`
    case 'agent_stopped': return `stopped early: ${e.text}`
    default: return null
  }
}

export function Feed({ events }: { events: AgentEvent[] }) {
  const ref = useRef<HTMLOListElement>(null)
  const rows = events.filter((e) => e.type !== 'tool_result').map((e) => ({ e, text: line(e) })).filter((r) => r.text)
  useEffect(() => { ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' }) }, [rows.length])
  return (
    <section className="feed">
      <h2 className="section-title">Shift log <span>{rows.length} entries</span></h2>
      {rows.length === 0 ? (
        <p className="empty">Pick a ticket and send it to the team. Everything they say and every tool they touch lands here.</p>
      ) : (
        <ol ref={ref}>
          {rows.map(({ e, text }, i) => {
            const a = isAgent(e.agent) ? AGENTS[e.agent] : null
            return (
              <li key={i} className={`feed-row t-${e.type}`}>
                <time>{new Date(e.ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit' })}</time>
                <span className="feed-who" style={{ color: a?.color ?? '#6b6253', borderColor: a?.color ?? '#cfc6b4' }}>
                  {a ? a.monogram : '•'}
                </span>
                <span className="feed-text">
                  {a && <b style={{ color: a.color }}>{a.title}</b>} {e.type === 'tool_call' && <code>{e.tool}</code>} {text}
                </span>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
