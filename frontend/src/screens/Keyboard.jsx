import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  .kb-key {
    position: relative;
    aspect-ratio: 1;
    background: rgba(30,32,36,0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
    cursor: pointer;
  }
  .kb-key:hover {
    border-color: #5bdac6;
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(91,218,198,0.3);
  }
  .kb-key .kb-label {
    font-family: 'Montserrat', sans-serif;
    font-weight: 700;
    font-size: 22px;
    color: #e2e2e8;
    position: relative;
    z-index: 10;
  }
  .kb-ring-svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
  .kb-ring-bg { fill: none; stroke: rgba(255,255,255,0.05); stroke-width: 4; }
  .kb-ring-arc {
    fill: none; stroke: #5bdac6; stroke-width: 4; stroke-linecap: round;
    stroke-dasharray: 251.2; stroke-dashoffset: 251.2;
    transform: rotate(-90deg); transform-origin: 50% 50%;
    transition: stroke-dashoffset 800ms linear;
  }
  .kb-key:hover .kb-ring-arc { stroke-dashoffset: 0; }
  .kb-glass {
    background: rgba(30,32,36,0.6);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.1);
  }
  @keyframes kb-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
  .kb-cursor { animation: kb-blink 1s step-end infinite; }
`

const ROW1 = ['Q','W','E','R','T','Y','U','I','O','P']
const ROW2 = ['A','S','D','F','G','H','J','K','L']
const ROW3 = ['Z','X','C','V','B','N','M','Ç']
const PREDICTIONS = ['Obrigado', 'Por favor', 'Quero', 'Sim']

function Key({ label, onPress }) {
  const { onMouseEnter, onMouseLeave } = useDwell(() => onPress(label))
  return (
    <button className="kb-key group" onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} onClick={() => onPress(label)}>
      <span className="kb-label">{label}</span>
      <svg className="kb-ring-svg" viewBox="0 0 100 100">
        <circle className="kb-ring-bg" cx="50" cy="50" r="40" />
        <circle className="kb-ring-arc" cx="50" cy="50" r="40" />
      </svg>
    </button>
  )
}

export default function Keyboard() {
  const navigate = useNavigate()
  const { sendMessage } = useGazeSocket()
  const [text, setText] = useState('')

  const addChar = (c) => setText((t) => t + c)
  const backspace = () => setText((t) => t.slice(0, -1))
  const clear = () => setText('')
  const speak = () => {
    if (text.trim()) {
      sendMessage('speak', { text: text.trim() })
      setText('')
    }
  }

  const addWord = (word) => setText((t) => (t.length > 0 && !t.endsWith(' ') ? t + ' ' : t) + word + ' ')

  const { onMouseEnter: speakEnter, onMouseLeave: speakLeave } = useDwell(speak)

  return (
    <div className="flex flex-col h-full">
      <style>{CSS}</style>

      <section className="flex-1 p-margin-desktop flex flex-col gap-6 overflow-y-auto">
        {/* Output display */}
        <div className="kb-glass w-full h-[120px] rounded-2xl flex items-center px-8 relative group">
          <div className="flex-1 overflow-hidden">
            <p className="text-[40px] font-bold text-secondary truncate">
              {text || <span className="opacity-30">Digite sua mensagem...</span>}
            </p>
          </div>
          <div className="w-1 h-10 bg-secondary kb-cursor ml-2 rounded-full" />
        </div>

        {/* Predictive text */}
        <div className="flex gap-4">
          {PREDICTIONS.map((word) => (
            <div
              key={word}
              className="flex-1 h-20 kb-glass rounded-xl flex items-center justify-center cursor-pointer hover:bg-secondary/10 hover:border-secondary transition-all group relative overflow-hidden"
              onClick={() => addWord(word)}
            >
              <span className="text-on-surface font-eye-track-label text-eye-track-label group-hover:text-secondary">{word}</span>
              <div className="absolute inset-0 bg-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          ))}
        </div>

        {/* Keyboard grid */}
        <div className="grid grid-cols-10 gap-3">
          {ROW1.map((k) => <Key key={k} label={k} onPress={addChar} />)}
          <div className="col-span-1" />
          {ROW2.map((k) => <Key key={k} label={k} onPress={addChar} />)}
          <div className="col-span-2" />
          {ROW3.map((k) => <Key key={k} label={k} onPress={addChar} />)}
        </div>

        {/* Special keys */}
        <div className="flex gap-4">
          <button
            className="flex-[6] h-24 kb-glass rounded-2xl flex items-center justify-center hover:bg-surface-bright transition-all group relative"
            onClick={() => addChar(' ')}
          >
            <span className="text-on-surface-variant font-bold text-headline-md opacity-40">SPACE</span>
            <div className="absolute inset-0 border-2 border-transparent group-hover:border-secondary/30 rounded-2xl transition-all" />
          </button>
          <button
            className="flex-[2] h-24 kb-glass rounded-2xl flex items-center justify-center hover:bg-error-container/20 group transition-all"
            onClick={backspace}
          >
            <span className="material-symbols-outlined text-[40px] text-error group-hover:scale-110 transition-transform">backspace</span>
          </button>
        </div>
      </section>

      {/* Footer actions */}
      <footer className="h-32 p-6 kb-glass border-t border-white/5 flex gap-6 shrink-0">
        <button
          className="flex-1 bg-secondary text-on-secondary font-bold text-headline-md rounded-2xl flex items-center justify-center gap-4 hover:brightness-110 active:scale-95 transition-all shadow-lg hover:shadow-[0_0_20px_rgba(91,218,198,0.3)]"
          onMouseEnter={speakEnter}
          onMouseLeave={speakLeave}
          onClick={speak}
        >
          <span className="material-symbols-outlined text-[32px]">volume_up</span>
          FALAR
        </button>
        <button
          className="w-48 bg-surface-container-high border border-white/10 text-on-surface font-bold text-headline-md rounded-2xl hover:bg-surface-bright transition-all active:scale-95"
          onClick={clear}
        >
          LIMPAR
        </button>
        <button
          className="w-48 bg-primary-container text-primary font-bold text-headline-md rounded-2xl hover:brightness-110 transition-all active:scale-95 flex items-center justify-center gap-2 hover:shadow-[0_0_20px_rgba(160,202,252,0.4)]"
          onClick={() => navigate('/')}
        >
          <span className="material-symbols-outlined">home</span>
          HOME
        </button>
      </footer>
    </div>
  )
}
