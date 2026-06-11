import { useNavigate, useLocation } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'

const CSS = `
  @keyframes or-pulse-teal {
    0% { box-shadow: 0 0 0 0 rgba(91, 218, 198, 0.4); }
    70% { box-shadow: 0 0 0 40px rgba(91, 218, 198, 0); }
    100% { box-shadow: 0 0 0 0 rgba(91, 218, 198, 0); }
  }
  .or-pulse-glow { animation: or-pulse-teal 3s infinite; }
  .or-dwell-fill::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0;
    height: 4px; width: 0%;
    background-color: #5bdac6;
    transition: width 0.5s linear;
  }
  .or-dwell-fill:hover::after { width: 100%; }
  .or-glass {
    background: rgba(30, 32, 36, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
`

export default function OnboardingReady() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const accuracy = state?.accuracy ?? 94
  const engine = state?.engine ?? 'IrisGazeNet'
  const latency = state?.latency ?? '8ms'
  const userName = state?.name ?? ''

  const dwellHome = useDwell(() => navigate('/'))

  return (
    <div className="bg-background text-on-background min-h-screen flex flex-col font-body-md">
      <style>{CSS}</style>

      {/* Header with stepper */}
      <header className="bg-surface-dim/80 backdrop-blur-xl border-b border-white/10 shadow-md flex justify-between items-center px-margin-desktop w-full h-24 fixed z-50">
        <div className="text-headline-lg font-headline-lg font-bold text-primary tracking-tight">IrisFlow</div>

        <nav className="hidden md:flex items-center gap-12">
          <div className="flex items-center gap-3 opacity-60">
            <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold">
              <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
            </div>
            <span className="font-label-lg text-label-lg text-on-surface-variant">1 Perfil</span>
          </div>
          <div className="w-12 h-px bg-white/10" />
          <div className="flex items-center gap-3 opacity-60">
            <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold">
              <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
            </div>
            <span className="font-label-lg text-label-lg text-on-surface-variant">2 Calibração</span>
          </div>
          <div className="w-12 h-px bg-white/10" />
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-secondary-container text-white flex items-center justify-center font-bold shadow-[0_0_15px_rgba(0,166,147,0.5)]">
              3
            </div>
            <span className="font-label-lg text-label-lg text-secondary font-bold">Pronto</span>
          </div>
        </nav>

        <div className="flex items-center gap-6">
          <div className="hidden lg:flex items-center gap-2 text-primary font-label-lg text-label-lg">
            <span className="material-symbols-outlined text-sm">sensors</span>
            Calibration Active
          </div>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-on-surface-variant">battery_full</span>
            <span className="material-symbols-outlined text-on-surface-variant">visibility</span>
          </div>
        </div>
      </header>

      <main className="flex-grow flex items-center justify-center px-margin-mobile md:px-margin-desktop pt-32 pb-16">
        <div className="max-w-4xl w-full flex flex-col items-center text-center">

          {/* Success ring */}
          <div className="relative mb-12">
            <div className="w-48 h-48 md:w-64 md:h-64 rounded-full bg-secondary/10 flex items-center justify-center border-2 border-secondary/30 or-pulse-glow">
              <div className="w-32 h-32 md:w-44 md:h-44 rounded-full bg-secondary-container flex items-center justify-center shadow-2xl">
                <span className="material-symbols-outlined text-white text-[80px] md:text-[110px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  check_circle
                </span>
              </div>
            </div>
            <div className="absolute -top-4 -right-4 w-12 h-12 bg-primary/20 rounded-full blur-xl" />
            <div className="absolute -bottom-6 -left-8 w-20 h-20 bg-secondary/10 rounded-full blur-2xl" />
          </div>

          <h1 className="font-display-lg text-display-lg text-primary mb-6 tracking-tighter">
            Tudo Pronto{userName ? `, ` : '!'}{userName && <span className="text-secondary">{userName}</span>}{userName ? '!' : ''}
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mb-12">
            Seu perfil foi configurado com sucesso e o sistema está pronto para uso. O algoritmo de rastreamento ocular foi sincronizado com sua anatomia única.
          </p>

          {/* Stats bento */}
          <div className="or-glass w-full max-w-2xl rounded-xl p-8 mb-16 flex flex-wrap items-center justify-around gap-8">
            <div className="flex flex-col items-center">
              <span className="font-label-lg text-label-lg text-on-surface-variant uppercase tracking-widest mb-2">Precisão</span>
              <div className="flex items-baseline gap-1">
                <span className="font-headline-lg text-headline-lg text-secondary">{accuracy}%</span>
                <span className="text-secondary/60 text-sm font-bold">(Excelente)</span>
              </div>
            </div>
            <div className="w-px h-12 bg-white/10 hidden md:block" />
            <div className="flex flex-col items-center">
              <span className="font-label-lg text-label-lg text-on-surface-variant uppercase tracking-widest mb-2">Motor</span>
              <span className="font-headline-lg text-headline-lg text-primary">{engine}</span>
            </div>
            <div className="w-px h-12 bg-white/10 hidden md:block" />
            <div className="flex flex-col items-center">
              <span className="font-label-lg text-label-lg text-on-surface-variant uppercase tracking-widest mb-2">Latência</span>
              <span className="font-headline-lg text-headline-lg text-primary">{latency}</span>
            </div>
          </div>

          {/* CTA */}
          <button
            className="or-dwell-fill group relative overflow-hidden bg-secondary text-on-secondary px-12 py-6 rounded-full font-eye-track-label text-eye-track-label flex items-center gap-4 transition-all duration-500 hover:scale-105 hover:shadow-[0_0_40px_rgba(91,218,198,0.4)]"
            {...dwellHome}
            onClick={() => navigate('/')}
          >
            ACESSAR HOME
            <span className="material-symbols-outlined group-hover:translate-x-2 transition-transform duration-300">arrow_forward</span>
          </button>
          <p className="mt-8 font-label-lg text-label-lg text-on-surface-variant/50">
            Fixe o olhar por 1 segundo para confirmar
          </p>
        </div>
      </main>

      {/* Atmospheric background */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
        <div className="absolute top-1/4 -left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 -right-1/4 w-[600px] h-[600px] bg-secondary/5 rounded-full blur-[150px]" />
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.05) 1px, transparent 0)', backgroundSize: '40px 40px' }} />
      </div>
    </div>
  )
}
