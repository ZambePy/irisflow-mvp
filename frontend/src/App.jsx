import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { GazeSocketProvider } from './context/GazeSocketContext'
import { useAppStore } from './store/appStore'
import { useGazeDwell } from './hooks/useGazeDwell'
import { API_BASE_URL } from './config/api'
import TopBar from './components/TopBar'
import SideNav from './components/SideNav'
import GazeCursor from './components/GazeCursor'
import Dashboard from './screens/Dashboard'
import QuickPhrases from './screens/QuickPhrases'
import PhraseList from './screens/PhraseList'
import Keyboard from './screens/Keyboard'
import Favorites from './screens/Favorites'
import Calibration from './screens/Calibration'
import Settings from './screens/Settings'
import Welcome from './screens/Welcome'
import ProfileSetup from './screens/ProfileSetup'
import OnboardingReady from './screens/OnboardingReady'

function AppShell() {
  useGazeDwell()

  return (
    <div className="flex h-screen overflow-hidden">
      <SideNav />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/"                  element={<Dashboard />} />
            <Route path="/phrases"           element={<QuickPhrases />} />
            <Route path="/phrases/:category" element={<PhraseList />} />
            <Route path="/keyboard"          element={<Keyboard />} />
            <Route path="/favorites"         element={<Favorites />} />
            <Route path="/calibration"       element={<Calibration />} />
            <Route path="/settings"          element={<Settings />} />
            <Route path="*"                  element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
      <GazeCursor />
    </div>
  )
}

function AppBootstrap() {
  const [ready, setReady] = useState(false)
  const [backendError, setBackendError] = useState('')
  const bootstrapAttemptRef = useRef(0)
  const setActiveProfile = useAppStore(state => state.setActiveProfile)
  const setDwellTime = useAppStore(state => state.setDwellTime)
  const setTrackingEngine = useAppStore(state => state.setTrackingEngine)
  const setCalibrated = useAppStore(state => state.setCalibrated)
  // useLocation garante re-render ao navegar (necessário para reler sessionStorage)
  useLocation()

  useEffect(() => {
    const attemptId = bootstrapAttemptRef.current + 1
    bootstrapAttemptRef.current = attemptId
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)
    let active = true

    const isCurrentAttempt = () => active && bootstrapAttemptRef.current === attemptId

    async function loadBootstrapState() {
      try {
        const profileRes = await fetch(`${API_BASE_URL}/profiles/last-used`, { signal: controller.signal })
        if (!profileRes.ok) throw new Error(`profiles HTTP ${profileRes.status}`)

        const profile = await profileRes.json()
        if (!isCurrentAttempt()) return

        setBackendError('')
        if (profile) {
          setActiveProfile(profile)
          setDwellTime(profile.dwell_time_ms ?? 1500)
          setTrackingEngine(profile.tracking_engine ?? 'mock')
        } else {
          setActiveProfile(null)
          setCalibrated(false)
        }

        try {
          const calibrationRes = await fetch(`${API_BASE_URL}/calibration/result`, { signal: controller.signal })
          if (!isCurrentAttempt()) return
          if (calibrationRes.ok) {
            const calibration = await calibrationRes.json()
            if (!isCurrentAttempt()) return
            setCalibrated(calibration?.status === 'calibrated')
          } else {
            setCalibrated(false)
          }
        } catch {
          if (!isCurrentAttempt()) return
          setCalibrated(false)
        }
      } catch (e) {
        if (!isCurrentAttempt()) return
        setBackendError(e.name === 'AbortError'
          ? 'Backend não respondeu dentro do tempo esperado.'
          : 'Backend desconectado. Inicie o servidor IrisFlow para continuar.')
        setActiveProfile(null)
        setCalibrated(false)
      } finally {
        clearTimeout(timeout)
        if (isCurrentAttempt()) {
          setReady(true)
        }
      }
    }

    loadBootstrapState()
    return () => {
      active = false
      controller.abort()
      clearTimeout(timeout)
    }
  }, [setActiveProfile, setCalibrated, setDwellTime, setTrackingEngine])

  if (!ready) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (backendError) {
    return (
      <div className="min-h-screen bg-background text-on-surface flex items-center justify-center p-8">
        <div className="max-w-xl text-center border border-error/30 bg-error/10 rounded-2xl p-10">
          <span className="material-symbols-outlined text-error text-5xl mb-4">wifi_off</span>
          <h1 className="font-headline-lg text-headline-lg text-error mb-4">Backend desconectado</h1>
          <p className="font-body-lg text-on-surface-variant mb-6">{backendError}</p>
          <p className="font-mono text-sm text-on-surface-variant">python -m irisflow.api.main</p>
        </div>
      </div>
    )
  }

  const profileSetupDone = sessionStorage.getItem('profile_setup_done') === 'true'

  return (
    <Routes>
      <Route path="/welcome"          element={<Welcome />} />
      <Route path="/profile-setup"    element={<ProfileSetup />} />
      <Route path="/onboarding-ready" element={<OnboardingReady />} />
      <Route path="/*" element={
        profileSetupDone ? <AppShell /> : <Navigate to="/profile-setup" replace />
      } />
    </Routes>
  )
}

export default function App() {
  return (
    <GazeSocketProvider>
      <BrowserRouter>
        <AppBootstrap />
      </BrowserRouter>
    </GazeSocketProvider>
  )
}
