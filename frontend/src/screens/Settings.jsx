import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  .st-glass { background: rgba(30,32,36,0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }
  .st-slider::-webkit-slider-thumb { -webkit-appearance:none; width:32px; height:32px; background:#5bdac6; border-radius:50%; cursor:pointer; box-shadow:0 0 15px rgba(91,218,198,0.5); transition:transform 0.2s; }
  .st-slider::-webkit-slider-thumb:hover { transform:scale(1.2); }
  .st-slider { height:12px; background:#333539; border-radius:6px; appearance:none; cursor:pointer; }
`

const CURSOR_SIZES = ['Pequeno', 'Médio', 'Grande']
const VOICE_OPTIONS = ['PT-BR Feminino (Ana)', 'PT-BR Masculino (Carlos)']

function Toggle({ on, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className="w-14 h-8 rounded-full relative transition-all"
      style={{ background: on ? '#00a693' : '#333539' }}
    >
      <div className="absolute top-1 w-6 h-6 rounded-full bg-white transition-all" style={{ left: on ? 26 : 4 }} />
    </button>
  )
}

export default function Settings() {
  const navigate = useNavigate()
  const { sendMessage } = useGazeSocket()
  const [dwellTime, setDwellTime] = useState(800)
  const [cursorSize, setCursorSize] = useState('Médio')
  const [sensitivity, setSensitivity] = useState(1)
  const [soundFeedback, setSoundFeedback] = useState(true)
  const [autoSpeak, setAutoSpeak] = useState(false)
  const [voice, setVoice] = useState('PT-BR Masculino (Carlos)')
  const [speechSpeed, setSpeechSpeed] = useState(1)
  const [demoMode, setDemoMode] = useState(false)
  const [debugLogs, setDebugLogs] = useState(true)

  const { onMouseEnter: recalibEnter, onMouseLeave: recalibLeave } = useDwell(() =>
    navigate('/calibration', { state: { from: 'settings' } })
  )

  const handleSave = () => {
    sendMessage('update_dwell', { time: dwellTime })
  }

  return (
    <div className="h-full overflow-y-auto">
      <style>{CSS}</style>

      <div className="max-w-[1600px] mx-auto p-margin-desktop">
        <div className="flex flex-col lg:flex-row gap-gutter-desktop">

          {/* LEFT: Settings Core */}
          <div className="lg:w-[65%] space-y-gutter-desktop">

            {/* Rastreamento */}
            <section className="st-glass p-8 rounded-2xl">
              <div className="flex items-center gap-4 mb-8">
                <span className="material-symbols-outlined text-secondary text-3xl">track_changes</span>
                <h2 className="font-headline-lg text-headline-lg">Rastreamento e Interação</h2>
              </div>
              <div className="space-y-12">
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <label className="font-label-lg text-on-surface-variant">Dwell Time (Tempo de Espera)</label>
                    <span className="text-secondary font-bold text-2xl">{dwellTime}ms</span>
                  </div>
                  <input
                    type="range" min="300" max="2000" value={dwellTime}
                    onChange={(e) => setDwellTime(Number(e.target.value))}
                    className="w-full st-slider"
                  />
                  <div className="flex justify-between text-xs text-on-surface-variant font-bold">
                    <span>LENTO (2000ms)</span>
                    <span>RÁPIDO (300ms)</span>
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="font-label-lg text-on-surface-variant">Tamanho do Cursor</label>
                  <div className="grid grid-cols-3 gap-4">
                    {CURSOR_SIZES.map((size) => (
                      <button
                        key={size}
                        className={`h-20 rounded-xl border font-bold flex flex-col items-center justify-center gap-1 group transition-all ${cursorSize === size ? 'bg-secondary/10 border-2 border-secondary' : 'bg-surface-container border-outline-variant hover:border-secondary'}`}
                        onClick={() => setCursorSize(size)}
                      >
                        <div className={`rounded-full ${size === 'Pequeno' ? 'w-2 h-2' : size === 'Médio' ? 'w-4 h-4' : 'w-6 h-6'} ${cursorSize === size ? 'bg-secondary' : 'bg-on-surface-variant group-hover:bg-secondary'} transition-colors`} />
                        {size}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="font-label-lg text-on-surface-variant">Sensibilidade do Olhar</label>
                  <input
                    type="range" min="0" max="2" step="1" value={sensitivity}
                    onChange={(e) => setSensitivity(Number(e.target.value))}
                    className="w-full st-slider"
                  />
                  <div className="flex justify-between text-xs text-on-surface-variant font-bold">
                    <span>BAIXA</span><span>MÉDIA</span><span>ALTA</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Áudio */}
            <section className="st-glass p-8 rounded-2xl">
              <div className="flex items-center gap-4 mb-8">
                <span className="material-symbols-outlined text-secondary text-3xl">volume_up</span>
                <h2 className="font-headline-lg text-headline-lg">Áudio</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 bg-surface-container rounded-xl border border-outline-variant">
                    <span className="font-bold">Feedback Sonoro</span>
                    <Toggle on={soundFeedback} onToggle={() => setSoundFeedback((v) => !v)} />
                  </div>
                  <div className="flex items-center justify-between p-4 bg-surface-container rounded-xl border border-outline-variant">
                    <span className="font-bold">TTS Automático</span>
                    <Toggle on={autoSpeak} onToggle={() => setAutoSpeak((v) => !v)} />
                  </div>
                </div>
                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="font-label-lg text-on-surface-variant text-xs">Voz Selecionada</label>
                    <select
                      value={voice}
                      onChange={(e) => setVoice(e.target.value)}
                      className="w-full h-14 bg-surface-container border-outline-variant rounded-xl px-4 text-on-surface font-bold focus:ring-secondary focus:border-secondary border"
                    >
                      {VOICE_OPTIONS.map((v) => <option key={v}>{v}</option>)}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="font-label-lg text-on-surface-variant text-xs">Velocidade da Fala</label>
                    <input
                      type="range" min="0.5" max="2" step="0.1" value={speechSpeed}
                      onChange={(e) => setSpeechSpeed(Number(e.target.value))}
                      className="w-full st-slider"
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* Interface */}
            <section className="st-glass p-8 rounded-2xl">
              <div className="flex items-center gap-4 mb-8">
                <span className="material-symbols-outlined text-secondary text-3xl">palette</span>
                <h2 className="font-headline-lg text-headline-lg">Interface</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  { label: 'Modo Noturno', value: 'ATIVADO', active: true },
                  { label: 'Animações', value: 'ATIVADO', active: true },
                ].map((item) => (
                  <div key={item.label} className="p-4 bg-surface-container rounded-xl border border-outline-variant flex flex-col gap-4">
                    <span className="font-bold text-sm">{item.label}</span>
                    <div className={`w-full h-12 ${item.active ? 'bg-secondary text-on-secondary' : 'bg-surface-bright text-on-surface-variant'} rounded-lg flex items-center justify-center font-bold`}>
                      {item.value}
                    </div>
                  </div>
                ))}
                <div className="p-4 bg-surface-container rounded-xl border border-outline-variant flex flex-col gap-4">
                  <span className="font-bold text-sm">Fonte Principal</span>
                  <div className="flex gap-1 h-12">
                    <button className="flex-1 bg-surface-variant rounded-l-lg text-xs font-bold">PADRÃO</button>
                    <button className="flex-1 bg-secondary text-on-secondary text-sm font-bold">GRANDE</button>
                    <button className="flex-1 bg-surface-variant rounded-r-lg text-lg font-bold">MAX</button>
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* RIGHT: User + Calibration */}
          <div className="lg:w-[35%] space-y-gutter-desktop">
            {/* Profile card */}
            <div className="st-glass p-8 rounded-2xl border-t-2 border-t-secondary/50">
              <div className="flex flex-col items-center text-center mb-8">
                <div className="relative mb-4">
                  <div className="w-24 h-24 rounded-full bg-primary-container border-4 border-secondary flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>person</span>
                  </div>
                  <div className="absolute bottom-0 right-0 w-6 h-6 bg-secondary rounded-full border-4 border-surface flex items-center justify-center">
                    <span className="material-symbols-outlined text-[12px] text-on-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
                  </div>
                </div>
                <h3 className="font-headline-md text-xl">Usuário Ativo</h3>
                <p className="text-on-surface-variant text-sm font-mono tracking-wider">USER_ID: 001-IF</p>
              </div>
              <div className="space-y-3">
                <button className="w-full h-16 bg-surface-container-high hover:bg-surface-variant border border-outline-variant rounded-xl font-bold transition-all uppercase tracking-widest text-xs"
                  onClick={() => navigate('/profile-setup')}>
                  Editar Perfil
                </button>
              </div>
            </div>

            {/* Calibration card */}
            <div className="st-glass p-8 rounded-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <span className="material-symbols-outlined text-8xl">biotech</span>
              </div>
              <h4 className="font-label-lg text-on-surface-variant mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">verified</span>
                ESTADO DA CALIBRAÇÃO
              </h4>
              <div className="mb-6">
                <div className="text-4xl font-bold text-on-surface mb-1">94.2%</div>
                <p className="text-secondary text-sm font-bold">ALTA PRECISÃO ATIVA</p>
                <p className="text-on-surface-variant text-[10px] mt-2 italic">Última atualização: Hoje</p>
              </div>
              <button
                className="w-full h-20 bg-error-container text-on-error-container hover:brightness-110 rounded-xl font-bold flex items-center justify-center gap-3 transition-all hover:scale-[1.02] shadow-lg"
                onMouseEnter={recalibEnter}
                onMouseLeave={recalibLeave}
                onClick={() => navigate('/calibration', { state: { from: 'settings' } })}
              >
                <span className="material-symbols-outlined">refresh</span>
                RECALIBRAR AGORA
              </button>
            </div>

            {/* System info */}
            <div className="st-glass p-6 rounded-2xl space-y-4">
              <div className="flex justify-between items-center">
                <h4 className="font-label-lg text-on-surface-variant text-xs">SISTEMA</h4>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-secondary" />
                  <span className="text-[10px] font-bold text-secondary">CONECTADO</span>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                {[{ label: 'Versão', val: 'v0.1.0-mvp' }, { label: 'Backend', val: 'iris-core' }, { label: 'Engine', val: 'Flow-Render v4' }].map((r) => (
                  <div key={r.label} className="flex justify-between border-b border-outline-variant/10 pb-2">
                    <span className="text-on-surface-variant">{r.label}:</span>
                    <span className="font-mono">{r.val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div className="st-glass p-6 rounded-2xl space-y-4">
              <h4 className="font-label-lg text-on-surface-variant text-xs uppercase tracking-widest">Ações Rápidas</h4>
              <div className="space-y-3">
                {[
                  { label: 'Modo Demo', state: demoMode, toggle: () => setDemoMode((v) => !v) },
                  { label: 'Logs de Debug', state: debugLogs, toggle: () => setDebugLogs((v) => !v) },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between p-3 bg-surface-container-lowest rounded-lg">
                    <span className="text-xs font-bold">{item.label}</span>
                    <input type="checkbox" checked={item.state} onChange={item.toggle}
                      className="rounded border-secondary text-secondary focus:ring-secondary bg-surface" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom actions */}
        <div className="mt-12 flex flex-col md:flex-row gap-6 pt-12 border-t border-outline-variant/20">
          <button
            className="flex-[2] h-20 bg-secondary text-on-secondary text-headline-md rounded-2xl font-bold shadow-2xl shadow-secondary/20 hover:scale-[1.01] transition-all flex items-center justify-center gap-4"
            onClick={handleSave}
          >
            <span className="material-symbols-outlined text-3xl">save</span>
            SALVAR CONFIGURAÇÕES
          </button>
          <button className="flex-1 h-20 bg-surface-container-highest text-on-surface rounded-2xl font-bold hover:bg-surface-variant transition-all flex items-center justify-center gap-4">
            <span className="material-symbols-outlined">restart_alt</span>
            RESTAURAR PADRÕES
          </button>
        </div>
      </div>
    </div>
  )
}
