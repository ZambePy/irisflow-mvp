import { useDwell } from '../hooks/useDwell'

export default function EmergencyButton() {
  const { onMouseEnter, onMouseLeave } = useDwell(() => alert('EMERGENCY'))
  return (
    <footer className="fixed bottom-0 left-0 w-full p-gutter flex justify-between items-end z-50 pointer-events-none">
      <div className="ml-80 glass-panel rounded-full px-8 py-4 flex items-center gap-6 border-t border-primary/20 pointer-events-auto">
        <span className="font-label-caps text-label-caps text-primary">IRISFLOW ASSISTIVE TECHNOLOGY</span>
        <div className="flex gap-4">
          <a className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary" href="#">SAFETY</a>
          <a className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary" href="#">PRIVACY</a>
        </div>
      </div>
      <button
        className="emergency-pulse w-[320px] h-[160px] bg-error-container rounded-[2.5rem] flex flex-col items-center justify-center gap-2 border-2 border-error pointer-events-auto transition-all active:scale-95 gaze-glow"
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        <span className="material-symbols-outlined text-on-error-container text-6xl">emergency</span>
        <span className="font-display text-headline-lg text-on-error-container tracking-tighter">EMERGENCY</span>
      </button>
    </footer>
  )
}
