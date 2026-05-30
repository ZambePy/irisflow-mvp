import { useGazeSocket } from '../context/GazeSocketContext'

export default function TopBar() {
  const { connected, calibrated } = useGazeSocket()

  return (
    <header className="h-24 shrink-0 bg-surface-dim/80 backdrop-blur-xl border-b border-white/10 flex justify-between items-center px-margin-desktop w-full shadow-md z-40">
      {/* Status pills */}
      <div className="flex items-center gap-8">
        {connected && (
          <div className="flex items-center gap-3 bg-secondary/10 px-4 py-2 rounded-full border border-secondary/20">
            <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
            <span className="font-label-lg text-label-lg text-secondary">System Healthy</span>
          </div>
        )}
        {calibrated && (
          <div className="flex items-center gap-3 bg-primary/10 px-4 py-2 rounded-full border border-primary/20">
            <span className="material-symbols-outlined text-primary text-sm">target</span>
            <span className="font-label-lg text-label-lg text-primary">Calibration Active: 98% Accuracy</span>
          </div>
        )}
        {!connected && (
          <div className="flex items-center gap-3 bg-error/10 px-4 py-2 rounded-full border border-error/20">
            <span className="material-symbols-outlined text-error text-sm">wifi_off</span>
            <span className="font-label-lg text-label-lg text-error">Disconnected</span>
          </div>
        )}
      </div>

      {/* User info + icons */}
      <div className="flex items-center gap-6">
        <div className="text-right">
          <p className="font-label-lg text-label-lg text-on-surface">Alex Johnson</p>
          <p className="text-xs text-on-surface-variant">Iris ID: 992-IF</p>
        </div>
        <div className="flex gap-2">
          <button className="p-3 text-on-surface-variant hover:bg-white/5 rounded-full transition-all">
            <span className="material-symbols-outlined">visibility</span>
          </button>
          <button className="p-3 text-on-surface-variant hover:bg-white/5 rounded-full transition-all">
            <span className="material-symbols-outlined">sensors</span>
          </button>
        </div>
      </div>
    </header>
  )
}
