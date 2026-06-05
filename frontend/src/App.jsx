import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { GazeSocketProvider } from './context/GazeSocketContext'
import { useAppStore } from './store/appStore'
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
  const [hasProfile, setHasProfile] = useState(false)
  const activeProfile = useAppStore(state => state.activeProfile)
  // location.state?.from === 'onboarding' is set by ProfileSetup on navigate() — React Router
  // delivers this synchronously in the same render pass, avoiding Zustand timing issues.
  const location = useLocation()
  const comingFromOnboarding = location.state?.from === 'onboarding'

  useEffect(() => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 2000)

    fetch('http://localhost:8765/profiles/', { signal: controller.signal })
      .then(r => r.json())
      .then(data => {
        setHasProfile(Array.isArray(data) && data.length > 0)
      })
      .catch(() => {
        // backend offline ou timeout → vai para home sem onboarding
        setHasProfile(true)
      })
      .finally(() => {
        clearTimeout(timeout)
        setReady(true)
      })
  }, [])

  if (!ready) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-secondary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <Routes>
      {/* Onboarding — sem shell */}
      <Route path="/welcome"          element={<Welcome />} />
      <Route path="/profile-setup"    element={<ProfileSetup />} />
      <Route path="/onboarding-ready" element={<OnboardingReady />} />

      {/* App principal — com shell */}
      <Route path="/*" element={
        (hasProfile || !!activeProfile || comingFromOnboarding)
          ? <AppShell />
          : <Navigate to="/welcome" replace />
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
