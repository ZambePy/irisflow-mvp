import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { useAppStore } from '../store/appStore'

const GazeSocketContext = createContext(null)

export function GazeSocketProvider({ children }) {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [engine, setEngine] = useState(null)
  const [gazePoint, setGazePoint] = useState({ x: 0, y: 0 })

  // Dwell: mapa por region_id
  const dwellHandlers = useRef({})
  const dwellRegions = useRef({})

  // calibrated e dwellTime vêm do appStore — fonte única de verdade (sem estado duplicado aqui)
  const calibrated = useAppStore(state => state.isCalibrated)
  const dwellTime = useAppStore(state => state.dwellTime)

  // Sincroniza dwellTime do perfil ativo ao backend sempre que mudar ou ao conectar
  useEffect(() => {
    if (connected && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'set_dwell_time', ms: dwellTime }))
    }
  }, [dwellTime, connected])

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
          case 'calibration_complete':
            // API Zustand imperativa — segura dentro de closure de effect
            useAppStore.getState().setCalibrated(true)
            break
          case 'dwell_progress':
            dwellHandlers.current[data.region_id]?.onProgress?.(data.progress)
            break
          case 'dwell_completed':
            dwellHandlers.current[data.region_id]?.onCompleted?.()
            break
          case 'dwell_cancelled':
            dwellHandlers.current[data.region_id]?.onCancelled?.()
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

  const sendMessage = useCallback((type, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }))
    } else {
      console.warn('[IrisFlow] WS não conectado — mensagem descartada:', type)
    }
  }, [])

  // Registra um elemento como região de dwell no backend.
  // rect: { x, y, w, h } em coordenadas de tela (screen-absolute).
  const registerDwellRegion = useCallback((id, rect, onCompleted, onProgress) => {
    dwellHandlers.current[id] = { onCompleted, onProgress }
    dwellRegions.current[id] = rect
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const regions = Object.entries(dwellRegions.current).map(([rid, r]) => ({ id: rid, ...r }))
      wsRef.current.send(JSON.stringify({ type: 'dwell_regions', regions }))
    }
  }, [])

  const unregisterDwellRegion = useCallback((id) => {
    delete dwellHandlers.current[id]
    delete dwellRegions.current[id]
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const regions = Object.entries(dwellRegions.current).map(([rid, r]) => ({ id: rid, ...r }))
      wsRef.current.send(JSON.stringify({ type: 'dwell_regions', regions }))
    }
  }, [])

  return (
    <GazeSocketContext.Provider value={{
      connected, engine, gazePoint, calibrated,
      sendMessage, registerDwellRegion, unregisterDwellRegion,
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
