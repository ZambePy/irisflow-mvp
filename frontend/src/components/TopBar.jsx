import { useGazeSocket } from '../context/GazeSocketContext'

export default function TopBar() {
  const { connected } = useGazeSocket()
  return (
    <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-margin-desktop h-hit-area-min bg-surface-container/60 backdrop-blur-xl border-b border-outline-variant/15">
      <div className="flex items-center gap-4">
        <span className="font-display text-headline-lg text-primary">IrisFlow</span>
        <div className="h-6 w-px bg-outline-variant/30" />
        <span className="font-label-caps text-label-caps text-on-surface-variant tracking-widest">GAZE READY</span>
      </div>
      <div className="flex items-center gap-gutter">
        <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20">
          <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>visibility</span>
          <span className="font-label-caps text-label-caps text-secondary">CALIBRATED</span>
        </div>
        <div className="flex items-center gap-6 text-on-surface-variant">
          <span className="material-symbols-outlined">wifi</span>
          <span className="material-symbols-outlined">battery_full</span>
        </div>
      </div>
    </header>
  )
}
