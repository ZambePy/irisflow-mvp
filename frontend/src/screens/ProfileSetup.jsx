import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  @keyframes ps-float {
    0% { transform: translateY(0) translateX(0); opacity: 0; }
    20% { opacity: 0.4; } 80% { opacity: 0.4; }
    100% { transform: translateY(-100vh) translateX(20px); opacity: 0; }
  }
  .ps-particle { position: absolute; background: #5bdac6; border-radius: 50%; pointer-events: none; opacity: 0.3; filter: blur(4px); }
  .ps-glass { background: rgba(30,32,36,0.6); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.08); }
  .ps-dwell-bar::after { content:''; position:absolute; bottom:0; left:0; height:4px; width:0%; background:#5bdac6; transition:width 0.5s linear; }
  .ps-dwell-bar:hover::after { width:100%; }
`

const DWELL_OPTIONS = [
  { label: 'Lento (2000ms)', value: 2000 },
  { label: 'Normal (1000ms)', value: 1000 },
  { label: 'Rápido (500ms)', value: 500 },
]
const CURSOR_OPTIONS = ['Pequeno', 'Médio', 'Grande']
const ENGINES = [
  { id: 'mock', label: 'Mock Engine', icon: 'visibility_off', desc: 'Simulação para testes rápidos de interface.' },
  { id: 'eyetrax-v2', label: 'EyeTrax v2', icon: 'center_focus_weak', desc: 'Balanceamento entre consumo e precisão.' },
  { id: 'iris-gaze-net', label: 'IrisGazeNet', icon: 'psychology', desc: 'IA avançada com baixa latência e auto-calibragem.', recommended: true },
]

export default function ProfileSetup() {
  const navigate = useNavigate()
  const particleRef = useRef(null)
  const [name, setName] = useState('')
  const [lang, setLang] = useState('pt-BR')
  const [dwell, setDwell] = useState(1000)
  const [cursor, setCursor] = useState('Médio')
  const [engine, setEngine] = useState('iris-gaze-net')

  const { onMouseEnter: nextEnter, onMouseLeave: nextLeave } = useDwell(handleSubmit)

  useEffect(() => {
    const c = particleRef.current
    if (!c) return
    for (let i = 0; i < 25; i++) {
      const p = document.createElement('div')
      p.className = 'ps-particle'
      const size = Math.random() * 8 + 2
      p.style.cssText = `width:${size}px;height:${size}px;left:${Math.random()*100}%;top:${Math.random()*100}%;opacity:${Math.random()*0.4};animation:ps-float ${Math.random()*10+10}s linear infinite;animation-delay:${Math.random()*10}s`
      c.appendChild(p)
    }
  }, [])

  async function handleSubmit() {
    try {
      await fetch('http://localhost:8765/profiles/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name || 'Usuário', dwell_time_ms: dwell, tracking_engine: engine }),
      })
    } catch {}
    navigate('/calibration', { state: { from: 'onboarding', name: name || 'Usuário' } })
  }

  return (
    <div className="min-h-screen relative flex flex-col font-body-md bg-background text-on-surface">
      <style>{CSS}</style>
      <div ref={particleRef} className="fixed inset-0 z-0 overflow-hidden pointer-events-none" />

      <header className="fixed top-0 left-0 w-full h-24 z-50 flex justify-between items-center px-margin-desktop bg-surface-dim/80 backdrop-blur-xl border-b border-white/10 shadow-md">
        <div className="flex items-center gap-8">
          <span className="text-headline-lg font-headline-lg font-bold text-primary tracking-tight">IrisFlow</span>
          <nav className="hidden md:flex items-center gap-6 ml-12">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-on-secondary font-bold text-sm">1</div>
              <span className="font-bold text-secondary font-eye-track-label text-[14px]">Profile</span>
            </div>
            <div className="h-[2px] w-8 bg-outline-variant" />
            <div className="flex items-center gap-2 opacity-50">
              <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center text-on-surface-variant font-bold text-sm">2</div>
              <span className="text-on-surface-variant font-label-lg">Calibration</span>
            </div>
            <div className="h-[2px] w-8 bg-outline-variant" />
            <div className="flex items-center gap-2 opacity-50">
              <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center text-on-surface-variant font-bold text-sm">3</div>
              <span className="text-on-surface-variant font-label-lg">Ready</span>
            </div>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-secondary font-mono text-[12px] tracking-widest bg-secondary/10 px-3 py-1 rounded">CALIBRATION ACTIVE</span>
          <span className="material-symbols-outlined text-on-surface-variant text-[20px]">sensors</span>
          <span className="material-symbols-outlined text-on-surface-variant text-[20px]">battery_full</span>
        </div>
      </header>

      <main className="flex-grow pt-32 pb-24 relative z-10 flex flex-col items-center justify-center px-margin-mobile md:px-margin-desktop">
        <div className="w-full max-w-[800px] mb-10 text-left">
          <h1 className="font-headline-lg text-headline-lg text-secondary mb-2">Configurar Perfil</h1>
          <p className="font-body-lg text-on-surface-variant">Etapa 1 de 3 — Informações Básicas</p>
        </div>

        <div className="w-full max-w-[800px] ps-glass rounded-2xl p-12 shadow-2xl relative overflow-hidden">
          <div className="space-y-12">
            <div className="space-y-4">
              <label className="font-mono text-label-lg text-primary tracking-[0.2em] opacity-80">NOME COMPLETO</label>
              <input
                className="w-full h-20 bg-surface-container-lowest border border-white/5 rounded-xl px-8 text-headline-md font-headline-md text-on-surface placeholder:text-on-surface-variant/30 focus:border-secondary focus:outline-none transition-all duration-300"
                placeholder="Como devemos chamar você?"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-4">
                <label className="font-mono text-[12px] text-primary tracking-widest">IDIOMA</label>
                <div className="flex flex-col gap-3">
                  {['pt-BR', 'en-US'].map((l) => (
                    <button key={l} type="button"
                      className={`h-16 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${lang === l ? 'bg-secondary/20 border-2 border-secondary text-secondary shadow-[0_0_25px_rgba(91,218,198,0.25)]' : 'bg-surface-container border border-white/5 text-on-surface-variant hover:bg-surface-bright'}`}
                      onClick={() => setLang(l)}>
                      {l}
                      {lang === l && <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="font-mono text-[12px] text-primary tracking-widest">VELOCIDADE DO OLHAR</label>
                <div className="flex flex-col gap-3">
                  {DWELL_OPTIONS.map((opt) => (
                    <button key={opt.value} type="button"
                      className={`h-12 rounded-xl font-bold text-[14px] transition-all ${dwell === opt.value ? 'bg-secondary/20 border-2 border-secondary text-secondary shadow-[0_0_25px_rgba(91,218,198,0.25)]' : 'bg-surface-container border border-white/5 text-on-surface-variant'}`}
                      onClick={() => setDwell(opt.value)}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="font-mono text-[12px] text-primary tracking-widest">TAMANHO DO CURSOR</label>
                <div className="flex flex-col gap-3">
                  {CURSOR_OPTIONS.map((opt) => (
                    <button key={opt} type="button"
                      className={`h-12 rounded-xl font-bold text-[14px] transition-all ${cursor === opt ? 'bg-secondary/20 border-2 border-secondary text-secondary shadow-[0_0_25px_rgba(91,218,198,0.25)]' : 'bg-surface-container border border-white/5 text-on-surface-variant'}`}
                      onClick={() => setCursor(opt)}>
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <label className="font-mono text-label-lg text-primary tracking-[0.2em] opacity-80 uppercase">Motor de Rastreamento</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {ENGINES.map((eng) => (
                  <div key={eng.id}
                    className={`p-6 rounded-xl relative cursor-pointer transition-all ${engine === eng.id ? 'bg-secondary/10 border-2 border-secondary shadow-[0_0_25px_rgba(91,218,198,0.25)]' : 'bg-surface-container-high border border-white/5 hover:border-white/20'}`}
                    onClick={() => setEngine(eng.id)}>
                    {eng.recommended && (
                      <div className="absolute -top-3 right-4 bg-secondary text-on-secondary text-[10px] font-bold px-2 py-0.5 rounded-full tracking-tighter">
                        RECOMENDADO
                      </div>
                    )}
                    <div className="flex justify-between items-start mb-4">
                      <span className={`material-symbols-outlined ${engine === eng.id ? 'text-secondary' : 'text-on-surface-variant'}`}>{eng.icon}</span>
                    </div>
                    <h4 className={`font-bold ${engine === eng.id ? 'text-secondary' : 'text-on-surface'}`}>{eng.label}</h4>
                    <p className={`text-[12px] mt-2 leading-relaxed ${engine === eng.id ? 'text-secondary/80' : 'text-on-surface-variant'}`}>{eng.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-8">
              <button type="button"
                className="ps-dwell-bar w-full h-20 bg-secondary hover:bg-secondary-fixed transition-all rounded-xl text-on-secondary flex items-center justify-center gap-4 font-headline-md text-headline-md relative group overflow-hidden shadow-2xl"
                onMouseEnter={nextEnter}
                onMouseLeave={nextLeave}
                onClick={handleSubmit}>
                <span className="relative z-10">PRÓXIMO</span>
                <span className="material-symbols-outlined relative z-10 transition-transform group-hover:translate-x-2">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
