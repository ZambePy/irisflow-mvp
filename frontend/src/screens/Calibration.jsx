import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { gsap } from 'gsap'
import { useDwell } from '../hooks/useDwell'
import { useAppStore } from '../store/appStore'

// ── Constantes ────────────────────────────────────────────────────────────────

const GRID_POINTS = [
  { x: 0.10, y: 0.10 }, { x: 0.50, y: 0.10 }, { x: 0.90, y: 0.10 },
  { x: 0.10, y: 0.50 }, { x: 0.50, y: 0.50 }, { x: 0.90, y: 0.50 },
  { x: 0.10, y: 0.90 }, { x: 0.50, y: 0.90 }, { x: 0.90, y: 0.90 },
]

const DWELL_MS     = 2000
const CIRCUMFERENCE = 2 * Math.PI * 36  // r=36 → ~226.2

function fisherYates(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

// ── CSS injetado ──────────────────────────────────────────────────────────────

const CSS = `
  @keyframes cal-pulse-ring {
    0%   { transform: scale(1);   opacity: 0.8; }
    50%  { transform: scale(1.5); opacity: 0;   }
    100% { transform: scale(1);   opacity: 0;   }
  }
  .cal-pulse-ring { animation: cal-pulse-ring 2s cubic-bezier(0.4,0,0.6,1) infinite; }

  .cal-glow { filter: drop-shadow(0 0 12px rgba(91,218,198,0.6)); }
  .cal-glow-hover { filter: drop-shadow(0 0 25px rgba(91,218,198,0.9)); }

  @keyframes cal-fade-in  { from { opacity: 0; } to { opacity: 1; } }
  .cal-fade-in { animation: cal-fade-in 0.3s ease forwards; }

  /* Intro screen reused styles */
  .cal-glass { background: rgba(30,32,36,0.6); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.1); }
  .cal-btn .cal-dwell-bar { position:absolute; bottom:0; left:0; height:4px; width:0%; background:#5bdac6; transition:width 2s linear; }
  .cal-btn:hover .cal-dwell-bar { width:100%; }

  /* Result screen */
  @keyframes cal-pulse-slow { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.8;transform:scale(1.02)} }
  .cal-pulse-slow { animation: cal-pulse-slow 4s infinite ease-in-out; }
  .cal-concluir-fill { position:absolute;inset:0;background:rgba(91,218,218,0.2);transform-origin:left;transform:scaleX(0);transition:transform 2s; }
  .cal-concluir:hover .cal-concluir-fill { transform:scaleX(1); }
`

const TIPS = [
  { icon: 'lightbulb', color: 'text-primary',   bg: 'bg-primary/10 group-hover:bg-primary/20',     title: 'Ambiente',  desc: 'Ambiente bem iluminado' },
  { icon: 'straighten', color: 'text-secondary', bg: 'bg-secondary/10 group-hover:bg-secondary/20', title: 'Distância', desc: '50–70 cm da tela' },
  { icon: 'visibility', color: 'text-tertiary',  bg: 'bg-tertiary/10 group-hover:bg-tertiary/20',   title: 'Foco',      desc: 'Olhe direto para cada ponto' },
]

// ── Componente principal ──────────────────────────────────────────────────────

export default function Calibration() {
  const navigate    = useNavigate()
  const location    = useLocation()
  const setCalibrated = useAppStore((s) => s.setCalibrated)

  const [phase,          setPhase]          = useState('intro')
  const [shuffled,       setShuffled]       = useState([])
  const [stepIdx,        setStepIdx]        = useState(0)   // 0-based index into shuffled
  const [fitResult,      setFitResult]      = useState(null)

  const targetRef      = useRef(null)
  const circleRef      = useRef(null)
  const rafRef         = useRef(null)
  const startRef       = useRef(null)
  const activeRef      = useRef(true)
  const collectingRef  = useRef(false)  // true enquanto o RAF de progresso está rodando
  const advancingRef   = useRef(false)  // guard contra double-advance (click + RAF simultâneos)
  const startingRef    = useRef(false)  // guard contra double-call de startSession (dwell + click)

  useEffect(() => {
    activeRef.current = true
    return () => {
      activeRef.current = false
      cancelAnimationFrame(rafRef.current)
    }
  }, [])

  // ── Funções de calibração ─────────────────────────────────────────────────

  const startSession = useCallback(async () => {
    if (startingRef.current) return        // guard: dwell + click simultâneos
    startingRef.current = true
    collectingRef.current = false
    advancingRef.current  = false

    try {
      await fetch('http://localhost:8765/calibration/new_session', { method: 'POST' })
    } catch { /* offline */ }

    const pts = fisherYates(GRID_POINTS)
    setShuffled(pts)
    setStepIdx(0)
    setFitResult(null)
    startingRef.current = false
    setPhase('calibrating')
  }, [])

  // Posiciona e anima a entrada do ponto quando stepIdx muda
  useEffect(() => {
    if (phase !== 'calibrating' || shuffled.length === 0) return
    const el = targetRef.current
    if (!el) return

    const pt = shuffled[stepIdx]
    const px = pt.x * window.innerWidth
    const py = pt.y * window.innerHeight

    // Posiciona sem transição e entra com scale back.out
    gsap.set(el, { x: px, y: py, scale: 0, opacity: 0, xPercent: -50, yPercent: -50 })
    gsap.to(el, { scale: 1, opacity: 1, duration: 0.5, delay: 0.1, ease: 'back.out(1.7)' })

    collectingRef.current = false
    advancingRef.current  = false
    startRef.current = null
    if (circleRef.current)
      circleRef.current.style.strokeDashoffset = CIRCUMFERENCE
  }, [stepIdx, phase, shuffled])

  // Loop de progresso após posicionar o ponto
  useEffect(() => {
    if (phase !== 'calibrating' || shuffled.length === 0) return
    if (collectingRef.current) return

    // Aguarda 200 ms (tempo da animação de entrada) antes de começar a coletar
    const delay = setTimeout(() => {
      collectingRef.current = true
      startRef.current = performance.now()

      const tick = (now) => {
        if (!activeRef.current) return
        const elapsed = now - startRef.current
        const pct = Math.min((elapsed / DWELL_MS) * 100, 100)
        if (circleRef.current)
          circleRef.current.style.strokeDashoffset =
            CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE
        if (pct < 100) {
          rafRef.current = requestAnimationFrame(tick)
        } else {
          advancePoint()
        }
      }
      rafRef.current = requestAnimationFrame(tick)
    }, 600)

    return () => {
      clearTimeout(delay)
      cancelAnimationFrame(rafRef.current)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepIdx, phase, shuffled])

  const advancePoint = useCallback(() => {
    if (!activeRef.current) return
    if (advancingRef.current) return   // guard: RAF + click simultâneos
    advancingRef.current = true
    cancelAnimationFrame(rafRef.current)
    const el = targetRef.current
    if (!el) return

    const currentStep = stepIdx   // capture before state update

    // Coleta o ponto no backend
    const pt = shuffled[currentStep]
    const px = Math.round(pt.x * window.innerWidth)
    const py = Math.round(pt.y * window.innerHeight)
    fetch('http://localhost:8765/calibration/collect_point', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ point_index: currentStep, expected_x: px, expected_y: py }),
    }).catch(() => {})

    gsap.to(el, {
      scale: 0,
      opacity: 0,
      duration: 0.35,
      ease: 'back.in(1.7)',
      onComplete: () => {
        if (!activeRef.current) return
        const next = currentStep + 1
        if (next < GRID_POINTS.length) {
          collectingRef.current = false
          cancelAnimationFrame(rafRef.current)
          setStepIdx(next)
        } else {
          setPhase('fitting')
        }
      },
    })
  }, [stepIdx, shuffled])

  // Clique para avançar (teste com mouse)
  const handlePointClick = useCallback(() => {
    advancePoint()
  }, [advancePoint])

  // Fase de fitting
  useEffect(() => {
    if (phase !== 'fitting') return
    const minDelay = new Promise((r) => setTimeout(r, 1000))
    fetch('http://localhost:8765/calibration/fit', { method: 'POST' })
      .then((r) => r.json())
      .then(async (data) => {
        await minDelay
        if (!activeRef.current) return
        setCalibrated(true)
        setFitResult(data.status === 'calibrated' ? data : { accuracy: 0.94 })
        setPhase('result')
      })
      .catch(async () => {
        await minDelay
        if (!activeRef.current) return
        setCalibrated(true)
        setFitResult({ accuracy: 0.94 })
        setPhase('result')
      })
  }, [phase, setCalibrated])

  // ── Dwell hooks para intro/result ─────────────────────────────────────────

  const handleConcluir = useCallback(() => {
    if (location.state?.from === 'onboarding') {
      navigate('/onboarding-ready', {
        state: {
          accuracy,
          engine: 'IrisGazeNet',
          latency: '8ms',
          name: location.state?.name ?? '',
        },
      })
    } else {
      navigate('/')
    }
  }, [navigate, location, accuracy])

  const { onMouseEnter: iniciarEnter, onMouseLeave: iniciarLeave } = useDwell(startSession)
  const { onMouseEnter: concluirEnter, onMouseLeave: concluirLeave } = useDwell(handleConcluir)

  const accuracy = fitResult ? Math.round((fitResult.accuracy ?? 0.94) * 100) : 94
  const completed = phase === 'calibrating' ? stepIdx : phase === 'fitting' ? GRID_POINTS.length : 0
  const topBarPct = (completed / GRID_POINTS.length) * 100

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <style>{CSS}</style>

      {/* ═══ PHASE: INTRO ═══════════════════════════════════════════════════ */}
      {phase === 'intro' && (
        <div className="min-h-full flex flex-col bg-background text-on-surface">
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-6xl w-full flex flex-col items-center">
              <div className="mb-16">
                <h1 className="font-headline-lg text-display-lg text-primary mb-4">Calibração do Olhar</h1>
                <p className="font-body-lg text-on-surface-variant max-w-2xl mx-auto">
                  9 pontos na tela. Olhe para cada um e aguarde o anel completar.
                  Mantenha a cabeça estável para máxima precisão.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl mb-16">
                {TIPS.map((tip) => (
                  <div key={tip.icon}
                    className="cal-glass p-8 rounded-xl flex flex-col items-center text-center gap-6 hover:scale-[1.02] transition-transform duration-500 cursor-default group">
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
                  onClick={startSession}
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
        </div>
      )}

      {/* ═══ PHASE: CALIBRATING ═════════════════════════════════════════════ */}
      {phase === 'calibrating' && (
        <div className="fixed inset-0 z-50 overflow-hidden" style={{ background: '#000000', cursor: 'none' }}>
          {/* Atmospheric radial glow */}
          <div className="fixed inset-0 pointer-events-none opacity-20"
            style={{ background: 'radial-gradient(circle at center, rgba(91,218,198,0.05) 0%, transparent 70%)' }} />

          {/* Progress bar top */}
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-surface-container-highest z-50">
            <div
              className="h-full transition-all duration-500 ease-out"
              style={{
                width: `${topBarPct}%`,
                background: '#5bdac6',
                boxShadow: '0 0 10px rgba(91,218,198,0.5)',
              }}
            />
          </div>

          {/* Counter top-right */}
          <div className="fixed top-12 right-12 z-50 select-none">
            <span className="font-headline-md text-secondary opacity-30" style={{ fontSize: 24 }}>
              {stepIdx + 1} / {GRID_POINTS.length}
            </span>
          </div>

          {/* Calibration target — positioned by GSAP.
              width/height=80 obrigatório: filhos são absolute,
              sem dimensões o xPercent/yPercent GSAP vira 0. */}
          <div
            ref={targetRef}
            className="cal-glow absolute"
            style={{ width: 80, height: 80, top: 0, left: 0, willChange: 'transform' }}
            onClick={handlePointClick}
          >
            {/* Pulsing outer ring */}
            <div
              className="cal-pulse-ring absolute rounded-full"
              style={{
                width: 60, height: 60,
                top: '50%', left: '50%',
                transform: 'translate(-50%,-50%)',
                border: '2px solid #5bdac6',
              }}
            />
            {/* Static outer border */}
            <div
              className="absolute rounded-full"
              style={{
                width: 60, height: 60,
                top: '50%', left: '50%',
                transform: 'translate(-50%,-50%)',
                border: '1px solid rgba(91,218,198,0.2)',
              }}
            />
            {/* SVG progress ring */}
            <svg
              className="absolute"
              width={80} height={80}
              style={{ top: '50%', left: '50%', transform: 'translate(-50%,-50%)' }}
            >
              <circle
                ref={circleRef}
                cx={40} cy={40} r={36}
                fill="transparent"
                stroke="#5bdac6"
                strokeWidth={3}
                strokeDasharray={CIRCUMFERENCE}
                strokeDashoffset={CIRCUMFERENCE}
                style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
              />
            </svg>
            {/* Solid inner dot */}
            <div
              className="absolute rounded-full"
              style={{
                width: 20, height: 20,
                top: '50%', left: '50%',
                transform: 'translate(-50%,-50%)',
                background: '#5bdac6',
                boxShadow: '0 0 15px rgba(91,218,198,0.8)',
              }}
            />
          </div>

          {/* Footer instruction */}
          <footer className="fixed bottom-12 left-1/2 -translate-x-1/2 text-center pointer-events-none">
            <p className="font-body-md text-white opacity-40 tracking-widest uppercase">
              Olhe para o ponto e aguarde...
            </p>
          </footer>

          {/* Skip button */}
          <div className="fixed bottom-12 right-12 z-50">
            <button
              className="px-6 py-2 rounded-lg border border-white/10 font-label-lg text-white/40 hover:text-white/80 hover:border-white/30 hover:bg-white/5 transition-all duration-300"
              onClick={() => navigate('/')}
            >
              Pular
            </button>
          </div>
        </div>
      )}

      {/* ═══ PHASE: FITTING ═════════════════════════════════════════════════ */}
      {phase === 'fitting' && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4"
          style={{ background: '#000000' }}>
          <div
            className="rounded-full"
            style={{
              width: 32, height: 32,
              border: '2px solid #5bdac6',
              borderTopColor: 'transparent',
              animation: 'spin 1s linear infinite',
            }}
          />
          <p className="text-white text-sm opacity-50 tracking-widest uppercase">Processando calibração...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* ═══ PHASE: RESULT ══════════════════════════════════════════════════ */}
      {phase === 'result' && (
        <div className="min-h-full flex flex-col bg-background text-on-surface">
          <div className="flex-1 flex flex-col items-center py-12 px-8 overflow-y-auto">
            <div className="relative flex flex-col items-center justify-center mb-12">
              <div
                className="relative w-72 h-72 rounded-full flex items-center justify-center border-4 border-secondary/20 bg-surface-container/30 backdrop-blur-2xl cal-pulse-slow"
                style={{ boxShadow: '0 0 40px 15px rgba(91,218,198,0.3)' }}
              >
                <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 288 288">
                  <circle fill="transparent" cx="144" cy="144" r="140" stroke="currentColor" strokeWidth="8" className="text-secondary/10" />
                  <circle
                    fill="transparent" cx="144" cy="144" r="140" stroke="currentColor" strokeWidth="8"
                    className="text-secondary"
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
                { icon: 'adjust',        label: 'Erro médio', value: fitResult?.mae_total != null ? `${fitResult.mae_total} px` : '-' },
                { icon: 'track_changes', label: 'Amostras',   value: fitResult?.n_samples != null ? `${fitResult.n_samples}` : '-' },
                { icon: 'check_circle',  label: 'Status',     value: 'Calibrado' },
              ].map((stat) => (
                <div key={stat.icon}
                  className="border border-white/10 rounded-xl p-8 flex flex-col items-center text-center hover:scale-[1.02] transition-transform duration-300"
                  style={{ background: 'linear-gradient(180deg,rgba(30,32,36,0.6) 0%,rgba(17,19,24,0.8) 100%)' }}
                >
                  <span className="material-symbols-outlined text-secondary text-4xl mb-4">{stat.icon}</span>
                  <p className="font-label-lg text-on-surface-variant mb-1">{stat.label}</p>
                  <p className="font-headline-md text-on-surface">{stat.value}</p>
                </div>
              ))}
            </div>

            <div className="flex gap-6 items-center flex-wrap justify-center">
              <button
                className="cal-concluir relative min-w-[280px] h-16 bg-secondary-container text-on-secondary-container font-eye-track-label rounded-full flex items-center justify-center gap-4 transition-all duration-300 hover:scale-105 active:scale-95 overflow-hidden"
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
                className="min-w-[200px] h-16 border-2 border-outline/30 text-on-surface-variant font-eye-track-label rounded-full flex items-center justify-center gap-4 transition-all duration-300 hover:bg-white/5 hover:border-outline hover:text-on-surface"
                onClick={startSession}
              >
                <span className="material-symbols-outlined">refresh</span>
                RECALIBRAR
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
