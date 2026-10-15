import { AGENTS, SPECIALISTS, TOOL_LABELS } from '../agents'
import type { FloorView, Station } from '../floor'
import type { AgentName } from '../types'

function StationCard({ s, big }: { s: Station; big?: boolean }) {
  const a = AGENTS[s.name]
  const doing =
    s.state === 'working'
      ? s.currentTool
        ? TOOL_LABELS[s.currentTool] ?? s.currentTool
        : 'thinking…'
      : s.state === 'done'
        ? 'clocked out'
        : 'at the station'
  return (
    <div
      className={`station ${s.state} ${big ? 'big' : ''}`}
      style={{ ['--ink' as string]: a.color, ['--tint' as string]: a.tint }}
    >
      <div className="station-top">
        <div className="monogram">{a.monogram}</div>
        <div>
          <div className="station-title">{a.title}</div>
          <div className="station-where">{a.station}</div>
        </div>
        <div className={`lamp ${s.state}`} title={s.state} />
      </div>
      <div className="station-doing">
        <span className="doing-dot" /> {doing}
        {s.currentTool && s.currentTool !== 'delegate' && s.state === 'working' && (
          <code className="tool-chip">{s.currentTool}</code>
        )}
      </div>
      {s.said && <div className="bubble">{s.said}</div>}
      {!s.said && s.task && s.state === 'working' && <div className="bubble task">“{s.task}”</div>}
      {s.state === 'idle' && <div className="station-idle">Not called on this ticket</div>}
      {s.tools.length > 0 && (
        <div className="tools-used">
          {s.tools.map((t) => <code key={t}>{t}</code>)}
        </div>
      )}
    </div>
  )
}

// x position (in %) of each specialist under the boss, for the hand-off wires
const X: Record<AgentName, number> = { boss: 50, inventory: 12.5, accounting: 37.5, facilities: 62.5, customer_service: 87.5 }

export function Floor({ view, ticketLabel }: { view: FloorView; ticketLabel: string }) {
  const { stations, handoffs } = view
  return (
    <section className="floor">
      <h2 className="section-title">
        The floor <span>{ticketLabel}</span>
        {view.running && <em className="live">● live</em>}
      </h2>
      <div className="floor-boss">
        <StationCard s={stations.boss} big />
      </div>
      <svg className="wires" viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden>
        {SPECIALISTS.map((n) => {
          const used = handoffs.filter((h) => h.to === n)
          const active = used.some((h) => h.active)
          const fromBoss = used.some((h) => h.from === 'boss')
          return (
            <path
              key={n}
              d={`M 50 0 C 50 15, ${X[n]} 15, ${X[n]} 30`}
              className={`wire ${used.length ? 'used' : ''} ${active ? 'active' : ''} ${fromBoss ? '' : 'side'}`}
              style={{ ['--ink' as string]: AGENTS[n].color }}
              vectorEffect="non-scaling-stroke"
            />
          )
        })}
      </svg>
      <div className="floor-row">
        {SPECIALISTS.map((n) => (
          <StationCard key={n} s={stations[n]} />
        ))}
      </div>
      {handoffs.length > 0 && (
        <div className="handoffs">
          {handoffs.map((h, i) => (
            <span key={i} className={`handoff ${h.active ? 'active' : ''}`} title={h.task}>
              <b style={{ color: AGENTS[h.from].color }}>{AGENTS[h.from].title}</b> →{' '}
              <b style={{ color: AGENTS[h.to].color }}>{AGENTS[h.to].title}</b>
            </span>
          ))}
        </div>
      )}
    </section>
  )
}
