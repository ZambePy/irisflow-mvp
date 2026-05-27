import { useEffect, useRef, useCallback, useId } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useAppStore } from '../store/appStore'
import { useDwell } from '../hooks/useDwell'

// --- Particle canvas background ---
function ParticleCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId
    let particles = []

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    class Particle {
      constructor() { this.init() }
      init() {
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height
        this.size = Math.random() * 2 + 1
        this.speedX = (Math.random() - 0.5) * 0.5
        this.speedY = (Math.random() - 0.5) * 0.5
        this.opacity = Math.random() * 0.5
      }
      update() {
        this.x += this.speedX
        this.y += this.speedY
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1
        if (this.y < 0 || this.y > canvas.height) this.speedY *= -1
      }
      draw() {
        ctx.fillStyle = `rgba(0, 219, 231, ${this.opacity})`
        ctx.fillRect(this.x, this.y, this.size, this.size)
      }
    }

    for (let i = 0; i < 100; i++) particles.push(new Particle())

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      particles.forEach(p => { p.update(); p.draw() })
      animId = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed', top: 0, left: 0,
        width: '100%', height: '100%',
        zIndex: -1, background: '#111417',
        pointerEvents: 'none',
      }}
    />
  )
}

// --- Volumetric pulse background ---
function VolumePulse() {
  const divRef = useRef(null)

  useEffect(() => {
    const el = divRef.current
    if (!el) return
    const onMove = (e) => {
      el.style.setProperty('--px', `${e.clientX}px`)
      el.style.setProperty('--py', `${e.clientY}px`)
    }
    document.addEventListener('mousemove', onMove)
    return () => document.removeEventListener('mousemove', onMove)
  }, [])

  return (
    <div
      ref={divRef}
      style={{
        position: 'fixed', width: '100vw', height: '100vh',
        background: 'radial-gradient(circle at var(--px, 50%) var(--py, 50%), rgba(0,219,231,0.04) 0%, transparent 50%)',
        zIndex: -1, pointerEvents: 'none', mixBlendMode: 'screen',
      }}
    />
  )
}

// Converte coordenadas de viewport para coordenadas de tela (usadas pelo DwellController)
function clientToScreen(rect) {
  const chromeH = window.outerHeight - window.innerHeight
  return {
    x: Math.round(rect.left + window.screenX),
    y: Math.round(rect.top + window.screenY + chromeH),
    w: Math.round(rect.width),
    h: Math.round(rect.height),
  }
}

// --- Tilt card wrapper com dwell registrado no backend ---
function TiltCard({ onClick, className = '', style = {}, children }) {
  const id = useId()
  const ref = useRef(null)
  const { onMouseEnter: dwellEnter, onMouseLeave: dwellLeave } = useDwell(onClick ?? (() => {}))
  const { registerDwellRegion, unregisterDwellRegion } = useGazeSocket()

  // Mantém referência estável ao onClick para o callback do backend
  const onClickRef = useRef(onClick)
  useEffect(() => { onClickRef.current = onClick }, [onClick])

  // Registra no DwellController do backend ao montar
  useEffect(() => {
    const el = ref.current
    if (!el) return
    registerDwellRegion(id, clientToScreen(el.getBoundingClientRect()), () => onClickRef.current?.(), null)
    return () => unregisterDwellRegion(id)
  }, [id, registerDwellRegion, unregisterDwellRegion])

  const onMove = useCallback((e) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const rx = (y - rect.height / 2) / 20
    const ry = (rect.width / 2 - x) / 20
    el.style.transform = `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.03) translateY(-4px)`
  }, [])

  const onLeave = useCallback((e) => {
    if (ref.current) ref.current.style.transform = ''
    dwellLeave(e)
  }, [dwellLeave])

  return (
    <button
      ref={ref}
      className={className}
      style={style}
      onMouseMove={onMove}
      onMouseEnter={dwellEnter}
      onMouseLeave={onLeave}
      onClick={onClick}
    >
      {children}
    </button>
  )
}

// --- Scanning light effect (CSS inline) ---
const scanStyle = `
@keyframes scan {
  0% { left: -20%; opacity: 0; }
  10% { opacity: 0.4; }
  90% { opacity: 0.4; }
  100% { left: 120%; opacity: 0; }
}
@keyframes holographic-flicker {
  0%, 19.999%, 22%, 62.999%, 64%, 64.999%, 70%, 100% { opacity: 0.99; filter: drop-shadow(0 0 1px #00dbe7); }
  20%, 21.999%, 63%, 63.999%, 65%, 69.999% { opacity: 0.4; filter: drop-shadow(0 0 8px #00dbe7); }
}
@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}
@keyframes slideUpFade {
  to { opacity: 1; transform: translateY(0); }
}
.scanning-light {
  background: linear-gradient(90deg, transparent, rgba(0,219,231,0.2), transparent);
  animation: scan 8s cubic-bezier(0.4,0,0.2,1) infinite;
  position: absolute; top: 0; height: 100%; width: 20%; pointer-events: none;
}
.holographic-text { animation: holographic-flicker 5s infinite; }
.card-entrance { animation: slideUpFade 0.6s cubic-bezier(0.2,0.8,0.2,1) forwards; opacity: 0; transform: translateY(20px); }
.gaze-target-active:hover {
  box-shadow: 0 0 40px rgba(0,219,231,0.3);
  border-color: rgba(0,219,231,0.6);
}
.glass-panel-cinematic {
  background: rgba(29,32,35,0.4);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255,255,255,0.05);
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
}
.glass-panel-cinematic:hover {
  border-color: rgba(0,219,231,0.4);
  background: rgba(29,32,35,0.55);
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.5);
}
`

// --- Main Dashboard ---
export default function Dashboard() {
  const navigate = useNavigate()
  const { sendMessage, registerDwellRegion, unregisterDwellRegion } = useGazeSocket()
  const activeMessage = useAppStore(state => state.activeMessage)

  // TTS sempre via backend Python (SAPI) — nunca window.speechSynthesis
  const handleSpeak = useCallback(() => {
    sendMessage('speak', { text: activeMessage || 'Gaze to start typing' })
  }, [sendMessage, activeMessage])

  // Botão speak (volume_up) registrado no backend para dwell
  const speakBtnRef = useRef(null)
  const speakBtnId = useId()
  const handleSpeakRef = useRef(handleSpeak)
  useEffect(() => { handleSpeakRef.current = handleSpeak }, [handleSpeak])

  useEffect(() => {
    const el = speakBtnRef.current
    if (!el) return
    registerDwellRegion(speakBtnId, clientToScreen(el.getBoundingClientRect()), () => handleSpeakRef.current(), null)
    return () => unregisterDwellRegion(speakBtnId)
  }, [speakBtnId, registerDwellRegion, unregisterDwellRegion])

  const { onMouseEnter: speakEnter, onMouseLeave: speakLeave } = useDwell(handleSpeak)

  return (
    <>
      <style>{scanStyle}</style>
      <ParticleCanvas />
      <VolumePulse />

      <main className="ml-64 pt-24 p-margin grid grid-cols-12 gap-gutter h-screen overflow-hidden">

        {/* --- Active Message --- */}
        <section
          className="col-span-12 glass-panel-cinematic rounded-2xl p-8 flex items-center justify-between border-l-4 border-l-[#00dbe7] relative overflow-hidden h-32 card-entrance"
          style={{ animationDelay: '0.1s' }}
        >
          <div className="absolute inset-0" style={{ background: 'linear-gradient(to right, rgba(0,219,231,0.05), transparent)' }} />
          <div className="scanning-light" />
          <div className="relative z-10">
            <span className="font-label-caps text-label-caps block mb-2 tracking-[0.2em]" style={{ color: 'rgba(116,245,255,0.6)' }}>
              ACTIVE MESSAGE
            </span>
            <h1 className="holographic-text text-on-surface opacity-90 text-2xl font-bold">
              {activeMessage || 'Gaze to start typing...'}
            </h1>
          </div>
          <button
            ref={speakBtnRef}
            className="glass-panel-cinematic w-16 h-16 rounded-full flex items-center justify-center hover:scale-110 cursor-pointer group"
            onMouseEnter={speakEnter}
            onMouseLeave={speakLeave}
            onClick={handleSpeak}
          >
            <span className="material-symbols-outlined text-outline group-hover:text-[#00dbe7] transition-colors">
              volume_up
            </span>
          </button>
        </section>

        {/* --- YES / NO column --- */}
        <div className="col-span-5 grid grid-rows-2 gap-gutter" style={{ height: 'calc(100vh - 320px)' }}>
          {/* YES — fala "SIM" via backend TTS */}
          <TiltCard
            onClick={() => sendMessage('speak', { text: 'SIM' })}
            className="glass-panel-cinematic gaze-target-active rounded-3xl flex flex-col items-center justify-center gap-4 group card-entrance w-full"
            style={{ animationDelay: '0.2s' }}
          >
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-500"
              style={{
                background: 'rgba(0,219,231,0.1)',
                border: '1px solid rgba(0,219,231,0.3)',
                animation: 'breathe 4s infinite ease-in-out',
              }}
            >
              <span
                className="material-symbols-outlined text-4xl"
                style={{ color: '#00dbe7', fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
            </div>
            <span
              className="font-bold text-3xl tracking-widest group-hover:tracking-[0.4em] transition-all duration-500"
              style={{ color: '#00dbe7' }}
            >
              YES
            </span>
          </TiltCard>

          {/* NO — fala "NÃO" via backend TTS */}
          <TiltCard
            onClick={() => sendMessage('speak', { text: 'NÃO' })}
            className="glass-panel-cinematic gaze-target-active rounded-3xl flex flex-col items-center justify-center gap-4 group card-entrance w-full"
            style={{ animationDelay: '0.3s' }}
          >
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-500"
              style={{
                background: 'rgba(210,4,25,0.1)',
                border: '1px solid rgba(210,4,25,0.3)',
                animation: 'breathe 4s infinite ease-in-out 1s',
              }}
            >
              <span
                className="material-symbols-outlined text-4xl"
                style={{ color: '#d20419', fontVariationSettings: "'FILL' 1" }}
              >
                cancel
              </span>
            </div>
            <span
              className="font-bold text-3xl tracking-widest group-hover:tracking-[0.4em] transition-all duration-500"
              style={{ color: '#d20419' }}
            >
              NO
            </span>
          </TiltCard>
        </div>

        {/* --- Right grid --- */}
        <div className="col-span-7 grid grid-cols-2 grid-rows-2 gap-gutter" style={{ height: 'calc(100vh - 320px)' }}>

          {/* Phrases */}
          <TiltCard
            onClick={() => navigate('/phrases')}
            className="glass-panel-cinematic gaze-target-active rounded-3xl p-6 relative overflow-hidden group card-entrance text-left"
            style={{ animationDelay: '0.4s' }}
          >
            <span className="font-label-caps text-label-caps text-outline mb-1 block">CATEGORIES</span>
            <h3 className="font-bold text-on-surface mb-6 text-xl">Phrases</h3>
            <div className="flex flex-wrap gap-2">
              {['NEEDS', 'EMOTIONS', 'SOCIAL'].map(cat => (
                <span
                  key={cat}
                  className="px-4 py-2 rounded-full font-label-caps text-label-caps text-on-surface transition-all duration-300"
                  style={{ background: 'rgba(50,53,57,0.5)' }}
                >
                  {cat}
                </span>
              ))}
            </div>
            <div className="absolute top-4 right-4 glass-panel-cinematic w-12 h-12 rounded-xl flex items-center justify-center group-hover:rotate-12 transition-transform">
              <span className="material-symbols-outlined text-outline">chat</span>
            </div>
          </TiltCard>

          {/* Calibration */}
          <TiltCard
            onClick={() => navigate('/calibration')}
            className="glass-panel-cinematic gaze-target-active rounded-3xl p-6 flex flex-col justify-center gap-4 group card-entrance text-left"
            style={{ animationDelay: '0.5s' }}
          >
            <div className="flex items-center gap-4">
              <div
                className="w-14 h-14 rounded-2xl glass-panel-cinematic flex items-center justify-center"
                style={{ borderColor: 'rgba(0,219,231,0.2)' }}
              >
                <span
                  className="material-symbols-outlined text-3xl group-hover:scale-110 transition-transform"
                  style={{ color: '#00dbe7' }}
                >
                  center_focus_strong
                </span>
              </div>
              <div>
                <h3 className="font-bold text-on-surface text-xl">Calibration</h3>
                <p className="font-label-caps text-label-caps text-outline">Check accuracy</p>
              </div>
            </div>
          </TiltCard>

          {/* Keyboard — span 2 cols */}
          <TiltCard
            onClick={() => navigate('/keyboard')}
            className="col-span-2 glass-panel-cinematic gaze-target-active rounded-3xl p-6 relative overflow-hidden card-entrance text-left"
            style={{
              animationDelay: '0.6s',
              background: 'linear-gradient(135deg, rgba(29,32,35,0.8), rgba(12,14,18,0.8))',
            }}
          >
            <span className="font-label-caps text-label-caps text-outline mb-1 block">FREE TEXT</span>
            <h3 className="font-bold text-on-surface mb-4 text-xl">Keyboard</h3>
            <div className="grid grid-cols-10 gap-2 opacity-40">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-10 glass-panel-cinematic rounded-lg" />
              ))}
            </div>
            <div className="absolute top-4 right-4 w-12 h-12 rounded-xl flex items-center justify-center border"
              style={{ background: 'rgba(0,219,231,0.1)', borderColor: 'rgba(0,219,231,0.3)' }}
            >
              <span className="material-symbols-outlined" style={{ color: '#00dbe7' }}>keyboard</span>
            </div>
            <div className="mt-4 flex gap-4">
              <div
                className="flex items-center gap-2 font-mono text-sm px-3 py-1 rounded-md"
                style={{ color: '#00dbe7', border: '1px solid rgba(0,219,231,0.2)', background: 'rgba(0,219,231,0.05)' }}
              >
                <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#00dbe7' }} />
                PREDICTION READY
              </div>
            </div>
          </TiltCard>
        </div>
      </main>
    </>
  )
}
