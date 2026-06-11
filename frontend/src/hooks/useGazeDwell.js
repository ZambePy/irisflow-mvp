import { useEffect, useRef, useState } from 'react'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useAppStore } from '../store/appStore'

const COOLDOWN_MS = 900
const TARGET_SELECTOR = '[data-dwell-target]'

function getDwellTarget(point) {
  if (!point || !Number.isFinite(point.x) || !Number.isFinite(point.y)) return null
  if (point.x <= 0 && point.y <= 0) return null
  if (point.x < 0 || point.y < 0 || point.x > window.innerWidth || point.y > window.innerHeight) return null

  const el = document.elementFromPoint(point.x, point.y)
  const target = el?.closest?.(TARGET_SELECTOR)
  if (!target || target.disabled || target.getAttribute('aria-disabled') === 'true') return null
  return target
}

function clearTargetProgress(target) {
  if (!target) return
  target.style.setProperty('--gaze-dwell-progress', '0')
  target.removeAttribute('data-gaze-dwell-active')
}

export function useGazeDwell() {
  const { gazePoint } = useGazeSocket()
  const dwellTime = useAppStore((state) => state.dwellTime)
  const [progress, setProgress] = useState(0)

  const targetRef = useRef(null)
  const startedAtRef = useRef(0)
  const cooldownUntilRef = useRef(0)
  const rafRef = useRef(null)

  useEffect(() => {
    const nextTarget = getDwellTarget(gazePoint)
    const now = performance.now()

    if (!nextTarget || now < cooldownUntilRef.current) {
      clearTargetProgress(targetRef.current)
      targetRef.current = null
      startedAtRef.current = 0
      setProgress(0)
      return
    }

    if (nextTarget !== targetRef.current) {
      clearTargetProgress(targetRef.current)
      targetRef.current = nextTarget
      startedAtRef.current = now
      setProgress(0)
      nextTarget.setAttribute('data-gaze-dwell-active', 'true')
      nextTarget.style.setProperty('--gaze-dwell-progress', '0')
    }
  }, [gazePoint])

  useEffect(() => {
    const tick = () => {
      const target = targetRef.current
      if (!target || !startedAtRef.current) {
        rafRef.current = requestAnimationFrame(tick)
        return
      }

      const nextProgress = Math.min((performance.now() - startedAtRef.current) / dwellTime, 1)
      target.style.setProperty('--gaze-dwell-progress', String(nextProgress))
      setProgress(nextProgress)

      if (nextProgress >= 1) {
        cooldownUntilRef.current = performance.now() + COOLDOWN_MS
        clearTargetProgress(target)
        targetRef.current = null
        startedAtRef.current = 0
        setProgress(0)
        target.click()
      }

      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(rafRef.current)
      clearTargetProgress(targetRef.current)
    }
  }, [dwellTime])

  return {
    progress,
    target: targetRef.current,
  }
}
