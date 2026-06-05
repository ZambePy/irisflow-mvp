import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'
import { useAppStore } from '../store/appStore'
import { useGazeSocket } from '../context/GazeSocketContext'
import { api } from '../api/http'

const CSS = `
  .glass-card {
    background: rgba(30, 32, 36, 0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(140, 145, 153, 0.1);
  }
  .ps-dwell-btn::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0;
    height: 3px; width: 0%;
    background: rgba(91, 218, 198, 0.8);
    border-radius: 9999px;
    transition: width 1.5s linear;
  }
  .ps-dwell-btn:hover::after { width: 100%; }
`

const DWELL_OPTIONS = [
  { label: 'Lento',  sub: '2000ms', value: 2000 },
  { label: 'Normal', sub: '1000ms', value: 1000 },
  { label: 'Rápido', sub: '500ms',  value: 500  },
]
const CURSOR_OPTIONS = ['Pequeno', 'Médio', 'Grande']
const ENGINES = [
  { id: 'mock',          label: 'Mock Engine', icon: 'visibility_off', desc: 'Simulação de Software' },
  { id: 'iris-gaze-net', label: 'IrisGazeNet', icon: 'psychology',     desc: 'Precisão Neural V4.2', recommended: true },
]

export default function ProfileSetup() {
  const navigate = useNavigate()
  const { sendMessage } = useGazeSocket()
  const [name,      setName]      = useState('')
  const [lang,      setLang]      = useState('pt-BR')
  const [dwell,     setDwell]     = useState(1000)
  const [cursorIdx, setCursorIdx] = useState(1)
  const [engine,    setEngine]    = useState('iris-gaze-net')

  const cursor = CURSOR_OPTIONS[cursorIdx]

  const { onMouseEnter: nextEnter, onMouseLeave: nextLeave } = useDwell(handleSubmit)

  async function handleSubmit() {
    if (!name.trim()) {
      document.querySelector('input')?.focus()
      return
    }
    const localProfile = { name: name.trim(), dwell_time_ms: dwell, tracking_engine: engine, cursor_size: cursor, lang }
    useAppStore.getState().setActiveProfile(localProfile)
    useAppStore.getState().setDwellTime(dwell)
    useAppStore.getState().setTrackingEngine(engine)

    const savedProfile = await api.createProfile({ name: name.trim(), dwell_time_ms: dwell, tracking_engine: engine })
    if (savedProfile) {
      useAppStore.getState().setActiveProfile({ ...savedProfile, cursor_size: cursor, lang })
    }

    sendMessage('set_engine', { engine })
    sessionStorage.setItem('profile_setup_done', 'true')
    navigate('/calibration', { state: { from: 'onboarding', name: name.trim() } })
  }

  const cursorPct   = cursorIdx * 50
  const thumbLeft   = cursorIdx === 0 ? '0%' : cursorIdx === 2 ? '100%' : '50%'
  const thumbXShift = cursorIdx === 0 ? 'translateX(0)' : cursorIdx === 2 ? 'translateX(-100%)' : 'translateX(-50%)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}
      className="font-body-md bg-background text-on-surface overflow-x-hidden">
      <style>{CSS}</style>

      {/* Ambient radial glows */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full"
          style={{ background: 'rgba(160,202,252,0.05)', filter: 'blur(120px)' }} />
        <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] rounded-full"
          style={{ background: 'rgba(91,218,198,0.05)', filter: 'blur(100px)' }} />
      </div>

      {/* ── Topbar ──────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 w-full px-12 h-20 flex justify-between items-center bg-surface/80 backdrop-blur-3xl border-b border-outline-variant/10">
        <div className="flex items-center gap-12">
          <span className="font-headline-md text-headline-md font-extrabold text-primary tracking-tight">IrisFlow</span>
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2 text-secondary">
              <span className="w-8 h-8 rounded-full border-2 border-secondary flex items-center justify-center font-bold text-label-lg bg-secondary/10"
                style={{ boxShadow: '0 0 0 4px rgba(91,218,198,0.2)' }}>1</span>
              <span className="font-label-lg uppercase tracking-wider">Profile</span>
            </div>
            <div className="h-[2px] w-8 bg-outline-variant/30" />
            <div className="flex items-center gap-2 text-on-surface-variant/40">
              <span className="w-8 h-8 rounded-full border-2 border-outline-variant/30 flex items-center justify-center font-bold text-label-lg">2</span>
              <span className="font-label-lg uppercase tracking-wider">Calibration</span>
            </div>
            <div className="h-[2px] w-8 bg-outline-variant/30" />
            <div className="flex items-center gap-2 text-on-surface-variant/40">
              <span className="w-8 h-8 rounded-full border-2 border-outline-variant/30 flex items-center justify-center font-bold text-label-lg">3</span>
              <span className="font-label-lg uppercase tracking-wider">Ready</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="px-4 py-1.5 rounded-full border border-secondary/30 flex items-center gap-2"
            style={{ background: 'rgba(0,166,147,0.1)' }}>
            <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
            <span className="text-secondary font-eye-track-label text-[12px] uppercase tracking-[0.1em]">Calibration Active</span>
          </div>
          <div className="flex items-center gap-4 text-on-surface-variant">
            <span className="material-symbols-outlined text-[20px]">visibility</span>
            <span className="material-symbols-outlined text-[20px]">sensors</span>
            <div className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[20px]">battery_full</span>
              <span className="font-label-lg text-secondary">98%</span>
            </div>
          </div>
        </div>
      </nav>

      {/* ── Main (scrollable) ────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflowY: 'auto', paddingBottom: '100px' }}
        className="flex flex-col items-center py-16 px-6">

        <header className="text-center mb-12">
          <h1 className="font-headline-lg text-headline-lg text-secondary mb-2">Configurar Perfil</h1>
          <p className="font-body-lg text-on-surface-variant">Etapa 1 de 3 — Informações Básicas</p>
        </header>

        {/* ── Configuration Card ─────────────────────────────────────── */}
        <section className="glass-card w-full max-w-[800px] rounded-3xl p-10 flex flex-col gap-10">

          {/* Nome */}
          <div className="flex flex-col gap-4">
            <label className="font-label-lg text-on-surface-variant uppercase tracking-widest pl-2">Nome Completo</label>
            <input
              className="w-full h-20 bg-surface-container border-2 border-outline-variant/30 rounded-2xl px-8 font-headline-md text-headline-md text-on-surface placeholder:text-on-surface-variant/30 focus:border-secondary outline-none transition-all focus:bg-surface-container-high"
              placeholder="Como devemos chamar você?"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>

          {/* Idioma + Velocidade do Olhar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="flex flex-col gap-4">
              <label className="font-label-lg text-on-surface-variant uppercase tracking-widest pl-2">Idioma</label>
              <div className="flex gap-3">
                {['pt-BR', 'en-US'].map(l => (
                  <button key={l} type="button"
                    className={`flex-1 py-4 px-6 rounded-xl font-label-lg border-2 transition-all ${
                      lang === l
                        ? 'bg-secondary-container text-on-secondary-container border-secondary'
                        : 'border-outline-variant/30 text-on-surface-variant hover:border-secondary'
                    }`}
                    style={lang === l ? { boxShadow: '0 0 0 2px rgba(91,218,198,0.2)' } : {}}
                    onClick={() => setLang(l)}>
                    {l.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-4">
              <label className="font-label-lg text-on-surface-variant uppercase tracking-widest pl-2">Velocidade do Olhar</label>
              <div className="flex bg-surface-container rounded-xl p-1.5 gap-1">
                {DWELL_OPTIONS.map(opt => (
                  <button key={opt.value} type="button"
                    className={`flex-1 py-3 px-2 rounded-lg font-label-lg transition-all ${
                      dwell === opt.value
                        ? 'bg-secondary text-on-secondary font-bold shadow-lg'
                        : 'text-on-surface-variant hover:bg-surface-bright/30'
                    }`}
                    onClick={() => setDwell(opt.value)}>
                    {opt.label}
                    <span className={`block text-[10px] ${dwell === opt.value ? 'opacity-80' : 'opacity-60'}`}>{opt.sub}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Tamanho do Cursor — slider */}
          <div className="flex flex-col gap-4">
            <label className="font-label-lg text-on-surface-variant uppercase tracking-widest pl-2">Tamanho do Cursor</label>
            <div className="flex items-center justify-between gap-6 px-4">
              <span className={`font-label-lg shrink-0 transition-colors ${cursorIdx === 0 ? 'text-secondary font-bold' : 'text-on-surface-variant'}`}>Pequeno</span>
              <div className="flex-1 relative h-2 bg-surface-container rounded-full">
                <div className="absolute left-0 top-0 h-full bg-secondary rounded-full transition-all duration-200"
                  style={{ width: `${cursorPct}%` }} />
                <div className="pointer-events-none absolute w-8 h-8 bg-secondary rounded-full border-4 border-surface ring-2 ring-secondary/20 transition-all duration-200"
                  style={{ top: '50%', left: thumbLeft, transform: `${thumbXShift} translateY(-50%)`, boxShadow: '0 0 15px rgba(91,218,198,0.5)' }} />
                <input type="range" min="0" max="2" step="1"
                  value={cursorIdx}
                  onChange={e => setCursorIdx(Number(e.target.value))}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
              </div>
              <span className={`font-label-lg shrink-0 transition-colors ${cursorIdx === 1 ? 'text-secondary font-bold' : 'text-on-surface-variant opacity-40'}`}>Médio</span>
              <span className={`font-label-lg shrink-0 transition-colors ${cursorIdx === 2 ? 'text-secondary font-bold' : 'text-on-surface-variant opacity-40'}`}>Grande</span>
            </div>
          </div>

          {/* Motor de Rastreamento */}
          <div className="flex flex-col gap-4">
            <label className="font-label-lg text-on-surface-variant uppercase tracking-widest pl-2">Motor de Rastreamento</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {ENGINES.map(eng => {
                const sel = engine === eng.id
                return (
                  <div key={eng.id}
                    className={`h-[120px] rounded-2xl border-2 p-5 flex items-center gap-4 cursor-pointer relative transition-all duration-200 ${
                      sel
                        ? 'border-secondary bg-secondary-container/10'
                        : 'border-outline-variant/20 bg-surface-container/40 opacity-60 hover:opacity-90 hover:border-outline-variant/40'
                    }`}
                    style={sel ? { boxShadow: '0 0 20px rgba(91,218,198,0.3)' } : {}}
                    onClick={() => setEngine(eng.id)}>
                    {eng.recommended && (
                      <div className="absolute top-3 right-3 bg-secondary text-on-secondary px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-tighter">
                        Recomendado
                      </div>
                    )}
                    <div className={`w-12 h-12 shrink-0 rounded-xl flex items-center justify-center ${sel ? 'bg-secondary-container' : 'bg-surface-variant/50'}`}>
                      <span className={`material-symbols-outlined ${sel ? 'text-on-secondary-container' : 'text-on-surface-variant'}`}
                        style={sel && eng.id === 'iris-gaze-net' ? { fontVariationSettings: "'FILL' 1" } : {}}>
                        {eng.icon}
                      </span>
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className={`font-headline-md text-[18px] font-bold ${sel ? 'text-on-surface' : 'text-on-surface-variant'}`}>{eng.label}</span>
                      <span className={`font-label-lg text-[12px] ${sel ? 'text-secondary' : 'text-on-surface-variant/60'}`}>{eng.desc}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        {/* Tech footer — dentro do main (scrollável) */}
        <div className="w-full max-w-[800px] mt-16 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="px-3 py-1 bg-surface-variant/30 rounded font-mono text-[10px] text-on-surface-variant tracking-widest border border-outline-variant/10">
              SISTEMA: IRISFLOW 2.4.0-STABLE [KRNL: GAZE_V9]
            </div>
            <div className="w-px h-4 bg-outline-variant/20" />
            <span className="text-[12px] text-on-surface-variant/60 font-medium">CONEXÃO SEGURA TLS 1.3</span>
          </div>
          <div className="flex items-center gap-8 font-label-lg text-on-surface-variant/40">
            <a className="hover:text-secondary transition-colors uppercase tracking-widest" href="#">Política de Privacidade</a>
            <a className="hover:text-secondary transition-colors uppercase tracking-widest" href="#">Suporte Técnico</a>
            <a className="hover:text-secondary transition-colors uppercase tracking-widest" href="#">Docs</a>
          </div>
        </div>
      </main>

      {/* ── Action footer — FIXO no rodapé ──────────────────────────────── */}
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 40,
        background: 'rgba(17,19,24,0.95)',
        backdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(66,71,79,0.15)',
        padding: '16px 48px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <button type="button"
          className="h-14 px-8 rounded-full border-2 border-outline-variant/30 text-on-surface-variant font-label-lg flex items-center gap-3 hover:border-secondary hover:text-secondary transition-all"
          onClick={() => navigate('/')}>
          <span className="material-symbols-outlined">arrow_back</span>
          Voltar para Home
        </button>
        <button type="button"
          className="ps-dwell-btn relative h-14 px-12 rounded-full bg-secondary text-on-secondary font-bold text-headline-md flex items-center gap-4 shadow-lg overflow-hidden transition-all"
          onMouseEnter={nextEnter}
          onMouseLeave={nextLeave}
          onClick={handleSubmit}>
          PRÓXIMO
          <span className="material-symbols-outlined">arrow_forward</span>
        </button>
      </div>
    </div>
  )
}
