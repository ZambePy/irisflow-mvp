import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'
import { useAppStore } from '../store/appStore'

const CSS = `
  .cal-glass { background: rgba(30,32,36,0.6); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.1); }
  .cal-point-active { box-shadow: 0 0 20px 5px rgba(91,218,198,0.4); }
  @keyframes cal-pulse { 0%, 100% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.5); opacity: 0; } }
  .cal-pulse-ring { animation: cal-pulse 2s cubic-bezier(0.4,0,0.6,1) infinite; }
  @keyframes cal-pulse-slow { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.8; transform: scale(1.02); } }
  .cal-pulse-slow { animation: cal-pulse-slow 4s infinite ease-in-out; }
  .cal-dwell-bar { position:absolute; bottom:0; left:0; height:4px; width:0%; background:#5bdac6; transition:width 2s linear; }
  .cal-btn:hover .cal-dwell-bar { width:100%; }
  .cal-concluir-fill { position:absolute; inset:0; background:rgba(91,218,198,0.2); transform-origin:left; transform:scaleX(0); transition:transform 2s; }
  .cal-concluir:hover .cal-concluir-fill { transform:scaleX(1); }
  .slider-teal::-webkit-slider-thumb { -webkit-appearance:none; width:32px; height:32px; background:#5bdac6; border-radius:50%; cursor:pointer; box-shadow:0 0 15px rgba(91,218,198,0.5); transition:transform 0.2s; }
  .slider-teal::-webkit-slider-thumb:hover { transform:scale(1.2); }
`

// Phase 1: intro tips
const TIPS = [
  { icon: 'lightbulb', color: 'text-primary', bg: 'bg-primary/10 group-hover:bg-primary/20', title: 'Ambiente', desc: 'Ambiente bem iluminado' },
  { icon: 'straighten', color: 'text-secondary', bg: 'bg-secondary/10 group-hover:bg-secondary/20', title: 'Distância', desc: '50-70cm da tela' },
  { icon: 'visibility', color: 'text-tertiary', bg: 'bg-tertiary/10 group-hover:bg-tertiary/20', title: 'Foco', desc: 'Olhe direto para cada ponto' },
]

// Phase 2: 6 points positions within a 600x600 container
const POINT_POSITIONS = [
  { top: '0', left: '50%', transform: 'translateX(-50%)' },
  { top: '25%', right: '0', transform: 'translateY(-50%)' },
  { bottom: '25%', right: '0', transform: 'translateY(50%)' },
  { bottom: '0', left: '50%', transform: 'translateX(-50%)' },
  { bottom: '25%', left: '0', transform: 'translateY(50%)' },
  { top: '25%', left: '0', transform: 'translateY(-50%)' },
]

export default function Calibration() {
  const navigate = useNavigate()
  const { state: locationState } = useLocation()
  const setCalibrated = useAppStore((s) => s.setCalibrated)

  const [phase, setPhase] = useState('intro') // 'intro' | 'calibrating' | 'result'
  const [currentPoint, setCurrentPoint] = useState(0)
  const [accuracy] = useState(94)

  const fromOnboarding = locationState?.from === 'onboarding'
  const onboardingName = locationState?.name ?? ''

  const startCalibration = useCallback(() => {
    fetch('http://localhost:8765/calibration/start?engine=mock', { method: 'POST' }).catch(() => {})
    setCurrentPoint(0)
    setPhase('calibrating')
  }, [])

  const { onMouseEnter: iniciarEnter, onMouseLeave: iniciarLeave } = useDwell(startCalibration)

  useEffect(() => {
    if (phase !== 'calibrating') return
    const timer = setInterval(() => {
      setCurrentPoint((p) => {
        if (p >= 5) {
          clearInterval(timer)
          setTimeout(() => {
            setCalibrated(true)
            setPhase('result')
          }, 600)
          return p
        }
        return p + 1
      })
    }, 1500)
    return () => clearInterval(timer)
  }, [phase, setCalibrated])

  const handleConcluir = () => {
    if (fromOnboarding) {
      navigate('/onboarding-ready', { state: { accuracy, engine: 'IrisGazeNet', latency: '8ms', name: onboardingName } })
    } else {
      navigate('/')
    }
  }

  const { onMouseEnter: concluirEnter, onMouseLeave: concluirLeave } = useDwell(handleConcluir)

  const phaseLabel = phase === 'intro' ? 'FASE 1: INTRO' : phase === 'calibrating' ? 'FASE 2: CALIBRAÇÃO' : 'FASE 3: RESULTADO'

  return (
    <div className="bg-background text-on-surface font-body-md overflow-hidden h-screen flex flex-col">
      <style>{CSS}</style>

      {/* Header */}
      <header className="fixed top-0 left-0 w-full h-24 bg-surface-dim/80 backdrop-blur-xl border-b border-white/10 px-margin-desktop flex justify-between items-center z-50 shrink-0">
        <div className="flex items-center gap-8">
          <span className="text-headline-lg font-headline-lg font-bold text-primary tracking-tight">IrisFlow</span>
          <div className="px-4 py-1.5 bg-secondary/10 border border-secondary/30 rounded-full">
            <span className="font-label-lg text-label-lg text-secondary uppercase tracking-widest">CALIBRATION MODE</span>
          </div>
        </div>
        <nav className="hidden md:flex items-center gap-1">
          {['FASE 1: INTRO', 'FASE 2: CALIBRAÇÃO', 'FASE 3: RESULTADO'].map((label) => (
            <div key={label} className={`px-6 py-2 font-label-lg ${phaseLabel === label ? 'text-secondary font-bold border-b-2 border-secondary' : 'text-on-surface-variant opacity-40'}`}>
              {label}
            </div>
          ))}
        </nav>
        <button
          className="w-16 h-16 flex items-center justify-center hover:bg-white/5 rounded-full transition-all active:scale-95 group"
          onClick={() => navigate('/')}
        >
          <span className="material-symbols-outlined text-on-surface-variant group-hover:text-on-surface">close</span>
        </button>
      </header>

      <main className="flex-1 h-screen pt-24 pb-32 flex items-center justify-center overflow-hidden relative">

        {/* === PHASE: INTRO === */}
        {phase === 'intro' && (
          <div className="text-center max-w-6xl w-full px-margin-desktop flex flex-col items-center">
            <div className="mb-16">
              <h1 className="font-headline-lg text-display-lg text-primary mb-4">Calibração do Olhar</h1>
              <p className="font-body-lg text-on-surface-variant max-w-2xl mx-auto">
                Siga os pontos com o olhar. Mantenha a cabeça estável para garantir a máxima precisão no rastreamento.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-desktop w-full max-w-6xl mb-16">
              {TIPS.map((tip) => (
                <div key={tip.icon} className="cal-glass p-8 rounded-xl flex flex-col items-center text-center gap-6 hover:scale-[1.02] transition-transform duration-500 cursor-default group">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors ${tip.bg}`}>
                    <span className={`material-symbols-outlined ${tip.color} text-4xl`}>{tip.icon}</span>
                  </div>
                  <div>
                    <h3 className={`font-headline-md ${tip.color} mb-2`}>{tip.title}</h3>
                    <p className="font-body-md text-on-surface-variant">{tip.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col items-center gap-8">
              <button
                className="cal-btn relative min-w-[320px] h-16 bg-secondary-container text-on-secondary-container font-eye-track-label rounded-full px-12 overflow-hidden hover:shadow-[0_0_30px_rgba(91,218,198,0.2)] transition-all active:scale-95 shadow-[0_0_20px_rgba(0,166,147,0.3)]"
                onMouseEnter={iniciarEnter}
                onMouseLeave={iniciarLeave}
                onClick={startCalibration}
              >
                <span className="relative z-10 flex items-center justify-center gap-3">
                  INICIAR CALIBRAÇÃO
                  <span className="material-symbols-outlined text-2xl">arrow_forward</span>
                </span>
                <div className="cal-dwell-bar" />
              </button>
              <button
                className="font-label-lg text-on-surface-variant hover:text-primary transition-colors py-4 px-8 rounded-full hover:bg-white/5 flex items-center gap-2 group"
                onClick={() => navigate('/')}
              >
                Pular (usar anterior)
                <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">skip_next</span>
              </button>
            </div>
          </div>
        )}

        {/* === PHASE: CALIBRATING === */}
        {phase === 'calibrating' && (
          <>
            <div className="absolute inset-0 flex items-center justify-center" style={{ paddingTop: '96px', paddingBottom: '128px' }}>
              <div className="relative w-[600px] h-[600px]">
                {POINT_POSITIONS.map((pos, i) => {
                  const isDone = i < currentPoint
                  const isActive = i === currentPoint
                  return (
                    <div key={i} className="absolute flex items-center justify-center" style={pos}>
                      {isActive && (
                        <div className="absolute w-20 h-20 bg-secondary/20 rounded-full cal-pulse-ring" />
                      )}
                      <div className={`rounded-full transition-all duration-500 ${
                        isActive ? 'w-10 h-10 bg-secondary cal-point-active flex items-center justify-center z-10 scale-110' :
                        isDone ? 'w-4 h-4 bg-secondary/50' :
                        'w-8 h-8 border-2 border-white/10'
                      }`}>
                        {isActive && <div className="w-2 h-2 bg-on-secondary rounded-full" />}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="cal-glass px-12 py-10 rounded-[2rem] flex flex-col items-center gap-6 z-20 shadow-2xl">
              <div className="w-20 h-20 bg-primary-container rounded-full flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-[40px]" style={{ fontVariationSettings: "'FILL' 1" }}>visibility</span>
              </div>
              <div className="text-center">
                <span className="block font-eye-track-label text-eye-track-label text-secondary uppercase tracking-[0.2em] mb-2">FIXAÇÃO</span>
                <span className="block font-display-lg text-display-lg text-on-surface">{currentPoint + 1} / 6</span>
              </div>
              <p className="text-on-surface-variant font-body-md max-w-[240px] text-center opacity-70">
                Mantenha o olhar fixo no ponto pulsante até que ele se complete.
              </p>
            </div>

            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px]" />
            </div>
          </>
        )}

        {/* === PHASE: RESULT === */}
        {phase === 'result' && (
          <div className="flex flex-col items-center px-margin-desktop w-full max-w-5xl">
            <div className="relative flex flex-col items-center justify-center mb-16">
              <div className="relative w-72 h-72 rounded-full flex items-center justify-center border-4 border-secondary/20 bg-surface-container/30 backdrop-blur-2xl cal-pulse-slow" style={{ boxShadow: '0 0 40px 15px rgba(91,218,198,0.3)' }}>
                <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 288 288">
                  <circle fill="transparent" cx="144" cy="144" r="140" stroke="currentColor" strokeWidth="8" className="text-secondary/10" />
                  <circle fill="transparent" cx="144" cy="144" r="140" stroke="currentColor" strokeWidth="8" className="text-secondary"
                    strokeDasharray="880" strokeDashoffset={Math.round(880 * (1 - accuracy / 100))}
                    style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
                </svg>
                <div className="text-center z-10">
                  <span className="font-display-lg text-display-lg text-on-surface block leading-none">{accuracy}%</span>
                  <span className="font-eye-track-label text-eye-track-label text-secondary mt-2 block tracking-widest uppercase">Excelente</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter-desktop w-full mb-24">
              {[
                { icon: 'adjust', label: 'Pontos coletados', value: '6/6' },
                { icon: 'track_changes', label: 'Precisão', value: 'Alta' },
                { icon: 'check_circle', label: 'Status', value: 'Calibrado' },
              ].map((stat) => (
                <div key={stat.icon} className="border border-white/10 rounded-xl p-8 flex flex-col items-center text-center hover:scale-[1.02] transition-transform duration-300" style={{ background: 'linear-gradient(180deg, rgba(30,32,36,0.6) 0%, rgba(17,19,24,0.8) 100%)' }}>
                  <span className="material-symbols-outlined text-secondary text-4xl mb-4">{stat.icon}</span>
                  <p className="font-label-lg text-label-lg text-on-surface-variant mb-1">{stat.label}</p>
                  <p className="font-headline-md text-headline-md text-on-surface">{stat.value}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 h-32 bg-surface-container-lowest/80 backdrop-blur-md px-margin-desktop flex items-center justify-between border-t border-white/5">
        {phase === 'result' ? (
          <div className="flex justify-center items-center gap-8 w-full">
            <button
              className="cal-concluir relative min-w-[320px] h-16 bg-secondary-container text-on-secondary-container font-eye-track-label text-eye-track-label rounded-full flex items-center justify-center gap-4 transition-all duration-300 hover:scale-105 active:scale-95 overflow-hidden"
              style={{ boxShadow: '0 0 40px 15px rgba(91,218,198,0.3)' }}
              onMouseEnter={concluirEnter}
              onMouseLeave={concluirLeave}
              onClick={handleConcluir}
            >
              <div className="cal-concluir-fill" />
              <span className="relative z-10">CONCLUIR</span>
              <span className="material-symbols-outlined relative z-10">arrow_forward</span>
            </button>
            <button
              className="min-w-[240px] h-16 border-2 border-outline/30 text-on-surface-variant font-eye-track-label text-eye-track-label rounded-full flex items-center justify-center gap-4 transition-all duration-300 hover:bg-white/5 hover:border-outline hover:text-on-surface"
              onClick={startCalibration}
            >
              <span className="material-symbols-outlined">refresh</span>
              RECALIBRAR
            </button>
          </div>
        ) : (
          <>
            <div className="flex-1 max-w-3xl">
              <div className="flex justify-between mb-3">
                <span className="font-label-lg text-label-lg text-on-surface-variant uppercase tracking-wider">PROGRESSO DO PERFIL</span>
                <span className="font-label-lg text-label-lg text-secondary font-bold">
                  {phase === 'intro' ? '0%' : `${Math.round((currentPoint / 6) * 100)}%`}
                </span>
              </div>
              <div className="w-full h-3 bg-surface-container-highest rounded-full overflow-hidden">
                <div
                  className="h-full bg-secondary transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(91,218,198,0.4)]"
                  style={{ width: phase === 'intro' ? '0%' : `${Math.round((currentPoint / 6) * 100)}%` }}
                />
              </div>
            </div>
            <button
              className="ml-12 min-w-[200px] h-16 bg-surface-container-high border border-white/10 hover:border-secondary/50 hover:bg-surface-bright rounded-xl flex items-center justify-between px-8 transition-all duration-300 group active:scale-95"
              onClick={() => navigate('/')}
            >
              <span className="font-eye-track-label text-eye-track-label text-on-surface-variant group-hover:text-secondary transition-colors">PULAR</span>
              <span className="material-symbols-outlined text-on-surface-variant group-hover:text-secondary group-hover:translate-x-2 transition-all">fast_forward</span>
            </button>
          </>
        )}
      </footer>

      {/* Atmospheric background */}
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-secondary/5 blur-[120px] rounded-full -z-10 pointer-events-none" />
      <div className="fixed top-0 right-0 w-[400px] h-[400px] bg-primary/5 blur-[100px] rounded-full -z-10 pointer-events-none" />
    </div>
  )
}
