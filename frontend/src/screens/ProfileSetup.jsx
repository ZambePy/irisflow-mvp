import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

const COLORS = {
  bg: '#0e1320',
  surface: 'rgba(22,27,41,0.9)',
  card: 'rgba(37,42,56,0.6)',
  border: 'rgba(255,255,255,0.08)',
  borderActive: 'rgba(0,217,255,0.5)',
  cyan: '#00d9ff',
  cyanBg: 'rgba(0,217,255,0.1)',
  text: '#dee2f5',
  muted: '#859398',
}

function OptionBtn({ label, active, onClick, icon }) {
  const { onMouseEnter, onMouseLeave } = useDwell(onClick)
  return (
    <button
      className="w-full flex items-center justify-center gap-3 rounded-xl transition-all duration-200"
      style={{
        height: 80,
        background: active ? COLORS.cyanBg : COLORS.card,
        border: `1px solid ${active ? COLORS.borderActive : COLORS.border}`,
        color: active ? COLORS.cyan : COLORS.muted,
        boxShadow: active ? '0 0 15px rgba(0,217,255,0.2)' : 'none',
        fontSize: 18,
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
    >
      {icon && <span className="material-symbols-outlined">{icon}</span>}
      {label}
    </button>
  )
}

export default function ProfileSetup() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [lang, setLang] = useState('PT-BR')
  const [speed, setSpeed] = useState('Normal')
  const [cursorSize, setCursorSize] = useState('Médio')

  const { onMouseEnter: nextEnter, onMouseLeave: nextLeave } = useDwell(() => navigate('/calibration'))

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6 py-10"
      style={{ background: COLORS.bg, color: COLORS.text }}
    >
      {/* Topbar simples */}
      <header
        className="fixed top-0 left-0 w-full flex items-center justify-between px-12 z-50"
        style={{
          height: 80,
          background: 'rgba(14,19,32,0.8)',
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        <span className="font-bold text-xl" style={{ color: COLORS.cyan }}>IrisFlow</span>
        <div className="flex items-center gap-3 text-sm font-mono" style={{ color: COLORS.muted }}>
          <span className="material-symbols-outlined text-base">sensors</span>
          <span className="material-symbols-outlined text-base">battery_charging_full</span>
        </div>
      </header>

      {/* Conteúdo */}
      <main className="w-full max-w-3xl pt-24 flex flex-col gap-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="font-bold text-4xl mb-2" style={{ color: COLORS.cyan }}>Configurar Perfil</h1>
          <p style={{ color: COLORS.muted }}>Etapa 1 de 3 — Informações Básicas</p>
        </div>

        {/* Card principal */}
        <div
          className="rounded-2xl p-8 flex flex-col gap-8"
          style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}` }}
        >
          {/* Nome */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-mono tracking-widest uppercase" style={{ color: COLORS.muted }}>
              Nome Completo
            </label>
            <div className="relative">
              <input
                className="w-full rounded-xl px-6 outline-none transition-all"
                style={{
                  height: 80,
                  background: 'rgba(22,27,41,0.5)',
                  border: `1px solid ${name ? COLORS.borderActive : COLORS.border}`,
                  color: COLORS.cyan,
                  fontSize: 22,
                }}
                placeholder="Como devemos chamar você?"
                value={name}
                onChange={e => setName(e.target.value)}
              />
              <div
                className="absolute bottom-0 left-0 w-full"
                style={{ height: 2, background: 'rgba(60,73,77,0.4)' }}
              />
            </div>
          </div>

          {/* Grid de opções */}
          <div className="grid grid-cols-3 gap-6">
            {/* Idioma */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono tracking-widest uppercase" style={{ color: COLORS.muted }}>Idioma</label>
              <OptionBtn label="PT-BR" icon="language" active={lang === 'PT-BR'} onClick={() => setLang('PT-BR')} />
              <OptionBtn label="EN-US" icon="translate" active={lang === 'EN-US'} onClick={() => setLang('EN-US')} />
            </div>

            {/* Velocidade */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono tracking-widest uppercase" style={{ color: COLORS.muted }}>Velocidade do Clique</label>
              <OptionBtn label="Lento" active={speed === 'Lento'} onClick={() => setSpeed('Lento')} />
              <OptionBtn label="Normal" active={speed === 'Normal'} onClick={() => setSpeed('Normal')} />
              <OptionBtn label="Rápido" active={speed === 'Rápido'} onClick={() => setSpeed('Rápido')} />
            </div>

            {/* Tamanho cursor */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono tracking-widest uppercase" style={{ color: COLORS.muted }}>Tamanho do Cursor</label>
              <OptionBtn label="Pequeno" active={cursorSize === 'Pequeno'} onClick={() => setCursorSize('Pequeno')} />
              <OptionBtn label="Médio" active={cursorSize === 'Médio'} onClick={() => setCursorSize('Médio')} />
              <OptionBtn label="Grande" active={cursorSize === 'Grande'} onClick={() => setCursorSize('Grande')} />
            </div>
          </div>

          {/* Botão próximo */}
          <button
            className="w-full flex items-center justify-center gap-3 rounded-xl font-bold text-xl transition-all duration-200 hover:scale-105 active:scale-95"
            style={{
              height: 80,
              background: COLORS.cyan,
              color: '#003641',
              boxShadow: '0 0 30px rgba(0,217,255,0.4)',
              fontSize: 22,
              letterSpacing: '0.05em',
            }}
            onMouseEnter={nextEnter}
            onMouseLeave={nextLeave}
            onClick={() => navigate('/calibration')}
          >
            PRÓXIMO
            <span className="material-symbols-outlined">arrow_forward</span>
          </button>
        </div>

        {/* Footer */}
        <div className="flex justify-center gap-8 text-xs font-mono" style={{ color: COLORS.muted }}>
          <span>CALIBRAÇÃO ATIVA</span>
          <span>MODO HUD 2.4.0</span>
        </div>
      </main>
    </div>
  )
}
