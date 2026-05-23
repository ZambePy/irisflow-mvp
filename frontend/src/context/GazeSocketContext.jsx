import { createContext, useContext, useEffect, useRef, useState } from 'react'

const GazeSocketContext = createContext(null)

export function GazeSocketProvider({ children }) {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [engine, setEngine] = useState(null)
  const [gazePoint, setGazePoint] = useState({ x: 0, y: 0 })
  const [calibrated, setCalibrated] = useState(false)

  const dwellCallbacks = useRef({})

  useEffect(() => {
    let timeoutId = null
    let destroyed = false

    const connect = () => {
      const ws = new WebSocket('ws://localhost:8765/ws')
      wsRef.current = ws

      ws.onopen = () => {
        if (destroyed) { ws.close(); return }
        console.log('[IrisFlow] Backend conectado')
        setConnected(true)
        ws.send(JSON.stringify({ type: 'start_tracking', engine: 'mock' }))
      }

      ws.onclose = () => {
        if (destroyed) return
        console.log('[IrisFlow] Backend desconectado — reconectando em 3s')
        setConnected(false)
        setEngine(null)
        timeoutId = setTimeout(connect, 3000)
      }

      ws.onerror = (e) => {
        if (destroyed) return
        console.warn('[IrisFlow] WebSocket error:', e)
      }

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        switch (data.type) {
          case 'gaze':
            setGazePoint({ x: data.x, y: data.y })
            break
          case 'tracking_status':
            setConnected(data.running)
            setEngine(data.engine)
            console.log('[IrisFlow] Engine:', data.engine)
            break
          case 'dwell_progress':
            dwellCallbacks.current.onProgress?.(data.region_id, data.progress)
            break
          case 'dwell_completed':
            dwellCallbacks.current.onCompleted?.(data.region_id)
            break
          case 'dwell_cancelled':
            dwellCallbacks.current.onCancelled?.(data.region_id)
            break
          case 'error':
            console.error('[IrisFlow]', data.message)
            break
        }
      }
    }

    connect()

    return () => {
      destroyed = true
      clearTimeout(timeoutId)
      wsRef.current?.close()
    }
  }, [])

  const sendMessage = (type, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }))
    } else {
      console.warn('[IrisFlow] WS não conectado — mensagem descartada:', type)
    }
  }

  const registerDwellCallbacks = (callbacks) => {
    dwellCallbacks.current = callbacks
  }

  return (
    <GazeSocketContext.Provider value={{
      connected, engine, gazePoint, calibrated,
      sendMessage, registerDwellCallbacks,
    }}>
      {children}
    </GazeSocketContext.Provider>
  )
}

export function useGazeSocket() {
  const ctx = useContext(GazeSocketContext)
  if (!ctx) throw new Error('useGazeSocket deve ser usado dentro de GazeSocketProvider')
  return ctx
}
