import type { AgentEvent, Cash, PendingAction, Run, Ticket } from './types'

// The FastAPI backend from Problem 7.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.detail ?? `${res.status} ${res.statusText}`)
  return body as T
}

export const api = {
  health: () => request<{ ok: boolean; model: string; running: boolean }>('/api/health'),
  tickets: () => request<{ tickets: Ticket[] }>('/api/tickets').then((r) => r.tickets),
  runTicket: (id: number) => request<{ run_id: string }>(`/api/tickets/${id}/run`, { method: 'POST' }),
  run: (runId: string) => request<Run>(`/api/runs/${runId}`),
  events: (q: { runId?: string; ticketId?: number; limit?: number }) => {
    const p = new URLSearchParams({ limit: String(q.limit ?? 400) })
    if (q.runId) p.set('run_id', q.runId)
    if (q.ticketId != null) p.set('ticket_id', String(q.ticketId))
    return request<{ events: AgentEvent[] }>(`/api/events?${p}`).then((r) => r.events)
  },
  actions: (status = 'all') =>
    request<{ actions: PendingAction[] }>(`/api/actions?status=${status}`).then((r) => r.actions),
  approve: (action_id: number, approved_by: string, checked_by: string) =>
    request<Record<string, unknown>>('/api/approve', {
      method: 'POST',
      body: JSON.stringify({ action_id, approved_by, checked_by }),
    }),
  reject: (action_id: number, rejected_by: string, reason: string) =>
    request<Record<string, unknown>>('/api/reject', {
      method: 'POST',
      body: JSON.stringify({ action_id, rejected_by, reason }),
    }),
  cash: () => request<Cash>('/api/cash'),
  reset: () => request<{ ok: boolean }>('/api/reset', { method: 'POST' }),
}
