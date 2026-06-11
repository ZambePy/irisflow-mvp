import { useEffect, useState } from 'react'
import { useGazeSocket } from '../context/GazeSocketContext'
import { DWELL_TIME_MS } from '../theme/lumina'

export default function GazeCursor() {
  const { gazePoint } = useGazeSocket()
  const [active, setActive] = useState(false)

  useEffect(() => {
    const handleMove = (e) => {
      const el = document.elementFromPoint(e.clientX, e.clientY)
      setActive(!!el?.closest('button, a, [role="button"]'))
    }
    window.addEventListener('mousemove', handleMove)
    return () => window.removeEventListener('mousemove', handleMove)
  }, [])

  if (!gazePoint || gazePoint.x == null || gazePoint.y == null) return null

  const cursorX = gazePoint.x * window.innerWidth
  const cursorY = gazePoint.y * window.innerHeight

  return (
    <div
      className="fixed top-0 left-0 w-12 h-12 border-2 border-secondary rounded-full flex items-center justify-center pointer-events-none z-[9999]"
      style={{ left: cursorX, top: cursorY, transform: 'translate(-50%, -50%)' }}
    >
      <svg className="w-full h-full -rotate-90" viewBox="0 0 48 48">
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="transparent"
          stroke="#5bdac6"
          strokeWidth="2"
          style={{
            strokeDasharray: 126,
            strokeDashoffset: active ? 0 : 126,
            transition: active
              ? `stroke-dashoffset ${DWELL_TIME_MS}ms linear`
              : 'none',
          }}
        />
      </svg>
    </div>
  )
}
