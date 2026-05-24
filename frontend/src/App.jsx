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

function AppShell() {
  const { gazePoint } = useGazeSocket()

  return (
    <BrowserRouter>
      <GazeCursor position={gazePoint} />
      <TopBar />
      <SideNav />
      <EmergencyButton />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/phrases" element={<QuickPhrases />} />
        <Route path="/keyboard" element={<Keyboard />} />
        <Route path="/calibration" element={<Calibration />} />
      </Routes>
    </BrowserRouter>
  )
}

export default function App() {
  return (
    <GazeSocketProvider>
      <AppShell />
    </GazeSocketProvider>
  )
}
