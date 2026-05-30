import { BrowserRouter, Routes, Route } from 'react-router-dom'
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

// Shell principal — SideNav + TopBar em flex (sem offsets manuais nas telas)
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
          </Routes>
        </div>
      </div>
    </div>
  )
}

// Calibração — shell próprio (topbar e sidenav colapsada internos)
function CalibrationShell() {
  const { gazePoint } = useGazeSocket()
  return (
    <>
      <GazeCursor position={gazePoint} />
      <Calibration />
    </>
  )
}

export default function App() {
  return (
    <GazeSocketProvider>
      <BrowserRouter>
        <Routes>
          {/* Onboarding — sem shell */}
          <Route path="/welcome" element={<Welcome />} />
          <Route path="/profile-setup" element={<ProfileSetup />} />

          {/* Onboarding conclusão — sem shell */}
          <Route path="/onboarding-ready" element={<OnboardingReady />} />

          {/* Calibração — shell próprio */}
          <Route path="/calibration" element={<CalibrationShell />} />

          {/* App principal — com shell */}
          <Route path="/*" element={<AppShell />} />
        </Routes>
      </BrowserRouter>
    </GazeSocketProvider>
  )
}
