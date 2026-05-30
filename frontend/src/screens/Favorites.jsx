import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGazeSocket } from '../context/GazeSocketContext'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  .fav-dwell { position:absolute; top:0; left:0; height:100%; width:0%; background:rgba(91,218,198,0.1); transition:width 1.5s linear; pointer-events:none; }
  .fav-item:hover .fav-dwell { width:100%; }
  .fav-item:hover { box-shadow: 0 0 20px 5px rgba(91,218,198,0.2); border-color: #5bdac6; transform: translateX(8px); }
`

const INITIAL_FAVORITES = [
  { id: 1, text: 'Estou com sede', category: 'Necessidades', categoryColor: 'bg-primary-container text-primary' },
  { id: 2, text: 'Preciso de ajuda', category: 'Emoções', categoryColor: 'bg-tertiary-container/20 text-tertiary' },
  { id: 3, text: 'Obrigado', category: 'Social', categoryColor: 'bg-secondary-container/20 text-secondary' },
  { id: 4, text: 'Chame o médico', category: 'Saúde', categoryColor: 'bg-error-container/20 text-error' },
  { id: 5, text: 'Estou bem', category: 'Emoções', categoryColor: 'bg-tertiary-container/20 text-tertiary' },
]

function FavoriteItem({ item, onSpeak, onRemove }) {
  const { onMouseEnter, onMouseLeave } = useDwell(onSpeak)
  return (
    <div
      className="fav-item relative flex items-center justify-between p-6 bg-surface-container-low border border-white/5 rounded-2xl min-h-[100px] transition-all duration-300 cursor-pointer overflow-hidden"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onSpeak}
    >
      <div className="fav-dwell" />
      <div className="flex items-center gap-8 relative z-10">
        <span className={`px-6 py-2 rounded-full font-bold text-label-lg uppercase tracking-wider ${item.categoryColor}`}>
          {item.category}
        </span>
        <span className="font-headline-md text-headline-md text-on-surface">{item.text}</span>
      </div>
      <div className="flex items-center gap-6 relative z-10">
        <button
          className="w-16 h-16 rounded-full bg-surface-bright flex items-center justify-center hover:bg-secondary/20 hover:text-secondary transition-all active:scale-90"
          onClick={(e) => { e.stopPropagation(); onSpeak() }}
        >
          <span className="material-symbols-outlined text-3xl">volume_up</span>
        </button>
        <button
          className="w-16 h-16 rounded-full bg-surface-bright flex items-center justify-center hover:bg-error/20 hover:text-error transition-all active:scale-90"
          onClick={(e) => { e.stopPropagation(); onRemove() }}
        >
          <span className="material-symbols-outlined text-secondary text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
        </button>
      </div>
    </div>
  )
}

export default function Favorites() {
  const navigate = useNavigate()
  const { sendMessage } = useGazeSocket()
  const [items, setItems] = useState(INITIAL_FAVORITES)
  const [lastSpoken, setLastSpoken] = useState('')

  const speak = (text) => {
    setLastSpoken(text)
    sendMessage('speak', { text })
  }

  const remove = (id) => setItems((prev) => prev.filter((i) => i.id !== id))

  const { onMouseEnter: speakLastEnter, onMouseLeave: speakLastLeave } = useDwell(() => lastSpoken && speak(lastSpoken))

  return (
    <div className="flex flex-col h-full relative">
      <style>{CSS}</style>

      <main className="flex-grow overflow-y-auto p-margin-desktop pb-48">
        <div className="flex justify-between items-end mb-12">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="material-symbols-outlined text-secondary text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
              <h2 className="font-headline-lg text-headline-lg text-on-background">Favoritas</h2>
            </div>
            <p className="text-on-surface-variant text-body-lg font-body-lg">{items.length} frases salvas para acesso rápido</p>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-on-surface-variant gap-4">
            <span className="material-symbols-outlined text-6xl opacity-30">star_border</span>
            <p className="font-body-lg">Nenhuma frase favoritada ainda</p>
          </div>
        ) : (
          <div className="space-y-6">
            {items.map((item) => (
              <FavoriteItem
                key={item.id}
                item={item}
                onSpeak={() => speak(item.text)}
                onRemove={() => remove(item.id)}
              />
            ))}
          </div>
        )}
      </main>

      <footer className="absolute bottom-0 left-0 w-full p-gutter-desktop grid grid-cols-2 gap-gutter-desktop bg-gradient-to-t from-background to-transparent pointer-events-none">
        <div
          className="pointer-events-auto relative overflow-hidden h-[100px] bg-primary-container text-primary-fixed font-bold text-eye-track-label rounded-3xl flex items-center justify-center shadow-2xl transition-transform hover:scale-[1.02] active:scale-95 cursor-pointer border border-primary/20"
          onMouseEnter={speakLastEnter}
          onMouseLeave={speakLastLeave}
          onClick={() => lastSpoken && speak(lastSpoken)}
        >
          <div className="relative z-10 flex items-center gap-4">
            <span className="material-symbols-outlined text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
            FALAR ÚLTIMA
          </div>
        </div>
        <div
          className="pointer-events-auto relative overflow-hidden h-[100px] bg-surface-container-highest text-on-surface font-bold text-eye-track-label rounded-3xl flex items-center justify-center shadow-2xl transition-transform hover:scale-[1.02] active:scale-95 cursor-pointer border border-white/10"
          onClick={() => navigate('/')}
        >
          <div className="relative z-10 flex items-center gap-4">
            <span className="material-symbols-outlined text-4xl">home</span>
            HOME
          </div>
        </div>
      </footer>
    </div>
  )
}
