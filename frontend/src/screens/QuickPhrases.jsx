import { useState } from 'react'
import { useDwell } from '../hooks/useDwell'
import { DWELL_TIME_MS } from '../theme/lumina'

const PHRASES = [
  { icon: 'sos', color: 'text-secondary', label: 'Urgent', text: 'I need help', fill: true },
  { icon: 'personal_injury', color: 'text-error', label: 'Medical', text: 'I am in pain', fill: false },
  { icon: 'contact_emergency', color: 'text-primary', label: 'Call', text: 'Call caregiver', fill: false },
  { icon: 'water_full', color: 'text-secondary', label: 'Needs', text: 'I need water', fill: false },
  { icon: 'airline_seat_recline_extra', color: 'text-on-surface-variant', label: 'Adjust', text: 'Uncomfortable', fill: false },
  { icon: 'favorite', color: 'text-primary', label: 'Social', text: 'Thank you', fill: false },
]

function PhraseCard({ phrase, onSelect }) {
  const [hovered, setHovered] = useState(false)
  const { onMouseEnter, onMouseLeave } = useDwell(() => onSelect(phrase.text))

  const handleEnter = () => { setHovered(true); onMouseEnter() }
  const handleLeave = () => { setHovered(false); onMouseLeave() }

  return (
    <button
      className="phrase-card relative overflow-hidden h-[240px] flex flex-col items-start justify-end p-8 glass-card rounded-3xl group transition-all duration-300 hover:ring-4 hover:ring-secondary/50 hover:bg-surface-container-high/40"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      <span
        className={`material-symbols-outlined ${phrase.color} text-5xl mb-auto group-hover:scale-110 transition-transform`}
        style={phrase.fill ? { fontVariationSettings: "'FILL' 1" } : undefined}
      >
        {phrase.icon}
      </span>
      <div className="text-left">
        <span className={`block font-label-caps ${phrase.color} text-xs mb-1 uppercase opacity-60`}>
          {phrase.label}
        </span>
        <h3 className="font-display text-headline-lg text-on-surface">{phrase.text}</h3>
      </div>

      {/* Barra de progresso dwell */}
      <div
        className="absolute bottom-0 left-0 h-1 bg-secondary"
        style={{
          width: hovered ? '100%' : '0%',
          transition: hovered ? `width ${DWELL_TIME_MS}ms linear` : 'none',
        }}
      />
    </button>
  )
}

export default function QuickPhrases() {
  const [lastPhrase, setLastPhrase] = useState('')

  const handleSelect = (text) => {
    setLastPhrase(text)
    console.log('[IrisFlow] Frase selecionada:', text)
    // TODO: integrar com TTS via WebSocket
  }

  return (
    <>
      <main className="ml-80 pt-20 overflow-y-auto bg-surface-dim p-margin-desktop min-h-screen pb-32">
        {/* Cabeçalho da tela */}
        <div className="mb-12">
          <h1 className="font-display text-display text-on-surface mb-2">Quick Phrases</h1>
          <p className="font-body-lg text-on-surface-variant">
            Focus your gaze to select a message.
          </p>
          {lastPhrase && (
            <div className="mt-4 px-6 py-3 rounded-full bg-secondary/10 border border-secondary/20 inline-flex items-center gap-3">
              <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
              <span className="font-label-caps text-label-caps text-secondary">{lastPhrase}</span>
            </div>
          )}
        </div>

        {/* Grid bento de frases */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
          {PHRASES.map((phrase) => (
            <PhraseCard key={phrase.text} phrase={phrase} onSelect={handleSelect} />
          ))}
        </div>

        {/* Decoração de fundo */}
        <div className="fixed bottom-0 right-0 p-12 opacity-10 pointer-events-none">
          <span
            className="material-symbols-outlined text-[300px]"
            style={{ fontVariationSettings: "'wght' 100" }}
          >
            neurology
          </span>
        </div>
      </main>

      {/* Footer de segurança */}
      <footer className="fixed bottom-0 left-0 w-full p-gutter flex justify-between items-center z-50 bg-error-container/20 backdrop-blur-2xl border-t border-error/30 rounded-t-xl shadow-[0_-4px_20px_rgba(147,0,10,0.2)]">
        <div className="flex items-center gap-unit">
          <span className="font-label-caps text-error text-xs uppercase font-bold">
            IrisFlow Assistive Technology
          </span>
        </div>
        <div className="flex gap-margin-desktop">
          <button className="font-label-caps text-on-error-container hover:bg-error hover:text-on-error px-4 py-2 rounded-lg transition-all">
            Safety
          </button>
          <button className="font-label-caps text-on-error-container hover:bg-error hover:text-on-error px-4 py-2 rounded-lg transition-all">
            Calibration
          </button>
          <button className="font-label-caps text-on-error-container hover:bg-error hover:text-on-error px-4 py-2 rounded-lg transition-all">
            Privacy
          </button>
        </div>
      </footer>
    </>
  )
}
