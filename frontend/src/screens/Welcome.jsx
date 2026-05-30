import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  @keyframes wc-rotateCW { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  @keyframes wc-rotateCCW { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }
  @keyframes wc-pulseGlow { 0%, 100% { opacity: 0.6; filter: drop-shadow(0 0 10px #5bdac6); } 50% { opacity: 1; filter: drop-shadow(0 0 25px #5bdac6); } }
  @keyframes wc-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
  @keyframes wc-scan { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  @keyframes wc-particleFloat { 0% { transform: translateY(0) translateX(0); opacity: 0; } 20% { opacity: 0.4; } 80% { opacity: 0.4; } 100% { transform: translateY(-100vh) translateX(20px); opacity: 0; } }
  @keyframes wc-fadeInUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
  .wc-rotate-cw { animation: wc-rotateCW 12s linear infinite; }
  .wc-rotate-ccw { animation: wc-rotateCCW 8s linear infinite; }
  .wc-pulse-glow { animation: wc-pulseGlow 3s ease-in-out infinite; }
  .wc-float { animation: wc-float 5s ease-in-out infinite; }
  .wc-reveal { animation: wc-fadeInUp 1.2s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
  .wc-reveal-2 { animation: wc-fadeInUp 1.2s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
  .wc-reveal-3 { animation: wc-fadeInUp 1.2s cubic-bezier(0.22, 1, 0.36, 1) 0.4s both; }
  .wc-radial-bg { background: radial-gradient(circle at center, rgba(0, 166, 147, 0.15) 0%, rgba(10, 12, 16, 1) 70%); }
  .wc-scan::after { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); animation: wc-scan 3s infinite; pointer-events: none; }
  .wc-particle { position: absolute; background: #5bdac6; border-radius: 50%; pointer-events: none; }
  .wc-gaze { position: fixed; top: 0; left: 0; width: 32px; height: 32px; border-radius: 50%; border: 2px solid #5bdac6; box-shadow: 0 0 15px #5bdac6; pointer-events: none; z-index: 100; opacity: 0.6; transition: transform 0.3s ease-out; }
`

export default function Welcome() {
  const navigate = useNavigate()
  const particleRef = useRef(null)
  const gazeRef = useRef(null)
  const tX = useRef(window.innerWidth * 0.7)
  const tY = useRef(window.innerHeight * 0.3)
  const cX = useRef(tX.current)
  const cY = useRef(tY.current)

  const { onMouseEnter: startEnter, onMouseLeave: startLeave } = useDwell(() => navigate('/profile-setup'))
  const { onMouseEnter: loadEnter, onMouseLeave: loadLeave } = useDwell(() => navigate('/'))

  useEffect(() => {
    const container = particleRef.current
    if (container) {
      for (let i = 0; i < 40; i++) {
        const p = document.createElement('div')
        p.className = 'wc-particle'
        const size = Math.random() * 3 + 1
        p.style.cssText = `width:${size}px;height:${size}px;left:${Math.random()*100}vw;top:${Math.random()*100}vh;animation:wc-particleFloat ${Math.random()*10+10}s linear infinite;animation-delay:${Math.random()*10}s;opacity:${Math.random()*0.5}`
        container.appendChild(p)
      }
    }

    const cursor = gazeRef.current
    let rafId
    const tick = () => {
      cX.current += (tX.current - cX.current) * 0.05
      cY.current += (tY.current - cY.current) * 0.05
      if (cursor) cursor.style.transform = `translate(${cX.current}px, ${cY.current}px)`
      rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)

    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const btns = document.querySelectorAll('button')
        if (btns.length) {
          const btn = btns[Math.floor(Math.random() * btns.length)]
          const rect = btn.getBoundingClientRect()
          tX.current = rect.left + rect.width / 2 + (Math.random() - 0.5) * 100
          tY.current = rect.top + rect.height / 2 + (Math.random() - 0.5) * 40
        }
      } else {
        tX.current = Math.max(100, Math.min(window.innerWidth - 100, tX.current + (Math.random() - 0.5) * 400))
        tY.current = Math.max(100, Math.min(window.innerHeight - 100, tY.current + (Math.random() - 0.5) * 400))
      }
    }, 2000)

    const onMove = (e) => { tX.current = e.clientX; tY.current = e.clientY }
    window.addEventListener('mousemove', onMove)
    return () => { cancelAnimationFrame(rafId); clearInterval(interval); window.removeEventListener('mousemove', onMove) }
  }, [])

  return (
    <div className="bg-background text-on-background overflow-hidden h-screen w-screen selection:bg-secondary selection:text-on-secondary">
      <style>{CSS}</style>
      <div className="fixed inset-0 wc-radial-bg z-0" />
      <div ref={particleRef} className="fixed inset-0 z-10 pointer-events-none" />

      <div className="fixed top-8 left-8 z-50">
        <span className="font-mono text-label-lg text-secondary opacity-40 tracking-widest uppercase">
          SYSTEM READY // ALPHA_01
        </span>
      </div>

      <div className="fixed bottom-8 right-8 z-50 flex items-center gap-4">
        <span className="font-mono text-label-lg text-on-surface-variant opacity-60 tracking-wider">
          CALIBRATION STATUS: OPTIMAL
        </span>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 bg-secondary rounded-sm shadow-[0_0_8px_#5bdac6]" />
          <div className="w-2.5 h-2.5 bg-secondary rounded-sm shadow-[0_0_8px_#5bdac6]" />
          <div className="w-2.5 h-2.5 bg-secondary rounded-sm shadow-[0_0_8px_#5bdac6]" />
        </div>
      </div>

      <main className="relative z-20 flex flex-col items-center justify-center h-full text-center px-gutter-desktop">
        <div className="wc-reveal wc-float mb-12 relative flex items-center justify-center">
          <div className="wc-rotate-cw absolute w-64 h-64 border-2 border-dashed border-secondary/20 rounded-full" />
          <div className="wc-rotate-ccw absolute w-48 h-48 border-2 border-secondary/40 rounded-full" />
          <div className="wc-pulse-glow flex items-center justify-center w-24 h-24 bg-surface-container rounded-full border border-secondary shadow-[0_0_30px_rgba(91,218,198,0.2)]">
            <span className="material-symbols-outlined text-[48px] text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
              visibility
            </span>
          </div>
        </div>

        <div className="wc-reveal-2">
          <h1 className="font-headline-lg text-[64px] leading-tight text-primary-fixed-dim font-extrabold mb-4 tracking-tight">
            IrisFlow
          </h1>
          <p className="font-mono text-body-lg text-on-surface-variant uppercase tracking-[0.4em] mb-16 opacity-80">
            COMUNICAÇÃO PELO OLHAR
          </p>
        </div>

        <div className="wc-reveal-3 flex flex-col gap-6">
          <button
            className="wc-scan relative group w-[500px] h-[80px] bg-secondary-container hover:bg-secondary transition-all duration-500 rounded-xl overflow-hidden flex items-center justify-center gap-3 hover:shadow-[0_0_40px_rgba(91,218,198,0.4)] active:scale-[0.98]"
            onMouseEnter={startEnter}
            onMouseLeave={startLeave}
            onClick={() => navigate('/profile-setup')}
          >
            <span className="font-headline-md text-on-secondary-container group-hover:text-on-secondary transition-colors duration-300 flex items-center gap-4">
              <span className="material-symbols-outlined text-[32px]">play_arrow</span>
              COMEÇAR
            </span>
            <div className="absolute bottom-0 left-0 h-1 bg-on-secondary-container/30 w-0 group-hover:w-full transition-all duration-[800ms] ease-out" />
          </button>

          <button
            className="group w-[500px] h-[80px] bg-surface-container/40 backdrop-blur-xl border border-outline-variant/30 hover:border-secondary/50 transition-all duration-300 rounded-xl flex items-center justify-center gap-3 active:scale-[0.98]"
            onMouseEnter={loadEnter}
            onMouseLeave={loadLeave}
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined text-[28px] text-on-surface-variant group-hover:text-secondary transition-colors duration-300">
              person
            </span>
            <span className="font-label-lg text-body-lg text-on-surface-variant group-hover:text-on-surface transition-colors duration-300">
              Carregar Perfil Existente
            </span>
          </button>
        </div>
      </main>

      <div ref={gazeRef} className="wc-gaze">
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 4, height: 4, background: '#5bdac6', borderRadius: '50%' }} />
      </div>
    </div>
  )
}
