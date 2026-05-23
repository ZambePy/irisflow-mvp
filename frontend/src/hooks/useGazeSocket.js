import { useEffect, useRef, useState } from 'react'

export function useGazeSocket() {
  const [gazePoint, setGazePoint] = useState({ x: 0, y: 0 })
  const [connected, setConnected] = useState(false)
  const [calibrated, setCalibrated] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    let mouseHandler = null

    const addMouseFallback = () => {
      mouseHandler = (e) => setGazePoint({ x: e.clientX, y: e.clientY })
      window.addEventListener('mousemove', mouseHandler)
    }

    try {
      const ws = new WebSocket('ws://localhost:8765/gaze')
      wsRef.current = ws

      ws.onopen = () => setConnected(true)

      ws.onclose = () => {
        setConnected(false)
        addMouseFallback()
      }

      ws.onerror = () => addMouseFallback()

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        if (data.type === 'gaze') setGazePoint({ x: data.x, y: data.y })
        if (data.type === 'calibrated') setCalibrated(true)
      }
    } catch {
      setConnected(false)
      addMouseFallback()
    }

    return () => {
      wsRef.current?.close()
      if (mouseHandler) window.removeEventListener('mousemove', mouseHandler)
    }
  }, [])

  return { gazePoint, connected, calibrated }
}
