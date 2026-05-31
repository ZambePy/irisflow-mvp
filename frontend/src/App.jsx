import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { GazeSocketProvider, useGazeSocket } from './context/GazeSocketContext'
import TopBar from './components/TopBar'
import SideNav from './components/SideNav'
import GazeCursor from './components/GazeCursor'
import Dashboard from './screens/Dashboard'
import QuickPhrases from './screens/QuickPhrases'
import PhraseList from './screens/PhraseList'
import Favorites from './screens/Favorites'
import Keyboard from './screens/Keyboard'
import Calibration from './screens/Calibration'
import Welcome from './screens/Welcome'
import ProfileSetup from './screens/ProfileSetup'
import Settings from './screens/Settings'
import OnboardingReady from './screens/OnboardingReady'

function AppShell() {
  const { gazePoint } = useGazeSocket()
  return (
    <div className="flex h-screen overflow-hidden bg-background text-on-surface">
      <GazeCursor position={gazePoint} />
      <SideNav />
      <div className="flex-grow flex flex-col min-w-0">
        <TopBar />
        <div className="flex-grow overflow-y-auto min-h-0">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/phrases" element={<QuickPhrases />} />
            <Route path="/phrases/:category" element={<PhraseList />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/keyboard" element={<Keyboard />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/calibration" element={<Calibration />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}

function AppBootstrap() {
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    fetch('http://localhost:8765/profiles/')
      .then((r) => r.json())
      .then((data) => {
        setStatus(Array.isArray(data) && data.length > 0 ? 'has-profile' : 'no-profile')
      })
      .catch(() => setStatus('no-profile'))
  }, [])

  if (status === 'loading') {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: '#0A0C10' }}>
        <div
          className="rounded-full animate-spin"
          style={{ width: 32, height: 32, border: '2px solid #5bdac6', borderTopColor: 'transparent' }}
        />
      </div>
    )
  }

  if (status === 'no-profile') {
    return <Navigate to="/welcome" replace />
  }

  return <AppShell />
}

export default function App() {
  return (
    <GazeSocketProvider>
      <BrowserRouter>
        <Routes>
          {/* Rotas sem shell */}
          <Route path="/welcome" element={<Welcome />} />
          <Route path="/profile-setup" element={<ProfileSetup />} />
          <Route path="/onboarding-ready" element={<OnboardingReady />} />

          {/* Todas as outras rotas passam pelo bootstrap */}
          <Route path="/*" element={<AppBootstrap />} />
        </Routes>
      </BrowserRouter>
    </GazeSocketProvider>
  )
}
