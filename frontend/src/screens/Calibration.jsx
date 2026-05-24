import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

// --- 6 pontos em padrao circular
const POINTS = [
  { top: '10%', left: '50%' },
  { top: '25%', left: '85%' },
  { top: '75%', left: '85%' },
  { top: '90%', left: '50%' },
  { top: '75%', left: '15%' },
  { top: '25%', left: '15%' },
]

// --- CalibrationPoint
function CalibrationPoint({ point, isActive, isDone, onActivate }) {
  const { onMouseEnter, onMouseLeave } = useDwell(onActivate, 1500)

  return (
    <div
      className={`calibration-point absolute w-10 h-10 -ml-5 -mt-5 rounded-full glass-panel border-2 flex items-center justify-center cursor-pointer transition-all duration-400 ${
        isActive
          ? 'border-secondary/50 shadow-[0_0_25px_rgba(0,166,147,0.8)] scale-110 active'
          : isDone
          ? 'border-secondary/20 opacity-40'
          : 'border-secondary/20'
      }`}
      style={{ top: point.top, left: point.left }}
      onMouseEnter={isActive ? onMouseEnter : undefined}
      onMouseLeave={isActive ? onMouseLeave : undefined}
      onClick={isActive ? onActivate : undefined}
    >
      <div
        className={`rounded-full transition-all duration-300 ${
          isActive
            ? 'w-4 h-4 bg-secondary'
            : isDone
            ? 'w-3 h-3 bg-secondary/50'
            : 'w-2 h-2 bg-secondary/40'
        }`}
      />
    </div>
  )
}

// --- Calibration
export default function Calibration() {
  const navigate = useNavigate()
  const [activeIndex, setActiveIndex] = useState(0)
  const [completed, setCompleted] = useState(false)

  const progress = Math.round((activeIndex / POINTS.length) * 100)

  const advancePoint = useCallback(() => {
    if (activeIndex < POINTS.length - 1) {
      setActiveIndex((i) => i + 1)
    } else {
      setCompleted(true)
      setTimeout(() => navigate('/'), 2000)
    }
  }, [activeIndex, navigate])

  const { onMouseEnter: startDwell, onMouseLeave: cancelDwell } = useDwell(advancePoint)

  return (
    <>
      {/* Topbar calibracao */}
      <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-margin-desktop h-hit-area-min bg-surface-container/80 backdrop-blur-xl border-b border-outline-variant/15">
        <div className="flex items-center gap-4">
          <span className="font-display text-headline-lg text-primary tracking-tighter">
            IrisFlow
          </span>
          <span className="font-label-caps text-label-caps text-on-surface-variant border-l border-outline-variant/30 pl-4">
            Modo Calibração
          </span>
        </div>
        <div className="flex items-center gap-gutter">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-primary-container/20 border border-primary/20">
            <span
              className="material-symbols-outlined text-primary"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              visibility
            </span>
            <span className="font-label-caps text-label-caps text-on-primary-container">
              Gaze Ativo
            </span>
          </div>
          <div className="flex gap-4 text-on-surface-variant">
            <span className="material-symbols-outlined">battery_full</span>
            <span className="material-symbols-outlined">wifi</span>
          </div>
        </div>
      </header>

      {/* Sidebar colapsada */}
      <nav className="fixed left-0 top-0 h-full flex flex-col py-margin-desktop z-40 bg-surface/50 w-20 border-r border-outline-variant/15 backdrop-blur-2xl">
        <div className="flex flex-col items-center gap-8 mt-20">
          <button
            className="w-14 h-14 rounded-xl flex items-center justify-center text-on-surface-variant hover:bg-surface-variant/30 transition-all"
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>

          <div className="w-8 h-px bg-outline-variant/30" />

          <div className="w-14 h-14 rounded-xl flex items-center justify-center text-secondary bg-secondary-container/20 border border-secondary/40 shadow-[0_0_15px_rgba(0,166,147,0.2)]">
            <span
              className="material-symbols-outlined"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              compass_calibration
            </span>
          </div>

          <button className="w-14 h-14 rounded-xl flex items-center justify-center text-on-surface-variant hover:bg-surface-variant/30 transition-all">
            <span className="material-symbols-outlined">help</span>
          </button>
        </div>
      </nav>

      {/* Canvas */}
      <main className="relative w-full h-screen flex flex-col items-center justify-center pl-20 pt-hit-area-min pb-24">
        <div className="relative w-[500px] h-[500px] flex items-center justify-center">
          {/* Aneis rotativos */}
          <div className="shutter-ring absolute inset-0 rounded-full opacity-20" />
          <div
            className="shutter-ring absolute inset-8 rounded-full opacity-10"
            style={{ animationDirection: 'reverse', animationDuration: '30s' }}
          />

          {/* Preview camera */}
          <div className="relative w-80 h-80 rounded-full overflow-hidden border-4 border-primary-container/40 shadow-2xl glass-panel">
            {/* Placeholder - trocar por video quando camera conectada */}
            <div className="w-full h-full bg-surface-container-lowest flex items-center justify-center">
              <span
                className="material-symbols-outlined text-secondary/30 text-[120px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                face
              </span>
            </div>

            {/* Sobreposicoes digitais */}
            <div className="scanline" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-full h-[2px] bg-secondary/20 shadow-[0_0_10px_rgba(0,166,147,0.5)]" />
            </div>

            {/* Vetores oculares */}
            <div className="absolute top-1/2 left-1/4 w-12 h-12 -mt-6 rounded-full border border-secondary/60 flex items-center justify-center">
              <div className="w-1 h-8 bg-secondary/80 origin-center rotate-45" />
            </div>
            <div className="absolute top-1/2 right-1/4 w-12 h-12 -mt-6 rounded-full border border-secondary/60 flex items-center justify-center">
              <div className="w-1 h-8 bg-secondary/80 origin-center -rotate-12" />
            </div>
          </div>

          {/* Pontos calibracao */}
          <div className="absolute inset-0">
            {POINTS.map((point, i) => (
              <CalibrationPoint
                key={i}
                point={point}
                isActive={!completed && i === activeIndex}
                isDone={completed || i < activeIndex}
                onActivate={i === activeIndex ? advancePoint : undefined}
              />
            ))}
          </div>
        </div>

        {/* Instrucao */}
        <div className="mt-12 text-center max-w-lg z-10">
          {completed ? (
            <>
              <h1 className="font-headline-lg text-headline-lg text-secondary mb-4">
                Calibração concluída!
              </h1>
              <p className="text-body-lg text-on-surface-variant">
                Redirecionando para o painel…
              </p>
            </>
          ) : (
            <>
              <h1 className="font-headline-lg text-headline-lg text-secondary mb-4">
                Foque no ponto destacado
              </h1>
              <p className="text-body-lg text-on-surface-variant">
                Mantenha a cabeça estável e siga o círculo teal conforme ele se move pela
                tela. A calibração garante alta precisão no rastreamento.
              </p>

              {/* Botao inicio - dwell - so antes do primeiro avanco */}
              {activeIndex === 0 && (
                <button
                  className="mt-8 px-8 py-4 rounded-xl bg-secondary-container text-on-secondary-container font-label-caps text-label-caps shadow-[0_0_20px_rgba(0,166,147,0.4)] hover:scale-105 transition-all"
                  onMouseEnter={startDwell}
                  onMouseLeave={cancelDwell}
                  onClick={advancePoint}
                >
                  INICIAR CALIBRAÇÃO
                </button>
              )}
            </>
          )}
        </div>
      </main>

      {/* Footer progresso */}
      <footer className="fixed bottom-0 left-0 w-full h-24 flex items-center justify-between px-margin-desktop z-50 bg-surface-container/80 backdrop-blur-2xl border-t border-outline-variant/15">
        <div className="flex items-center gap-6 flex-1">
          <div className="flex flex-col gap-1">
            <span className="font-label-caps text-label-caps text-on-surface-variant">
              Progresso
            </span>
            <span className="font-headline-md text-headline-md text-primary">
              Ponto {activeIndex + 1} de {POINTS.length}
            </span>
          </div>

          <div className="flex-1 max-w-md h-3 bg-surface-container-highest rounded-full overflow-hidden">
            <div
              className="h-full bg-secondary shadow-[0_0_10px_#00A693] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          <span className="font-label-caps text-label-caps text-secondary">
            {progress}%
          </span>
        </div>

        <div className="flex items-center gap-gutter ml-12">
          <button
            className="px-8 h-14 rounded-xl border border-error/30 text-error font-label-caps text-label-caps hover:bg-error/10 transition-all"
            onClick={() => navigate('/')}
          >
            CANCELAR
          </button>
          <button
            className="px-8 h-14 rounded-xl bg-secondary-container text-on-secondary-container font-label-caps text-label-caps shadow-[0_0_20px_rgba(0,166,147,0.4)] hover:scale-105 transition-all"
            onClick={() => navigate('/')}
          >
            PULAR CALIBRAÇÃO
          </button>
        </div>
      </footer>

      {/* Tooltip ajuda */}
      <div className="fixed bottom-32 right-margin-desktop z-40">
        <div className="glass-panel p-6 rounded-2xl border border-secondary/30 flex items-start gap-4 max-w-xs shadow-2xl">
          <span className="material-symbols-outlined text-secondary flex-shrink-0">info</span>
          <p className="text-body-md text-on-surface">
            Se o rastreador perder seus olhos, certifique-se de estar em um ambiente bem iluminado.
          </p>
        </div>
      </div>
    </>
  )
}
