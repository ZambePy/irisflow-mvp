import { useRef, useCallback } from 'react'
import { useAppStore } from '../store/appStore'
import { DWELL_TIME_MS } from '../theme/lumina'

export function useDwell(onActivate, dwellTime) {
  const timerRef = useRef(null)
  const storeDwellTime = useAppStore(state => state.dwellTime)
  const effectiveDwellTime = dwellTime ?? storeDwellTime ?? DWELL_TIME_MS

  const onMouseEnter = useCallback(() => {
    timerRef.current = setTimeout(() => {
      onActivate()
    }, effectiveDwellTime)
  }, [onActivate, effectiveDwellTime])

  const onMouseLeave = useCallback(() => {
    clearTimeout(timerRef.current)
  }, [])

  return { onMouseEnter, onMouseLeave }
}
