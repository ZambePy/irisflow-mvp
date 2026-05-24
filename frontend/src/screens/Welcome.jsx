import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

// --- Particle canvas ---
function ParticleCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId
    const particles = []

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
        this.size = Math.random() * 2 + 0.5
        this.speedX = (Math.random() - 0.5) * 0.5
        this.speedY = (Math.random() - 0.5) * 0.5
        this.opacity = Math.random() * 0.5 + 0.1
      }
      update() {
        this.x += this.speedX
        this.y += this.speedY
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1
        if (this.y < 0 || this.y > canvas.height) this.speedY *= -1
      }
      draw() {
        ctx.fillStyle = `rgba(0, 217, 255, ${this.opacity})`
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    for (let i = 0; i < 60; i++) particles.push(new Particle())

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
        zIndex: 0, pointerEvents: 'none',
      }}
    />
  )
}

// --- Scan line animation ---
const css = `
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
@keyframes scanning {
  0% { top: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}
@keyframes ringPulse {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.05); }
}
.welcome-float { animation: float 6s ease-in-out infinite; }
.welcome-scan {
  position: absolute; top: 0; left: 0;
  width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, #00d9ff, transparent);
  animation: scanning 4s linear infinite;
}
.welcome-ring { animation: ringPulse 2s ease-in-out infinite; }
`

export default function Welcome() {
  const navigate = useNavigate()

  const { onMouseEnter: startEnter, onMouseLeave: startLeave } = useDwell(() => navigate('/profile-setup'))
  const { onMouseEnter: loadEnter, onMouseLeave: loadLeave } = useDwell(() => navigate('/'))

  return (
    <>
      <style>{css}</style>
      <ParticleCanvas />

      {/* HUD decoration top-left */}
      <div className="fixed top-12 left-12 flex flex-col gap-2 pointer-events-none opacity-40 z-10">
        <div className="h-1 w-12 bg-primary" style={{ background: '#00d9ff' }} />
        <span className="text-xs font-mono tracking-widest" style={{ color: '#00d9ff' }}>
          SYSTEM READY // ALPHA_01
        </span>
      </div>

      {/* HUD decoration bottom-right */}
      <div className="fixed bottom-12 right-12 text-right pointer-events-none opacity-40 z-10">
        <span className="text-xs font-mono tracking-widest" style={{ color: '#00d9ff' }}>
          CALIBRATION STATUS: OPTIMAL
        </span>
        <div className="flex justify-end gap-1 mt-1">
          <div className="w-2 h-2" style={{ background: '#00d9ff' }} />
          <div className="w-2 h-2" style={{ background: '#00d9ff' }} />
          <div className="w-2 h-2" style={{ background: 'rgba(0,217,255,0.2)' }} />
        </div>
      </div>

      {/* Main content */}
      <main
        className="relative z-10 flex flex-col items-center justify-center text-center min-h-screen px-12"
        style={{ background: '#0e1320' }}
      >
        {/* Logo */}
        <div className="welcome-float flex flex-col items-center mb-10">
          <div className="relative w-32 h-32 flex items-center justify-center mb-6">
            {/* Outer ring pulse */}
            <div
              className="welcome-ring absolute inset-0 rounded-full border-2"
              style={{ borderColor: 'rgba(0,217,255,0.2)' }}
            />
            {/* Inner ring */}
            <div
              className="absolute w-24 h-24 rounded-full border rotate-45"
              style={{ borderColor: 'rgba(0,217,255,0.4)' }}
            />
            {/* Eye icon */}
            <span
              className="material-symbols-outlined"
              style={{
                fontSize: 80,
                color: '#00d9ff',
                fontVariationSettings: "'FILL' 0",
              }}
            >
              visibility
            </span>
          </div>

          <h1
            className="font-bold tracking-tight"
            style={{ fontSize: 64, lineHeight: '72px', color: '#afecff', letterSpacing: '-0.02em' }}
          >
            IrisFlow
          </h1>
          <p
            className="mt-2 uppercase tracking-[0.2em]"
            style={{ fontSize: 20, color: 'rgba(187,201,206,0.8)' }}
          >
            Comunicação pelo Olhar
          </p>
        </div>

        {/* Buttons */}
        <div className="flex flex-col gap-4 w-full max-w-md">
          {/* COMEÇAR */}
          <button
            className="relative w-full flex items-center justify-center gap-4 rounded-xl overflow-hidden transition-all duration-300 hover:scale-105 active:scale-95"
            style={{
              height: 80,
              background: '#00d9ff',
              color: '#003641',
              fontSize: 24,
              fontWeight: 700,
              boxShadow: '0 0 30px rgba(0,217,255,0.4), inset 0 0 10px rgba(0,217,255,0.2)',
            }}
            onMouseEnter={startEnter}
            onMouseLeave={startLeave}
            onClick={() => navigate('/profile-setup')}
          >
            <div className="welcome-scan" />
            <span
              className="material-symbols-outlined"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              play_arrow
            </span>
            COMEÇAR
          </button>

          {/* Carregar perfil */}
          <button
            className="w-full flex items-center justify-center gap-4 rounded-xl transition-all duration-200 hover:bg-white/10"
            style={{
              height: 80,
              background: 'rgba(48,52,67,0.2)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#00d9ff',
              fontSize: 18,
            }}
            onMouseEnter={loadEnter}
            onMouseLeave={loadLeave}
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined">account_circle</span>
            Carregar Perfil Existente
          </button>
        </div>
      </main>
    </>
  )
}
