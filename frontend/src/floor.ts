import { AGENTS, isAgent } from './agents'
import type { AgentEvent, AgentName, BossReport } from './types'

export type AgentState = 'idle' | 'working' | 'done'

export interface Station {
  name: AgentName
  state: AgentState
  task: string | null
  said: string | null
  currentTool: string | null
  tools: string[]
  toolCalls: number
  summary: string | null
  output: Record<string, unknown> | null
  calledBy: AgentName[]
}

export interface Handoff {
  from: AgentName
  to: AgentName
  task: string
  active: boolean
}

export interface FloorView {
  runId: string | null
  running: boolean
  stations: Record<AgentName, Station>
  handoffs: Handoff[]
  report: BossReport | null
  error: string | null
}

const blank = (name: AgentName): Station => ({
  name, state: 'idle', task: null, said: null, currentTool: null, tools: [], toolCalls: 0,
  summary: null, output: null, calledBy: [],
})

/** Replay one run's events into what each station is doing right now. */
export function buildFloor(events: AgentEvent[]): FloorView {
  const starts = events.filter((e) => e.type === 'run_start' && e.run_id)
  const runId = starts.length ? starts[starts.length - 1].run_id : null
  const stations = Object.fromEntries(
    (Object.keys(AGENTS) as AgentName[]).map((n) => [n, blank(n)]),
  ) as Record<AgentName, Station>
  const handoffs: Handoff[] = []
  let running = false
  let report: BossReport | null = null
  let error: string | null = null

  for (const e of events) {
    if (!runId || e.run_id !== runId) continue
    if (e.type === 'run_start') running = true
    if (e.type === 'run_end') {
      running = false
      const out = (e as unknown as { detail?: { output?: BossReport } }).detail?.output
      if (out && typeof out === 'object') report = out
    }
    if (e.type === 'run_error') { running = false; error = e.text ?? 'Run failed' }
    if (!isAgent(e.agent)) continue
    const s = stations[e.agent]
    switch (e.type) {
      case 'start':
        s.state = 'working'; s.task = e.text ?? null; s.currentTool = null; break
      case 'said':
        s.said = e.text ?? null; break
      case 'tool_call':
        if (e.tool && e.tool !== 'delegate') {
          s.currentTool = e.tool; s.toolCalls += 1
          if (!s.tools.includes(e.tool)) s.tools.push(e.tool)
        }
        break
      case 'delegate':
        if (isAgent(e.to)) {
          handoffs.push({ from: e.agent, to: e.to, task: e.text ?? '', active: true })
          if (!stations[e.to].calledBy.includes(e.agent)) stations[e.to].calledBy.push(e.agent)
          s.currentTool = 'delegate'
        }
        break
      case 'done':
        s.state = 'done'; s.currentTool = null
        s.summary = e.text ?? null
        s.output = (e.output as Record<string, unknown>) ?? null
        handoffs.forEach((h) => { if (h.to === e.agent) h.active = false })
        break
    }
  }
  if (!running) handoffs.forEach((h) => (h.active = false))
  return { runId, running, stations, handoffs, report, error }
}
