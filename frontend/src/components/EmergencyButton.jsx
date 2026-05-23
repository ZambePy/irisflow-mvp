import { useDwell } from '../hooks/useDwell'

export default function EmergencyButton() {
  const { onMouseEnter, onMouseLeave } = useDwell(() => {
    console.warn('[IrisFlow] EMERGÊNCIA ATIVADA')
    // TODO: emitir evento via WebSocket quando backend estiver ativo
    if (window.irisflow) {
      window.irisflow.send('emergency', { timestamp: Date.now() })
    }
  })

  return (
    <button
      className="emergency-pulse fixed bottom-6 right-6 z-[100] w-[320px] h-[160px] bg-error-container rounded-[2.5rem] flex flex-col items-center justify-center gap-2 border-2 border-error transition-all active:scale-95 group gaze-glow"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <span
        className="material-symbols-outlined text-on-error-container text-6xl group-hover:animate-pulse"
        style={{ fontVariationSettings: "'FILL' 1" }}
      >
        emergency
      </span>
      <span className="font-display text-headline-lg text-on-error-container tracking-tighter">
        EMERGENCY
      </span>
    </button>
  )
}
