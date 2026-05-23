import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

const POINTS = [
  { top: '10%', left: '50%' },
  { top: '25%', left: '85%' },
  { top: '75%', left: '85%' },
  { top: '90%', left: '50%' },
  { top: '75%', left: '15%' },
  { top: '25%', left: '15%' },
]

function CalibrationPoint({ point, isActive, onClick }) {
  return (
    <div
      className={`calibration-point absolute w-10 h-10 -ml-5 -mt-5 rounded-full glass-panel border-2 flex items-center justify-center cursor-pointer transition-all duration-400 ${
        isActive
          ? 'border-secondary/50 shadow-[0_0_25px_rgba(0,166,147,0.8)] scale-110'
          : 'border-secondary/20'
      }`}
      style={{ top: point.top, left: point.left }}
      onClick={onClick}
    >
      <div
        className={`rounded-full ${isActive ? 'w-4 h-4 bg-secondary' : 'w-2 h-2 bg-secondary/40'}`}
      />
    </div>
  )
}

export default function Calibration() {
  const navigate = useNavigate()
  const [activeIndex, setActiveIndex] = useState(0)
  const [completed, setCompleted] = useState(false)

  const progress = Math.round((activeIndex / POINTS.length) * 100)

  const advancePoint = () => {
    if (activeIndex < POINTS.length - 1) {
      setActiveIndex((i) => i + 1)
    } else {
      setCompleted(true)
      setTimeout(() => navigate('/'), 1500)
    }
  }

  const { onMouseEnter: startDwell, onMouseLeave: cancelDwell } = useDwell(advancePoint)

  return (
    <>
      {/* Canvas principal — offset para sidebar global (w-80) e topbar */}
      <main className="pl-80 pt-20 w-full h-screen flex flex-col items-center justify-center pb-24">
        {/* Gráfico do iris / câmera */}
        <div className="relative w-[500px] h-[500px] flex items-center justify-center">
          {/* Anéis rotativos decorativos */}
          <div className="shutter-ring absolute inset-0 rounded-full opacity-20" />
          <div
            className="shutter-ring absolute inset-8 rounded-full opacity-10"
            style={{ animationDirection: 'reverse', animationDuration: '30s' }}
          />

          {/* Janela de prévia da câmera */}
          <div className="relative w-80 h-80 rounded-full overflow-hidden border-4 border-primary-container/40 shadow-2xl glass-panel">
            {/* Placeholder de vídeo */}
            <div className="w-full h-full bg-surface-container-lowest flex items-center justify-center">
              <span
                className="material-symbols-outlined text-secondary/30 text-[120px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                face
              </span>
            </div>

            {/* Sobreposições digitais */}
            <div className="scanline" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-full h-[2px] bg-secondary/20 shadow-[0_0_10px_rgba(0,166,147,0.5)]" />
            </div>

            {/* Vetores oculares simulados */}
            <div className="absolute top-1/2 left-1/4 w-12 h-12 -mt-6 rounded-full border border-secondary/60 flex items-center justify-center">
              <div className="w-1 h-8 bg-secondary/80 origin-center rotate-45" />
            </div>
            <div className="absolute top-1/2 right-1/4 w-12 h-12 -mt-6 rounded-full border border-secondary/60 flex items-center justify-center">
              <div className="w-1 h-8 bg-secondary/80 origin-center -rotate-12" />
            </div>
          </div>

          {/* Pontos de calibração */}
          <div className="absolute inset-0">
            {POINTS.map((point, i) => (
              <CalibrationPoint
                key={i}
                point={point}
                isActive={i === activeIndex}
                onClick={i === activeIndex ? advancePoint : undefined}
              />
            ))}
          </div>
        </div>

        {/* Instrução */}
        <div className="mt-12 text-center max-w-lg z-10">
          {completed ? (
            <h1 className="font-headline-lg text-headline-lg text-secondary mb-4">
              Calibração concluída!
            </h1>
          ) : (
            <>
              <h1 className="font-headline-lg text-headline-lg text-secondary mb-4">
                Focus on the highlighted point
              </h1>
              <p className="text-body-lg text-on-surface-variant">
                Keep your head steady and follow the teal circle as it moves around the screen.
                Calibration ensures 99.8% gaze accuracy.
              </p>
              {/* Botão de início com dwell */}
              <button
                className="mt-8 px-8 py-4 rounded-xl bg-secondary-container text-on-secondary-container font-label-caps text-label-caps shadow-[0_0_20px_rgba(0,166,147,0.4)] hover:scale-105 transition-all"
                onMouseEnter={startDwell}
                onMouseLeave={cancelDwell}
                onClick={advancePoint}
              >
                INICIAR CALIBRAÇÃO
              </button>
            </>
          )}
        </div>
      </main>

      {/* Footer de progresso */}
      <footer className="fixed bottom-0 left-0 w-full h-24 flex items-center justify-between px-margin-desktop z-50 bg-surface-container/80 backdrop-blur-2xl border-t border-outline-variant/15">
        <div className="flex items-center gap-6 flex-1">
          <div className="flex flex-col gap-1">
            <span className="font-label-caps text-on-surface-variant">Progress</span>
            <span className="font-headline-md text-headline-md text-primary">
              Stage {activeIndex + 1} of {POINTS.length}
            </span>
          </div>
          <div className="flex-1 max-w-md h-3 bg-surface-container-highest rounded-full overflow-hidden">
            <div
              className="h-full bg-secondary shadow-[0_0_10px_#00A693] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="font-label-caps text-secondary">{progress}%</span>
        </div>

        <div className="flex items-center gap-gutter ml-12">
          <button
            className="px-8 h-14 rounded-xl border border-error/30 text-error font-label-caps hover:bg-error/10 transition-all"
            onClick={() => navigate('/')}
          >
            CANCEL
          </button>
          <button
            className="px-8 h-14 rounded-xl bg-secondary-container text-on-secondary-container font-label-caps shadow-[0_0_20px_rgba(0,166,147,0.4)] hover:scale-105 transition-all"
            onClick={() => navigate('/')}
          >
            SKIP CALIBRATION
          </button>
        </div>
      </footer>

      {/* Tooltip de ajuda */}
      <div className="fixed bottom-32 right-margin-desktop z-40">
        <div className="glass-panel p-6 rounded-2xl border-secondary/30 flex items-start gap-4 max-w-xs animate-bounce shadow-2xl">
          <span className="material-symbols-outlined text-secondary">info</span>
          <p className="text-body-md text-on-surface">
            If the tracker loses your eyes, ensure you are in a well-lit environment.
          </p>
        </div>
      </div>
    </>
  )
}
