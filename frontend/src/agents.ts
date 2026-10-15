import type { AgentName } from './types'

export interface AgentMeta {
  name: AgentName
  title: string
  monogram: string
  station: string // where they sit in the shop
  color: string
  tint: string
}

// Each agent gets its own ink color, monogram and "station" so you can tell who's talking at a glance.
export const AGENTS: Record<AgentName, AgentMeta> = {
  boss: { name: 'boss', title: 'Store Manager', monogram: 'B', station: 'Front desk', color: '#14284b', tint: '#e4e9f2' },
  inventory: { name: 'inventory', title: 'Inventory Lead', monogram: 'In', station: 'Stockroom', color: '#2f6b4f', tint: '#e2efe7' },
  accounting: { name: 'accounting', title: 'Bookkeeper', monogram: 'Ac', station: 'Back office', color: '#a8741a', tint: '#f6ecd6' },
  facilities: { name: 'facilities', title: 'Facilities', monogram: 'Fa', station: 'Chapel St. lease', color: '#9c3d2e', tint: '#f5e1dc' },
  customer_service: { name: 'customer_service', title: 'Customer Service', monogram: 'CS', station: 'Counter', color: '#7a4a8c', tint: '#efe3f3' },
}

export const SPECIALISTS: AgentName[] = ['inventory', 'accounting', 'facilities', 'customer_service']

export const isAgent = (a: string | null | undefined): a is AgentName => !!a && a in AGENTS

export const label = (a: string) => (isAgent(a) ? AGENTS[a].title : a)

// Friendly names for MCP tools in the live feed
export const TOOL_LABELS: Record<string, string> = {
  get_today: 'checked the date',
  list_open_tickets: 'pulled open tickets',
  list_tickets: 'pulled tickets',
  get_ticket: 'read the ticket',
  check_inventory: 'checked the shelf',
  list_inventory: 'counted every size',
  list_vendors: 'looked up vendors',
  get_invoice: 'pulled the invoice',
  get_lease: 'opened the lease',
  get_pricing: 'checked the price tag',
  get_cash_balance: 'checked the till',
  list_payments: 'read the payment ledger',
  list_pending_actions: 'checked the sign-off tray',
  prepare_payment: 'prepared a payment',
  prepare_purchase: 'prepared a purchase order',
  update_ticket: 'updated the ticket',
  delegate: 'handed off work',
}

export const money = (n: number | null | undefined) =>
  n == null ? '—' : n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
