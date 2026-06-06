import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { useAppStore } from '../store/appStore'
import { WS_URL } from '../config/api'

const GazeSocketContext = createContext(null)

export function GazeSocketProvider({ children }) {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [engine, setEngine] = useState(null)
  const [gazePoint, setGazePoint] = useState(null)
  const [trackingMessage, setTrackingMessage] = useState('')

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
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        if (destroyed) { ws.close(); return }
        console.log('[IrisFlow] Backend conectado')
        setConnected(true)
        setTrackingMessage('')
        ws.send(JSON.stringify({ type: 'client_ready' }))
      }

      ws.onclose = () => {
        if (destroyed) return
        console.log('[IrisFlow] Backend desconectado — reconectando em 3s')
        setConnected(false)
        setEngine(null)
        setTrackingMessage('')
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
            setGazePoint(data)
            break
          case 'tracking_status':
            setEngine(data.engine)
            setTrackingMessage(data.message || '')
            console.log('[IrisFlow] Tracking:', data.running, '— engine:', data.engine)
            break
          case 'emergency_activated':
            console.warn('[IrisFlow] Emergência activada pelo backend')
            break
          case 'error':
            setTrackingMessage(data.message || 'Erro no tracking')
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

  // Dwell via backend: implementado quando gaze real estiver ativo.
  // Por ora são no-ops — modo mock usa onMouseEnter/onMouseLeave local.
  const registerDwellRegion = useCallback(() => {}, [])
  const unregisterDwellRegion = useCallback(() => {}, [])

  return (
    <GazeSocketContext.Provider value={{
      connected, engine, gazePoint, calibrated,
      trackingMessage,
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
