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
  green: '#4ae176',
  error: '#ffb4ab',
  errorBg: '#93000a',
}

export default function Settings() {
  const navigate = useNavigate()
  const [dwellTime, setDwellTime] = useState(800)
  const [fontSize, setFontSize] = useState(24)
  const [nightMode, setNightMode] = useState(true)
  const [soundFeedback, setSoundFeedback] = useState(false)

  const { onMouseEnter: recalibEnter, onMouseLeave: recalibLeave } = useDwell(() => navigate('/calibration'))

  return (
    <div className="overflow-y-auto p-12" style={{ color: COLORS.text }}>
        <div className="max-w-5xl mx-auto">

          {/* Header */}
          <div className="flex items-end justify-between mb-10">
            <div>
              <h1 className="font-bold text-4xl mb-2" style={{ color: COLORS.text }}>Configurações</h1>
              <div className="h-1 w-24 rounded-full" style={{ background: COLORS.cyan, boxShadow: '0 0 10px #00d9ff' }} />
            </div>
            <button
              className="flex items-center gap-3 px-6 rounded-xl font-bold uppercase tracking-widest transition-all hover:scale-105 active:scale-95"
              style={{
                height: 60,
                background: COLORS.errorBg,
                color: COLORS.error,
                border: `1px solid rgba(255,180,171,0.3)`,
                boxShadow: '0 0 20px rgba(255,180,171,0.2)',
                fontSize: 14,
              }}
              onMouseEnter={recalibEnter}
              onMouseLeave={recalibLeave}
              onClick={() => navigate('/calibration')}
            >
              <span className="material-symbols-outlined animate-pulse">target</span>
              Recalibrar
            </button>
          </div>

          <div className="grid grid-cols-12 gap-6">

            {/* Rastreamento */}
            <section
              className="col-span-8 rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden"
              style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="material-symbols-outlined" style={{ color: COLORS.cyan }}>visibility</span>
                <h3 className="font-mono uppercase tracking-wider text-sm" style={{ color: COLORS.cyan }}>
                  Rastreamento e Interação
                </h3>
              </div>

              {/* Dwell time */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <label style={{ color: COLORS.muted }}>Dwell Time (Tempo de Fixação)</label>
                  <span className="font-bold" style={{ color: COLORS.cyan }}>{dwellTime}ms</span>
                </div>
                <div className="p-4 rounded-xl" style={{ background: 'rgba(37,42,56,0.8)' }}>
                  <input
                    type="range" min="200" max="2000" value={dwellTime}
                    onChange={e => setDwellTime(Number(e.target.value))}
                    className="w-full cursor-pointer accent-cyan-400"
                    style={{ accentColor: COLORS.cyan }}
                  />
                </div>
                <p className="text-sm" style={{ color: COLORS.muted }}>
                  Define quanto tempo o olhar deve permanecer em um alvo para ativar a ação.
                </p>
              </div>

              {/* Tamanho fonte */}
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <label style={{ color: COLORS.muted }}>Tamanho da Fonte HUD</label>
                  <span className="font-bold" style={{ color: COLORS.cyan }}>
                    {fontSize <= 16 ? 'Pequeno' : fontSize <= 24 ? 'Grande' : 'Muito Grande'} ({fontSize}px)
                  </span>
                </div>
                <div className="p-4 rounded-xl" style={{ background: 'rgba(37,42,56,0.8)' }}>
                  <input
                    type="range" min="12" max="48" value={fontSize}
                    onChange={e => setFontSize(Number(e.target.value))}
                    className="w-full cursor-pointer"
                    style={{ accentColor: COLORS.cyan }}
                  />
                </div>
                <p className="text-sm" style={{ color: COLORS.muted }}>
                  Ajusta a legibilidade global do sistema para diferentes distâncias oculares.
                </p>
              </div>

              {/* Cards perfil + sobre */}
              <div className="grid grid-cols-2 gap-4 mt-2">
                {/* Perfil */}
                <div
                  className="rounded-xl p-6 flex flex-col gap-4"
                  style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-16 h-16 rounded-full flex items-center justify-center"
                      style={{ background: COLORS.cyanBg }}
                    >
                      <span className="material-symbols-outlined" style={{ color: COLORS.cyan }}>person</span>
                    </div>
                    <div>
                      <h3 className="font-bold" style={{ color: COLORS.text }}>Perfil do Usuário</h3>
                      <p style={{ color: COLORS.muted, fontSize: 13 }}>Usuário Padrão</p>
                    </div>
                  </div>
                  <div className="h-px w-full" style={{ background: COLORS.border }} />
                  <button
                    className="w-full flex items-center justify-center gap-2 rounded-xl font-mono text-xs uppercase tracking-widest transition-all hover:bg-white/5"
                    style={{
                      height: 48,
                      color: COLORS.cyan,
                      border: `1px solid rgba(0,217,255,0.2)`,
                    }}
                    onClick={() => navigate('/profile-setup')}
                  >
                    Editar Dados
                    <span className="material-symbols-outlined text-sm">edit</span>
                  </button>
                </div>

                {/* Sobre */}
                <div
                  className="rounded-xl p-6 flex flex-col gap-3"
                  style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
                >
                  <h3 className="font-bold mb-2" style={{ color: COLORS.text }}>Sobre o Sistema</h3>
                  {[
                    { label: 'Versão', value: 'v0.1.0-mvp', highlight: true },
                    { label: 'Backend', value: 'FastAPI 8765', highlight: false },
                    { label: 'Status', value: 'Conectado', highlight: true },
                  ].map(({ label, value, highlight }) => (
                    <div key={label} className="flex justify-between text-sm">
                      <span style={{ color: COLORS.muted }}>{label}</span>
                      <span style={{ color: highlight ? COLORS.cyan : COLORS.text }}>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Ações rápidas + diagnóstico */}
            <aside className="col-span-4 flex flex-col gap-4">
              <div
                className="rounded-2xl p-6 flex flex-col gap-4"
                style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
              >
                <h3 className="font-bold" style={{ color: COLORS.text }}>Ações Rápidas</h3>

                {/* Modo noturno */}
                <div
                  className="flex items-center justify-between p-4 rounded-xl"
                  style={{ background: 'rgba(37,42,56,0.6)', border: `1px solid ${COLORS.border}` }}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined" style={{ color: COLORS.muted }}>settings</span>
                    <span style={{ color: COLORS.text }}>Modo Noturno</span>
                  </div>
                  <button
                    onClick={() => setNightMode(!nightMode)}
                    className="w-12 h-6 rounded-full transition-all relative"
                    style={{ background: nightMode ? COLORS.cyan : COLORS.border }}
                  >
                    <div
                      className="absolute top-1 w-4 h-4 rounded-full bg-white transition-all"
                      style={{ left: nightMode ? 26 : 4 }}
                    />
                  </button>
                </div>

                {/* Feedback sonoro */}
                <div
                  className="flex items-center justify-between p-4 rounded-xl"
                  style={{ background: 'rgba(37,42,56,0.6)', border: `1px solid ${COLORS.border}` }}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined" style={{ color: COLORS.muted }}>volume_up</span>
                    <span style={{ color: COLORS.text }}>Feedback Sonoro</span>
                  </div>
                  <button
                    onClick={() => setSoundFeedback(!soundFeedback)}
                    className="w-12 h-6 rounded-full transition-all relative"
                    style={{ background: soundFeedback ? COLORS.cyan : COLORS.border }}
                  >
                    <div
                      className="absolute top-1 w-4 h-4 rounded-full bg-white transition-all"
                      style={{ left: soundFeedback ? 26 : 4 }}
                    />
                  </button>
                </div>
              </div>

              {/* Diagnóstico */}
              <div
                className="rounded-2xl p-6 flex flex-col gap-3 flex-1"
                style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}
              >
                <div className="flex items-center justify-center h-32 rounded-xl mb-2" style={{ background: 'rgba(0,217,255,0.05)' }}>
                  <span className="material-symbols-outlined text-6xl" style={{ color: 'rgba(0,217,255,0.3)' }}>
                    radar
                  </span>
                </div>
                <h3 className="font-bold" style={{ color: COLORS.text }}>Diagnóstico</h3>
                <p style={{ color: COLORS.green, fontSize: 14 }}>Sensores 98% Otimizados</p>
              </div>
            </aside>

          </div>
        </div>
    </div>
  )
}
