export type AgentName = 'boss' | 'inventory' | 'accounting' | 'facilities' | 'customer_service'

export interface Ticket {
  id: number
  type: string
  requester: string
  subject: string
  sku: string | null
  size: string | null
  qty: number | null
  lease_id: number | null
  invoice_id: number | null
  status: string
  state: 'open' | 'resolved'
  notes: string | null
  created_at: string
}

export interface AgentEvent {
  ts: string
  run_id: string | null
  agent: string | null
  type: 'start' | 'said' | 'tool_call' | 'tool_result' | 'delegate' | 'done' | 'run_start' | 'run_end'
    | 'run_error' | 'agent_stopped' | 'reset' | 'approve' | 'reject'
  text?: string | null
  tool?: string
  to?: string
  args?: Record<string, unknown> | null
  result?: unknown
  output?: Record<string, unknown>
  ticket_id?: number | null
}

export interface ApprovalRequest {
  kind: string
  action_id: number | null
  ticket_id: number | null
  ref: string
  amount: number | null
  reason: string
}

export interface BossReport {
  summary: string
  tickets: { ticket_id: number; status: string; owner: string; resolution: string; customer_reply: string | null }[]
  approvals_needed: ApprovalRequest[]
  cash_after_run: number | null
}

export interface Run {
  run_id: string
  ticket_id: number
  status: 'running' | 'done' | 'error'
  started_at: string
  finished_at?: string
  report: BossReport | null
  error: string | null
}

export interface PendingAction {
  id: number
  kind: 'invoice' | 'rent' | 'purchase'
  ref_id: number
  sku: string | null
  size: string | null
  qty: number | null
  amount: number
  ticket_id: number | null
  reason: string
  prepared_by: string
  status: 'pending' | 'approved' | 'rejected' | 'failed'
  created_at: string
  decided_by: string | null
}

export interface Cash {
  found: boolean
  name: string
  balance: number
  date: string
}
