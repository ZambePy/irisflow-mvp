import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { GazeSocketProvider, useGazeSocket } from './context/GazeSocketContext'
import TopBar from './components/TopBar'
import SideNav from './components/SideNav'
import GazeCursor from './components/GazeCursor'
import EmergencyButton from './components/EmergencyButton'
import Dashboard from './screens/Dashboard'
import QuickPhrases from './screens/QuickPhrases'
import Keyboard from './screens/Keyboard'
import Calibration from './screens/Calibration'
import Welcome from './screens/Welcome'
import ProfileSetup from './screens/ProfileSetup'
import Settings from './screens/Settings'

// Telas que usam o shell completo (topbar + sidebar + emergency)
function AppShell() {
  const { gazePoint, connected, calibrated } = useGazeSocket()
  return (
    <>
      <GazeCursor position={gazePoint} />
      <TopBar calibrated={calibrated} connected={connected} />
      <SideNav />
      <EmergencyButton />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/phrases" element={<QuickPhrases />} />
        <Route path="/keyboard" element={<Keyboard />} />
        <Route path="/calibration" element={<Calibration />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </>
  )
}

// Telas standalone (sem sidebar/topbar — fluxo de onboarding)
function OnboardingShell() {
  const { gazePoint } = useGazeSocket()
  return (
    <>
      <GazeCursor position={gazePoint} />
      <Routes>
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/profile-setup" element={<ProfileSetup />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <GazeSocketProvider>
      <BrowserRouter>
        <Routes>
          {/* Onboarding — sem shell */}
          <Route path="/welcome" element={
            <>
              <GazeCursor position={null} />
              <Welcome />
            </>
          } />
          <Route path="/profile-setup" element={
            <>
              <GazeCursor position={null} />
              <ProfileSetup />
            </>
          } />

          {/* App principal — com shell */}
          <Route path="/*" element={<AppShell />} />
        </Routes>
      </BrowserRouter>
    </GazeSocketProvider>
  )
}
