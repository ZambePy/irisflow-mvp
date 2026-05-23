import { useRef, useCallback } from 'react'
import { DWELL_TIME_MS } from '../theme/lumina'

export function useDwell(onActivate, dwellTime = DWELL_TIME_MS) {
  const timerRef = useRef(null)

  const onMouseEnter = useCallback(() => {
    timerRef.current = setTimeout(() => {
      onActivate()
    }, dwellTime)
  }, [onActivate, dwellTime])

  const onMouseLeave = useCallback(() => {
    clearTimeout(timerRef.current)
  }, [])

  return { onMouseEnter, onMouseLeave }
}
