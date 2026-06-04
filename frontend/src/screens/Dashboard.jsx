import { useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useAppStore } from '../store/appStore'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  .if-dwell {
    position: relative;
    overflow: hidden;
    transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.3s ease;
  }
  .if-ring-wrap {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 120px; height: 120px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 20;
  }
  .if-dwell:hover .if-ring-wrap { opacity: 1; }
  .if-ring-arc {
    fill: none;
    stroke: currentColor;
    stroke-width: 4;
    stroke-dasharray: 283;
    stroke-dashoffset: 283;
    transition: stroke-dashoffset 1.5s linear;
  }
  .if-dwell:hover .if-ring-arc { stroke-dashoffset: 0; }

  @keyframes if-breathe-blue {
    0%, 100% { box-shadow: 0 0 20px rgba(160, 202, 252, 0.2); }
    50%       { box-shadow: 0 0 40px rgba(160, 202, 252, 0.5); }
  }
  @keyframes if-breathe-teal {
    0%, 100% { box-shadow: 0 0 20px rgba(91, 218, 198, 0.15); }
    50%       { box-shadow: 0 0 40px rgba(91, 218, 198, 0.4); }
  }
  @keyframes if-breathe-red {
    0%, 100% { box-shadow: 0 0 20px rgba(255, 180, 171, 0.2); }
    50%       { box-shadow: 0 0 40px rgba(255, 180, 171, 0.5); }
  }
  .if-glow-blue { animation: if-breathe-blue 3s infinite ease-in-out; }
  .if-glow-teal { animation: if-breathe-teal 3s infinite ease-in-out; }
  .if-glow-red  { animation: if-breathe-red  3s infinite ease-in-out; }

  .if-cursor::after {
    content: '_';
    animation: if-blink 1s step-end infinite;
    color: #a0cafc;
    margin-left: 6px;
  }
  @keyframes if-blink {
    from, to { opacity: 1; }
    50%       { opacity: 0; }
  }

  @media (prefers-reduced-motion: reduce) {
    .if-dwell, .if-ring-arc,
    .if-glow-blue, .if-glow-teal, .if-glow-red {
      animation: none !important;
      transition: none !important;
    }
  }
`

function DwellRing({ color = 'currentColor' }) {
  return (
    <div className="if-ring-wrap">
      <svg viewBox="0 0 100 100" width="120" height="120">
        <circle className="if-ring-arc" style={{ color }} cx="50" cy="50" r="45" />
      </svg>
    </div>
  )
}

function GazeBtn({
  onClick,
  glowClass = '',
  className = '',
  style = {},
  dwellColor = 'currentColor',
  magnetic = false,
  children,
}) {
  const ref = useRef(null)
  const { onMouseEnter: dwellEnter, onMouseLeave: dwellLeave } = useDwell(onClick ?? (() => {}))

  function handleMouseMove(e) {
    if (!magnetic || !ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const moveX = (e.clientX - (rect.left + rect.width / 2)) * 0.15
    const moveY = (e.clientY - (rect.top + rect.height / 2)) * 0.15
    ref.current.style.transform = `translate(${moveX}px, ${moveY}px) scale(1.02)`
  }

  function handleMouseLeave(e) {
    if (magnetic && ref.current) ref.current.style.transform = 'translate(0, 0) scale(1)'
    dwellLeave(e)
  }

  return (
    <button
      ref={ref}
      className={`if-dwell group ${glowClass} ${className}`}
      style={style}
      onMouseEnter={dwellEnter}
      onMouseLeave={handleMouseLeave}
      onMouseMove={magnetic ? handleMouseMove : undefined}
      onClick={onClick}
    >
      {children}
      <DwellRing color={dwellColor} />
    </button>
  )
}

function FluidBg() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const handler = (e) => {
      const x = (e.clientX / window.innerWidth) * 100
      const y = (e.clientY / window.innerHeight) * 100
      el.style.background = `
        radial-gradient(circle at ${x}% ${y}%, rgba(31,78,121,0.15), transparent 50%),
        radial-gradient(circle at ${100 - x}% ${100 - y}%, rgba(0,166,147,0.1), transparent 40%),
        #0A0C10
      `
    }
    document.addEventListener('mousemove', handler)
    return () => document.removeEventListener('mousemove', handler)
  }, [])

  return (
    <div
      ref={ref}
      style={{
        position: 'fixed',
        top: 0, left: 0,
        width: '100%', height: '100%',
        zIndex: -1,
        pointerEvents: 'none',
        background:
          'radial-gradient(circle at 50% 50%, rgba(31,78,121,0.15), transparent 50%),' +
          'radial-gradient(circle at 80% 20%, rgba(0,166,147,0.1), transparent 40%)',
        transition: 'background 0.5s ease',
      }}
    />
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { sendMessage } = useGazeSocket()
  const activeMessage    = useAppStore(state => state.activeMessage)
  const setActiveMessage = useAppStore(state => state.setActiveMessage)

  const handleBackspace = useCallback(() => {
    setActiveMessage(useAppStore.getState().activeMessage.slice(0, -1))
  }, [setActiveMessage])

  const { onMouseEnter: bkspEnter, onMouseLeave: bkspLeave } = useDwell(handleBackspace)

  return (
    <>
      <style>{CSS}</style>
      <FluidBg />

      <div className="p-gutter-desktop space-y-gutter-desktop">

        {/* ── Barra de Mensagem ── */}
        <section className="glass-panel p-8 rounded-3xl shadow-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent" />
          <div className="relative flex items-center justify-between">
            <div className="flex flex-col">
              <span className="font-label-lg text-label-lg text-primary/70 mb-2 flex items-center gap-2 uppercase tracking-widest">
                <span className="material-symbols-outlined text-sm">edit_note</span>
                Communication
              </span>
              <div className="font-display-lg text-display-lg text-on-surface tracking-tight h-20 flex items-center">
                {activeMessage || 'Eu gostaria de'}
                <span className="if-cursor ml-2" />
              </div>
            </div>

            <button
              className="if-dwell w-20 h-20 bg-surface-container-highest rounded-2xl hover:bg-surface-bright transition-all flex items-center justify-center"
              onMouseEnter={bkspEnter}
              onMouseLeave={bkspLeave}
              onClick={handleBackspace}
            >
              <span className="material-symbols-outlined text-4xl">backspace</span>
              <DwellRing />
            </button>
          </div>
        </section>

        {/* ── Grade de Comunicação ── */}
        <div className="grid grid-cols-12 gap-gutter-desktop h-[50vh]">

          {/* SIM + NÃO */}
          <div className="col-span-8 grid grid-cols-2 gap-gutter-desktop">
            <GazeBtn
              onClick={() => sendMessage('speak', { text: 'SIM' })}
              glowClass="if-glow-blue"
              className="h-full bg-primary-container text-on-primary-container rounded-[2.5rem] flex flex-col items-center justify-center gap-6 border border-primary/20 transition-all duration-300"
              dwellColor="#a0cafc"
              magnetic
            >
              <span
                className="material-symbols-outlined text-[10rem] transition-transform duration-500 group-hover:scale-110"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
              <span className="font-display-lg text-display-lg tracking-tighter">SIM</span>
            </GazeBtn>

            <GazeBtn
              onClick={() => sendMessage('speak', { text: 'NÃO' })}
              glowClass="if-glow-red"
              className="h-full bg-error-container text-on-error-container rounded-[2.5rem] flex flex-col items-center justify-center gap-6 border border-error/20 transition-all duration-300"
              dwellColor="#ffb4ab"
              magnetic
            >
              <span
                className="material-symbols-outlined text-[10rem] transition-transform duration-500 group-hover:scale-110"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                cancel
              </span>
              <span className="font-display-lg text-display-lg tracking-tighter">NÃO</span>
            </GazeBtn>
          </div>

          {/* Teclado + Frases */}
          <div className="col-span-4 flex flex-col gap-gutter-desktop">
            <GazeBtn
              onClick={() => navigate('/keyboard')}
              glowClass="if-glow-teal"
              className="flex-grow glass-panel rounded-3xl flex flex-col items-center justify-center gap-4 transition-all"
              dwellColor="#5bdac6"
              magnetic
            >
              <span className="material-symbols-outlined text-6xl text-secondary transition-transform duration-500 group-hover:scale-110">
                keyboard
              </span>
              <span className="font-headline-md text-headline-md text-on-surface">Teclado</span>
            </GazeBtn>

            <GazeBtn
              onClick={() => navigate('/phrases')}
              glowClass="if-glow-teal"
              className="flex-grow glass-panel rounded-3xl flex flex-col items-center justify-center gap-4 transition-all"
              dwellColor="#5bdac6"
              magnetic
            >
              <span className="material-symbols-outlined text-6xl text-secondary transition-transform duration-500 group-hover:scale-110">
                chat
              </span>
              <span className="font-headline-md text-headline-md text-on-surface">Frases</span>
            </GazeBtn>
          </div>
        </div>

        {/* ── Linha Inferior ── */}
        <div className="grid grid-cols-12 gap-gutter-desktop pt-4 pb-8">

          {/* Calibrar */}
          <div className="col-span-3">
            <GazeBtn
              onClick={() => navigate('/calibration')}
              className="w-full bg-secondary/5 border border-secondary/20 text-secondary p-8 rounded-3xl flex items-center justify-center gap-4 hover:bg-secondary/10 transition-all"
              dwellColor="#5bdac6"
            >
              <span className="material-symbols-outlined text-4xl transition-transform duration-500 group-hover:scale-110">
                track_changes
              </span>
              <span className="font-headline-md text-headline-md">Calibrar</span>
            </GazeBtn>
          </div>

          {/* Círculo de Cuidado */}
          <div className="col-span-6 glass-panel rounded-3xl p-6 flex items-center gap-8">
            <div className="flex -space-x-4">
              <div
                className="w-12 h-12 rounded-full border-2 border-surface bg-primary-container flex items-center justify-center"
                style={{ zIndex: 3 }}
              >
                <span className="material-symbols-outlined text-on-surface" style={{ fontSize: '20px' }}>person</span>
              </div>
              <div
                className="w-12 h-12 rounded-full border-2 border-surface bg-secondary-container flex items-center justify-center"
                style={{ zIndex: 2 }}
              >
                <span className="material-symbols-outlined text-on-surface" style={{ fontSize: '20px' }}>person</span>
              </div>
              <div
                className="w-12 h-12 rounded-full border-2 border-surface bg-primary-container flex items-center justify-center text-xs font-bold text-on-surface"
                style={{ zIndex: 1 }}
              >
                +12
              </div>
            </div>
            <div className="flex-grow">
              <p className="font-label-lg text-label-lg text-on-surface">Círculo de Cuidado</p>
              <p className="text-on-surface-variant text-sm opacity-60">3 contatos online</p>
            </div>
            <GazeBtn
              onClick={() => sendMessage('speak', { text: 'Preciso de ajuda' })}
              className="bg-primary text-on-primary px-8 py-4 rounded-full font-bold hover:scale-105 transition-all"
              dwellColor="#003257"
            >
              CHAMAR AJUDA
            </GazeBtn>
          </div>

          {/* Sinal de Olhar */}
          <div className="col-span-3 glass-panel rounded-3xl p-6 flex flex-col justify-center">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-on-surface-variant tracking-widest">GAZE SIGNAL</span>
              <span className="text-secondary text-xs font-bold">STRONG</span>
            </div>
            <div className="w-full bg-white/5 rounded-full h-2">
              <div
                className="bg-secondary h-2 rounded-full"
                style={{ width: '85%', boxShadow: '0 0 15px rgba(91,218,198,0.6)' }}
              />
            </div>
          </div>

        </div>
      </div>
    </>
  )
}
