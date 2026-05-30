import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  .pl-dwell { position:absolute; bottom:0; left:0; height:4px; width:0%; background:#5bdac6; transition:width 0.5s linear; }
  .pl-card:hover .pl-dwell { width:100%; }
  .pl-card:hover { box-shadow: 0 0 30px rgba(91,218,198,0.3); }
`

const PHRASES_BY_CATEGORY = {
  saude: ['Preciso de ajuda médica', 'Estou com dor', 'Chame a enfermeira', 'Preciso de medicamento', 'Estou bem', 'Quero descansar'],
  necessidades: ['Estou com fome', 'Estou com sede', 'Preciso ir ao banheiro', 'Estou com frio', 'Estou com calor', 'Quero descansar'],
  social: ['Obrigado', 'Por favor', 'Com licença', 'Bom dia', 'Como vai você?', 'Até logo'],
  emocoes: ['Estou feliz', 'Estou triste', 'Estou com medo', 'Preciso de ajuda', 'Estou bem', 'Estou cansado'],
}

const CATEGORY_META = {
  saude: { label: '🏥 Saúde', emoji: '🏥' },
  necessidades: { label: '🍽️ Necessidades', emoji: '🍽️' },
  social: { label: '💬 Social', emoji: '💬' },
  emocoes: { label: '❤️ Emoções', emoji: '❤️' },
}

function PhraseCard({ text, isFavorited, onSpeak, onToggleFavorite }) {
  const { onMouseEnter, onMouseLeave } = useDwell(onSpeak)
  return (
    <div
      className="pl-card relative group flex items-center justify-between min-h-[100px] bg-surface-container hover:bg-surface-bright rounded-2xl px-10 border border-white/5 transition-all duration-300 cursor-pointer overflow-hidden"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onSpeak}
    >
      <div className="pl-dwell" />
      <div className="flex items-center gap-6 relative z-10">
        <span className="text-white font-headline-lg text-headline-lg">{text}</span>
      </div>
      <div className="flex items-center gap-6 relative z-10">
        <button
          className="p-4 rounded-full hover:bg-secondary/10 text-secondary transition-colors"
          onClick={(e) => { e.stopPropagation(); onToggleFavorite() }}
        >
          <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: isFavorited ? "'FILL' 1" : "'FILL' 0" }}>
            star
          </span>
        </button>
        <button
          className="p-4 rounded-full bg-secondary/10 text-secondary transition-all hover:scale-110 active:scale-95"
          onClick={(e) => { e.stopPropagation(); onSpeak() }}
        >
          <span className="material-symbols-outlined text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>volume_up</span>
        </button>
      </div>
    </div>
  )
}

export default function PhraseList() {
  const navigate = useNavigate()
  const { category } = useParams()
  const { sendMessage } = useGazeSocket()
  const [favorites, setFavorites] = useState(new Set())
  const [lastSpoken, setLastSpoken] = useState('')

  const phrases = PHRASES_BY_CATEGORY[category] ?? PHRASES_BY_CATEGORY.necessidades
  const meta = CATEGORY_META[category] ?? CATEGORY_META.necessidades

  const speak = (text) => {
    setLastSpoken(text)
    sendMessage('speak', { text })
  }

  const { onMouseEnter: speakLastEnter, onMouseLeave: speakLastLeave } = useDwell(() => lastSpoken && speak(lastSpoken))

  return (
    <div className="flex flex-col h-full relative bg-background">
      <style>{CSS}</style>

      <div className="flex-grow flex flex-col px-margin-desktop pt-10 pb-32 overflow-y-auto">
        <div className="flex items-end justify-between mb-8">
          <div>
            <button
              className="flex items-center gap-2 text-primary hover:text-primary-container transition-colors mb-4 group px-4 py-2 -ml-4 rounded-lg hover:bg-white/5"
              onClick={() => navigate('/phrases')}
            >
              <span className="material-symbols-outlined transition-transform group-hover:-translate-x-1">arrow_back</span>
              <span className="font-label-lg text-label-lg">Frases</span>
            </button>
            <h2 className="font-display-lg text-display-lg text-white mb-2">{meta.label}</h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant">{phrases.length} frases disponíveis</p>
          </div>
          <div className="flex gap-4">
            <span className="px-6 py-3 rounded-full bg-surface-container-highest/50 border border-white/10 font-label-lg text-label-lg text-white/60">
              Auto-Speak: ON
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 max-w-5xl">
          {phrases.map((text) => (
            <PhraseCard
              key={text}
              text={text}
              isFavorited={favorites.has(text)}
              onSpeak={() => speak(text)}
              onToggleFavorite={() => setFavorites((prev) => {
                const next = new Set(prev)
                next.has(text) ? next.delete(text) : next.add(text)
                return next
              })}
            />
          ))}
        </div>
      </div>

      <footer className="absolute bottom-0 left-0 w-full h-32 bg-surface-dim/95 backdrop-blur-2xl border-t border-white/5 flex items-center px-margin-desktop gap-gutter-desktop z-40">
        <button
          className="flex-1 h-20 bg-surface-container-high hover:bg-surface-bright text-on-surface font-eye-track-label text-eye-track-label rounded-2xl flex items-center justify-center gap-4 border border-white/5 transition-all group"
          onClick={() => navigate('/phrases')}
        >
          <span className="material-symbols-outlined transition-transform group-hover:-translate-x-2">arrow_back</span>
          VOLTAR
        </button>
        <button
          className="flex-1 h-20 bg-surface-container-high hover:bg-surface-bright text-on-surface font-eye-track-label text-eye-track-label rounded-2xl flex items-center justify-center gap-4 border border-white/5 transition-all group"
          onClick={() => navigate('/')}
        >
          <span className="material-symbols-outlined group-hover:scale-110 transition-transform">home</span>
          HOME
        </button>
        <button
          className="flex-[1.5] h-20 bg-primary-container text-on-primary-container font-eye-track-label text-eye-track-label rounded-2xl flex items-center justify-center gap-4 shadow-xl shadow-primary/10 transition-all active:scale-95 hover:brightness-110 group"
          onMouseEnter={speakLastEnter}
          onMouseLeave={speakLastLeave}
          onClick={() => lastSpoken && speak(lastSpoken)}
        >
          <span className="material-symbols-outlined group-hover:animate-pulse">play_circle</span>
          FALAR ÚLTIMA
        </button>
      </footer>

      <div className="fixed top-0 right-0 -z-10 w-[50vw] h-[512px] bg-primary/5 blur-[120px] rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none" />
      <div className="fixed bottom-0 left-0 -z-10 w-[40vw] h-[409px] bg-secondary/5 blur-[100px] rounded-full -translate-x-1/2 translate-y-1/2 pointer-events-none" />
    </div>
  )
}
