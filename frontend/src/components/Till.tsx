import { useEffect, useRef, useState } from 'react'
import { money } from '../agents'
import type { Cash } from '../types'

const FLOOR = 300 // the shop's low-cash warning line

/** A register-style display that rolls down to the new balance after a payment. */
export function Till({ cash, pendingTotal }: { cash: Cash | null; pendingTotal: number }) {
  const target = cash?.balance ?? 0
  const [shown, setShown] = useState(target)
  const [dropped, setDropped] = useState<number | null>(null)
  const prev = useRef(target)

  useEffect(() => {
    const from = prev.current
    if (from === target) return
    if (target < from) setDropped(from - target)
    prev.current = target
    const start = performance.now()
    let raf = 0
    const tick = (t: number) => {
      const k = Math.min(1, (t - start) / 1400)
      setShown(from + (target - from) * (1 - Math.pow(1 - k, 3)))
      if (k < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    const clear = setTimeout(() => setDropped(null), 4000)
    return () => { cancelAnimationFrame(raf); clearTimeout(clear) }
  }, [target])

  const after = target - pendingTotal
  return (
    <section className="till">
      <div className="till-label">Checking · the till</div>
      <div className="till-screen">
        <span className="till-amount">{money(shown)}</span>
        {dropped != null && <span className="till-drop">−{money(dropped)}</span>}
      </div>
      <div className="till-sub">
        <span>as of {cash?.date ?? '—'}</span>
        {pendingTotal > 0 && (
          <span className={after < FLOOR ? 'warn' : ''}>
            if every waiting slip is signed: {money(after)}{after < FLOOR ? ` · under the ${money(FLOOR)} line` : ''}
          </span>
        )}
      </div>
    </section>
  )
}
