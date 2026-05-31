import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'
import { useAppStore } from '../store/appStore'

const CSS = `
  @keyframes cal-outer-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.5); }
  }
  .cal-outer-pulse { animation: cal-outer-pulse 1.5s ease-in-out infinite; }
  @keyframes cal-progress {
    from { stroke-dashoffset: 50.27; }
    to { stroke-dashoffset: 0; }
  }
  .cal-progress-fill { animation: cal-progress 2s linear forwards; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .cal-spin { animation: spin 1s linear infinite; }
  @keyframes cal-fade-in { from { opacity: 0; } to { opacity: 1; } }
  .cal-fade-in { animation: cal-fade-in 0.2s ease-out forwards; }
  @keyframes cal-pulse-slow { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.8; transform: scale(1.02); } }
  .cal-pulse-slow { animation: cal-pulse-slow 4s infinite ease-in-out; }
  .cal-glass { background: rgba(30,32,36,0.6); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.1); }
  .cal-concluir-fill { position:absolute; inset:0; background:rgba(91,218,218,0.2); transform-origin:left; transform:scaleX(0); transition:transform 2s; }
  .cal-concluir:hover .cal-concluir-fill { transform:scaleX(1); }
  .cal-btn .cal-dwell-bar { position:absolute; bottom:0; left:0; height:4px; width:0%; background:#5bdac6; transition:width 2s linear; }
  .cal-btn:hover .cal-dwell-bar { width:100%; }
`

const BASE_POINTS = [
  { x: 0.1, y: 0.1 },
  { x: 0.5, y: 0.1 },
  { x: 0.9, y: 0.1 },
  { x: 0.1, y: 0.9 },
  { x: 0.5, y: 0.9 },
  { x: 0.9, y: 0.9 },
]

function fisherYates(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

const TIPS = [
  { icon: 'lightbulb', color: 'text-primary', bg: 'bg-primary/10 group-hover:bg-primary/20', title: 'Ambiente', desc: 'Ambiente bem iluminado' },
  { icon: 'straighten', color: 'text-secondary', bg: 'bg-secondary/10 group-hover:bg-secondary/20', title: 'Distância', desc: '50-70cm da tela' },
  { icon: 'visibility', color: 'text-tertiary', bg: 'bg-tertiary/10 group-hover:bg-tertiary/20', title: 'Foco', desc: 'Olhe direto para cada ponto' },
]

function CalDot({ point, collecting }) {
  const px = Math.round(point.x * window.innerWidth)
  const py = Math.round(point.y * window.innerHeight)
  return (
    <div
      className="cal-fade-in"
      style={{ position: 'absolute', left: px, top: py, width: 60, height: 60, transform: 'translate(-50%, -50%)' }}
    >
      {/* Outer pulsing ring */}
      <div
        className={`w-full h-full rounded-full ${collecting ? '' : 'cal-outer-pulse'}`}
        style={{ border: '2px solid #5bdac6', opacity: 0.3 }}
      />
      {/* Inner circle or progress ring */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
        style={{ width: 20, height: 20 }}
      >
        {collecting ? (
          <svg viewBox="0 0 20 20" className="w-full h-full -rotate-90">
            <circle cx="10" cy="10" r="8" fill="none" stroke="#5bdac6" strokeWidth="2" strokeOpacity="0.2" />
            <circle
              cx="10" cy="10" r="8" fill="none" stroke="#5bdac6" strokeWidth="2"
              strokeDasharray="50.27" strokeDashoffset="50.27"
              className="cal-progress-fill"
            />
          </svg>
        ) : (
          <div className="w-full h-full rounded-full" style={{ background: '#5bdac6' }} />
        )}
      </div>
    </div>
  )
}

export default function Calibration() {
  const navigate = useNavigate()
  const { state: locationState } = useLocation()
  const setCalibrated = useAppStore((s) => s.setCalibrated)

  const [phase, setPhase] = useState('intro')
  const [shuffledPoints, setShuffledPoints] = useState([])
  const [currentPoint, setCurrentPoint] = useState(0)
  const [pointState, setPointState] = useState('idle')
  const [fitResult, setFitResult] = useState(null)
  const timerRef = useRef(null)

  const fromOnboarding = locationState?.from === 'onboarding'
  const onboardingName = locationState?.name ?? ''
  const accuracy = fitResult ? Math.round(fitResult.accuracy * 100) : 0

  useEffect(() => () => clearTimeout(timerRef.current), [])

  // Prepare → collect flow (auto, no user interaction)
  useEffect(() => {
    if (phase !== 'calibrating' || pointState !== 'preparing' || shuffledPoints.length === 0) return

    let active = true

    timerRef.current = setTimeout(async () => {
      if (!active) return
      setPointState('collecting')

      const pt = shuffledPoints[currentPoint]
      const px = Math.round(pt.x * window.innerWidth)
      const py = Math.round(pt.y * window.innerHeight)

      try {
        const res = await fetch('http://localhost:8765/calibration/collect_point', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ point_index: currentPoint, expected_x: px, expected_y: py }),
        })
        const data = await res.json()
        if (!active) return
        if (data.ready) {
          if (currentPoint >= 5) {
            setPhase('fitting')
          } else {
            setPointState('transitioning')
            timerRef.current = setTimeout(() => {
              if (!active) return
              setCurrentPoint((c) => c + 1)
              setPointState('preparing')
            }, 300)
          }
        }
      } catch (e) {
        if (active) {
          console.error('[Cal] collect_point error:', e)
          setPointState('preparing')
        }
      }
    }, 1500)

    return () => {
      active = false
      clearTimeout(timerRef.current)
    }
  }, [phase, pointState, currentPoint, shuffledPoints])

  // Call fit when entering fitting phase
  useEffect(() => {
    if (phase !== 'fitting') return
    fetch('http://localhost:8765/calibration/fit', { method: 'POST' })
      .then((r) => r.json())
      .then((data) => {
        if (data.status === 'calibrated') {
          setCalibrated(true)
          setFitResult(data)
          setPhase('result')
        }
      })
      .catch((e) => console.error('[Cal] fit error:', e))
  }, [phase, setCalibrated])

  const handleStartCalibration = useCallback(async () => {
    clearTimeout(timerRef.current)
    try {
      await fetch('http://localhost:8765/calibration/new_session', { method: 'POST' })
      const points = fisherYates(BASE_POINTS)
      setShuffledPoints(points)
      setCurrentPoint(0)
      setFitResult(null)
      setPointState('preparing')
      setPhase('calibrating')
    } catch (e) {
      console.error('[Cal] new_session error:', e)
    }
  }, [])

  const handleConcluir = useCallback(() => {
    if (fromOnboarding) {
      navigate('/onboarding-ready', { state: { accuracy, engine: 'IrisGazeNet', name: onboardingName } })
    } else {
      navigate('/')
    }
  }, [accuracy, fromOnboarding, navigate, onboardingName])

  const { onMouseEnter: iniciarEnter, onMouseLeave: iniciarLeave } = useDwell(handleStartCalibration)
  const { onMouseEnter: concluirEnter, onMouseLeave: concluirLeave } = useDwell(handleConcluir)

  const progressPct = phase === 'fitting' ? 100 : (currentPoint / 6) * 100
  const progressLabel = phase === 'fitting' ? '6' : String(currentPoint)

  return (
    <div className="min-h-full flex flex-col bg-background text-on-surface">
      <style>{CSS}</style>

      {/* === PHASE: INTRO === */}
      {phase === 'intro' && (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-6xl w-full flex flex-col items-center">
            <div className="mb-16">
              <h1 className="font-headline-lg text-display-lg text-primary mb-4">Calibração do Olhar</h1>
              <p className="font-body-lg text-on-surface-variant max-w-2xl mx-auto">
                Siga os pontos com o olhar. Mantenha a cabeça estável para garantir a máxima precisão no rastreamento.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl mb-16">
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
                onClick={handleStartCalibration}
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
        </div>
      )}

      {/* === PHASE: CALIBRATING / FITTING — fullscreen overlay === */}
      {(phase === 'calibrating' || phase === 'fitting') && (
        <div className="fixed inset-0 z-50" style={{ background: '#000000' }}>
          {/* Progress bar (4px, top) */}
          <div className="absolute top-0 left-0 right-0" style={{ height: 4 }}>
            <div
              className="h-full transition-all duration-500"
              style={{ width: `${progressPct}%`, background: '#5bdac6' }}
            />
          </div>

          {/* Progress label */}
          <div
            className="absolute top-4 right-4 text-white font-mono text-sm"
            style={{ opacity: 0.3 }}
          >
            {progressLabel} / 6
          </div>

          {/* Active calibration dot */}
          {phase === 'calibrating' && pointState !== 'transitioning' && shuffledPoints.length > 0 && (
            <CalDot
              key={currentPoint}
              point={shuffledPoints[currentPoint]}
              collecting={pointState === 'collecting'}
            />
          )}

          {/* Instruction text */}
          {phase === 'calibrating' && (
            <div
              className="absolute bottom-8 left-0 right-0 text-center text-white text-sm"
              style={{ opacity: 0.5 }}
            >
              Olhe para o ponto e aguarde...
            </div>
          )}

          {/* Fitting spinner */}
          {phase === 'fitting' && (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <div
                className="rounded-full cal-spin"
                style={{ width: 32, height: 32, border: '2px solid #5bdac6', borderTopColor: 'transparent' }}
              />
              <p className="text-white text-sm" style={{ opacity: 0.5 }}>Processando calibração...</p>
            </div>
          )}
        </div>
      )}

      {/* === PHASE: RESULT === */}
      {phase === 'result' && (
        <div className="flex-1 flex flex-col items-center py-12 px-8 overflow-y-auto">
          <div className="relative flex flex-col items-center justify-center mb-12">
            <div
              className="relative w-72 h-72 rounded-full flex items-center justify-center border-4 border-secondary/20 bg-surface-container/30 backdrop-blur-2xl cal-pulse-slow"
              style={{ boxShadow: '0 0 40px 15px rgba(91,218,198,0.3)' }}
            >
              <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 288 288">
                <circle fill="transparent" cx="144" cy="144" r="140" stroke="currentColor" strokeWidth="8" className="text-secondary/10" />
                <circle
                  fill="transparent" cx="144" cy="144" r="140" stroke="currentColor" strokeWidth="8" className="text-secondary"
                  strokeDasharray="880"
                  strokeDashoffset={Math.round(880 * (1 - accuracy / 100))}
                  style={{ transition: 'stroke-dashoffset 1s ease-out' }}
                />
              </svg>
              <div className="text-center z-10">
                <span className="font-display-lg text-display-lg text-on-surface block leading-none">{accuracy}%</span>
                <span className="font-eye-track-label text-eye-track-label text-secondary mt-2 block tracking-widest uppercase">
                  {accuracy >= 80 ? 'Excelente' : accuracy >= 60 ? 'Bom' : 'Regular'}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-3xl mb-12">
            {[
              { icon: 'adjust', label: 'Erro médio', value: fitResult ? `${fitResult.mae_total} px` : '-' },
              { icon: 'track_changes', label: 'Amostras', value: fitResult ? `${fitResult.n_samples}` : '-' },
              { icon: 'check_circle', label: 'Status', value: 'Calibrado' },
            ].map((stat) => (
              <div
                key={stat.icon}
                className="border border-white/10 rounded-xl p-8 flex flex-col items-center text-center hover:scale-[1.02] transition-transform duration-300"
                style={{ background: 'linear-gradient(180deg, rgba(30,32,36,0.6) 0%, rgba(17,19,24,0.8) 100%)' }}
              >
                <span className="material-symbols-outlined text-secondary text-4xl mb-4">{stat.icon}</span>
                <p className="font-label-lg text-label-lg text-on-surface-variant mb-1">{stat.label}</p>
                <p className="font-headline-md text-headline-md text-on-surface">{stat.value}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-6 items-center flex-wrap justify-center">
            <button
              className="cal-concluir relative min-w-[280px] h-16 bg-secondary-container text-on-secondary-container font-eye-track-label text-eye-track-label rounded-full flex items-center justify-center gap-4 transition-all duration-300 hover:scale-105 active:scale-95 overflow-hidden"
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
              className="min-w-[200px] h-16 border-2 border-outline/30 text-on-surface-variant font-eye-track-label text-eye-track-label rounded-full flex items-center justify-center gap-4 transition-all duration-300 hover:bg-white/5 hover:border-outline hover:text-on-surface"
              onClick={handleStartCalibration}
            >
              <span className="material-symbols-outlined">refresh</span>
              RECALIBRAR
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
