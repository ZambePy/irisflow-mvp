import { useState } from 'react'
import { useDwell } from '../hooks/useDwell'
import { DWELL_TIME_MS } from '../theme/lumina'
import { useNavigate } from 'react-router-dom'

const ROW1 = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P']
const ROW2 = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L']
const ROW3 = ['Z', 'X', 'C', 'V', 'B', 'N', 'M']

function KeyButton({ label, children, onPress, className = '', dwellTime = DWELL_TIME_MS }) {
  const [hovered, setHovered] = useState(false)
  const { onMouseEnter, onMouseLeave } = useDwell(() => onPress(label))

  const handleEnter = () => { setHovered(true); onMouseEnter() }
  const handleLeave = () => { setHovered(false); onMouseLeave() }

  return (
    <button
      className={`glass-key h-hit-area-min rounded-xl font-display text-headline-md relative overflow-hidden flex items-center justify-center ${className}`}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      onClick={() => onPress(label)}
    >
      {children ?? label}
      {/* Barra de progresso dwell */}
      <div
        className="absolute bottom-1 left-1/2 -translate-x-1/2 h-1 bg-secondary rounded-full"
        style={{
          width: hovered ? '80%' : '0%',
          transition: hovered ? `width ${dwellTime}ms linear` : 'none',
        }}
      />
    </button>
  )
}

export default function Keyboard() {
  const [text, setText] = useState('')
  const navigate = useNavigate()

  const handleKey = (char) => {
    if (char === 'DELETE') {
      setText((t) => t.slice(0, -1))
    } else if (char === 'SPACE') {
      setText((t) => t + ' ')
    } else if (char === 'SPEAK') {
      if (text && 'speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(text)
        u.rate = 0.9
        u.pitch = 1.1
        window.speechSynthesis.speak(u)
      }
      setText('')
    } else {
      setText((t) => t + char)
    }
  }

  return (
    <>
      <main className="ml-80 pt-hit-area-min pb-margin-desktop px-margin-desktop h-screen flex flex-col gap-gutter">
        {/* Área de texto atual */}
        <section className="mt-margin-desktop">
          <div className="glass-key rounded-xl p-6 flex flex-col gap-4 min-h-[140px]">
            <div className="flex justify-between items-center">
              <span className="font-label-caps text-label-caps text-outline uppercase">
                Current Message
              </span>
              <div className="font-display text-headline-lg text-primary tracking-wide">
                {text || 'Ready to type...'}
              </div>
              <span className="material-symbols-outlined text-outline">more_horiz</span>
            </div>
            {/* Sugestões de texto preditivo */}
            <div className="flex gap-4">
              {['Hello', 'I need', 'Water', 'Thank you'].map((s) => (
                <button
                  key={s}
                  className="glass-key px-8 py-3 rounded-full font-body-lg text-secondary border-secondary/30"
                  onClick={() => setText((t) => t + s + ' ')}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Grade do teclado */}
        <section className="flex-grow grid grid-cols-10 gap-gutter content-center">
          {/* Linha 1: Q-P */}
          {ROW1.map((k) => (
            <KeyButton key={k} label={k} onPress={handleKey} />
          ))}

          {/* Linha 2: A-L (offset de 1 coluna) */}
          <div className="col-span-1" />
          {ROW2.map((k) => (
            <KeyButton key={k} label={k} onPress={handleKey} />
          ))}

          {/* Linha 3: Z-M (offset de 2 colunas) */}
          <div className="col-span-2" />
          {ROW3.map((k) => (
            <KeyButton key={k} label={k} onPress={handleKey} />
          ))}
          <div className="col-span-1" />

          {/* Linha funcional */}
          <KeyButton
            label="DELETE"
            onPress={handleKey}
            className="col-span-2 bg-error-container/20 text-error border-error/30"
          >
            <span className="material-symbols-outlined text-[32px]">backspace</span>
          </KeyButton>

          <KeyButton
            label="SPACE"
            onPress={handleKey}
            className="col-span-5"
          >
            SPACE
          </KeyButton>

          <KeyButton
            label="SPEAK"
            onPress={handleKey}
            className="col-span-3 bg-secondary-container text-on-secondary-container border-secondary shadow-[0_0_20px_rgba(0,166,147,0.4)]"
          >
            <div className="flex items-center justify-center gap-3">
              <span className="material-symbols-outlined text-[32px]">volume_up</span>
              SPEAK
            </div>
          </KeyButton>
        </section>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 w-full p-gutter flex justify-between items-center z-50 bg-surface-container/60 backdrop-blur-2xl border-t border-outline-variant/15">
        <div className="flex gap-4">
          <button
            className="glass-key h-16 px-8 rounded-xl flex items-center gap-3"
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined text-primary">arrow_back</span>
            <span className="font-label-caps">Back</span>
          </button>
          <button
            className="glass-key h-16 px-8 rounded-xl flex items-center gap-3"
            onClick={() => navigate('/calibration')}
          >
            <span className="material-symbols-outlined text-primary">settings</span>
            <span className="font-label-caps">Calibrate</span>
          </button>
        </div>
        <p className="font-label-caps text-label-caps text-on-surface-variant">
          IrisFlow Assistive Tech v0.1
        </p>
      </footer>
    </>
  )
}
