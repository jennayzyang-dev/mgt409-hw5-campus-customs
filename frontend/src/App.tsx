import { useCallback, useEffect, useMemo, useState } from 'react'
import { API_URL, api } from './api'
import { Feed } from './components/Feed'
import { Floor } from './components/Floor'
import { ShiftReport } from './components/ShiftReport'
import { SignOff } from './components/SignOff'
import { TicketSpike } from './components/TicketSpike'
import { Till } from './components/Till'
import { buildFloor } from './floor'
import type { AgentEvent, Cash, PendingAction, Ticket } from './types'

const FAST = 1500 // poll while the team is working
const SLOW = 6000

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [actions, setActions] = useState<PendingAction[]>([])
  const [runningTicketId, setRunningTicketId] = useState<number | null>(null)
  const [online, setOnline] = useState<boolean | null>(null)
  const [toast, setToast] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const flash = (kind: 'ok' | 'err', text: string) => {
    setToast({ kind, text })
    setTimeout(() => setToast(null), 4500)
  }

  const refreshShop = useCallback(async () => {
    try {
      const [t, c, a, h] = await Promise.all([api.tickets(), api.cash(), api.actions('all'), api.health()])
      setTickets(t)
      setCash(c)
      setActions(a)
      setOnline(true)
      if (!h.running) setRunningTicketId(null)
      setSelectedId((cur) => cur ?? t.find((x) => x.state === 'open')?.id ?? t[0]?.id ?? null)
    } catch {
      setOnline(false)
    }
  }, [])

  const refreshEvents = useCallback(async () => {
    if (selectedId == null) return
    try {
      setEvents(await api.events({ ticketId: selectedId }))
    } catch { /* shown by the offline banner */ }
  }, [selectedId])

  const view = useMemo(() => buildFloor(events), [events])
  const working = runningTicketId !== null || view.running

  useEffect(() => { refreshShop() }, [refreshShop])
  useEffect(() => { refreshEvents() }, [refreshEvents])
  useEffect(() => {
    const id = setInterval(() => { refreshShop(); refreshEvents() }, working ? FAST : SLOW)
    return () => clearInterval(id)
  }, [working, refreshShop, refreshEvents])

  // when the selected ticket's run finishes, pull the final shop state once more
  useEffect(() => {
    if (!view.running && runningTicketId === selectedId && view.report) {
      setRunningTicketId(null)
      refreshShop()
      flash('ok', `Ticket ${selectedId} is done. Check the shift report and the sign-off tray.`)
    }
  }, [view.running, view.report, runningTicketId, selectedId, refreshShop])

  const run = async (id: number) => {
    try {
      setSelectedId(id)
      setRunningTicketId(id)
      await api.runTicket(id)
      setTimeout(refreshEvents, 400)
    } catch (e) {
      setRunningTicketId(null)
      flash('err', (e as Error).message)
    }
  }

  const approve = async (id: number, maker: string, checker: string) => {
    try {
      const r = await api.approve(id, maker, checker)
      flash('ok', r.new_balance != null ? `Paid. Till now holds $${Number(r.new_balance).toLocaleString()}.` : 'Purchase order approved.')
    } catch (e) {
      flash('err', (e as Error).message)
    }
    refreshShop()
  }

  const reject = async (id: number, by: string) => {
    try { await api.reject(id, by, 'Rejected on the desk'); flash('ok', 'Slip rejected. Nothing was paid.') }
    catch (e) { flash('err', (e as Error).message) }
    refreshShop()
  }

  const reset = async () => {
    if (!confirm('Reset the shop database to its original values? The audit trail is kept.')) return
    try { await api.reset(); setEvents([]); flash('ok', 'Fresh day: the database is back to the original values.') }
    catch (e) { flash('err', (e as Error).message) }
    refreshShop()
  }

  const selected = tickets.find((t) => t.id === selectedId)
  const pendingTotal = actions.filter((a) => a.status === 'pending' && a.kind !== 'purchase').reduce((s, a) => s + a.amount, 0)

  return (
    <div className="desk">
      <header className="sign">
        <div className="sign-mark">CC</div>
        <div className="sign-words">
          <h1>Campus Customs</h1>
          <p>The Desk · Chapel Street · New Haven</p>
        </div>
        <div className="sign-right">
          <span className={`status-dot ${online === false ? 'off' : working ? 'busy' : 'on'}`} />
          <span className="sign-status">
            {online === false ? `Backend offline (${API_URL})` : working ? 'Team is working' : 'Shop is open'}
          </span>
          <span className="sign-date">Business day {cash?.date ?? '—'}</span>
          <button className="ghost" onClick={reset} disabled={working}>Reset day</button>
        </div>
      </header>

      {online === false && (
        <div className="banner">
          Can't reach the backend at <code>{API_URL}</code>. Start it from <code>backend/</code> with{' '}
          <code>uvicorn main:app --reload --port 8000</code>.
        </div>
      )}

      <main className="layout">
        <TicketSpike
          tickets={tickets}
          selectedId={selectedId}
          runningTicketId={runningTicketId ?? (view.running ? selectedId : null)}
          pending={actions}
          onSelect={setSelectedId}
          onRun={run}
        />

        <div className="center">
          <Floor
            view={view}
            ticketLabel={selected ? `Ticket ${selected.id} · ${selected.requester}` : 'No ticket selected'}
          />
          <ShiftReport view={view} ticketId={selectedId} />
          <Feed events={events.filter((e) => e.run_id === view.runId)} />
        </div>

        <aside className="right">
          <Till cash={cash} pendingTotal={pendingTotal} />
          <SignOff actions={actions} onApprove={approve} onReject={reject} />
        </aside>
      </main>

      {toast && <div className={`toast ${toast.kind}`}>{toast.text}</div>}
    </div>
  )
}
