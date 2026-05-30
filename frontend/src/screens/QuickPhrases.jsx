import { useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  .qp-glass { background: rgba(30,32,36,0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }
  .qp-dwell-bar { position:absolute; bottom:0; left:0; height:4px; background:#5bdac6; width:0%; transition:width 0.5s linear; }
  .qp-card:hover .qp-dwell-bar { width:100%; }
  .qp-card:hover { box-shadow: 0 0 30px rgba(91,218,198,0.2); }
`

const CATEGORIES = [
  { id: 'saude', label: 'Saúde', icon: 'medical_services', count: 12 },
  { id: 'necessidades', label: 'Necessidades', icon: 'restaurant', count: 8 },
  { id: 'social', label: 'Social', icon: 'forum', count: 15 },
  { id: 'emocoes', label: 'Emoções', icon: 'favorite', count: 10 },
]

function CategoryCard({ cat, onClick }) {
  const { onMouseEnter, onMouseLeave } = useDwell(onClick)
  return (
    <div
      className="qp-glass qp-card group relative min-h-[260px] rounded-2xl flex flex-col items-center justify-center cursor-pointer p-8 transition-all duration-500 hover:border-secondary hover:scale-[1.02] overflow-hidden border border-white/5"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
    >
      <div className="qp-dwell-bar" />
      <div className="w-24 h-24 rounded-full bg-secondary/10 flex items-center justify-center mb-6 group-hover:bg-secondary/20 transition-colors">
        <span className="material-symbols-outlined text-secondary text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>
          {cat.icon}
        </span>
      </div>
      <h2 className="text-headline-lg font-headline-lg text-on-surface group-hover:text-secondary transition-colors">{cat.label}</h2>
      <p className="text-on-surface-variant font-body-lg">{cat.count} frases</p>
    </div>
  )
}

export default function QuickPhrases() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-full">
      <style>{CSS}</style>

      <div className="flex-1 p-margin-desktop overflow-y-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter-desktop">
          {CATEGORIES.map((cat) => (
            <CategoryCard
              key={cat.id}
              cat={cat}
              onClick={() => navigate(`/phrases/${cat.id}`)}
            />
          ))}
        </div>
      </div>

      <footer className="h-32 bg-surface-container-low/60 backdrop-blur-xl border-t border-white/5 flex items-center px-margin-desktop gap-gutter-desktop shrink-0">
        <button
          className="relative group min-w-[280px] h-20 bg-surface-container-highest rounded-2xl flex items-center px-8 gap-4 hover:bg-surface-bright transition-all overflow-hidden border border-white/5"
          onClick={() => navigate('/')}
        >
          <span className="material-symbols-outlined text-primary">arrow_back</span>
          <span className="font-eye-track-label text-eye-track-label text-on-surface">Voltar para Home</span>
        </button>
        <div className="flex-1 relative group h-20">
          <span className="absolute left-6 top-1/2 -translate-y-1/2 material-symbols-outlined text-on-surface-variant text-3xl">search</span>
          <input
            className="w-full h-full bg-surface-container/50 border-2 border-white/5 rounded-2xl pl-16 pr-8 text-headline-md font-body-lg text-on-surface focus:outline-none focus:border-secondary/50 transition-all placeholder:text-on-surface-variant/40"
            placeholder="Buscar frase..."
            type="text"
          />
        </div>
      </footer>
    </div>
  )
}
