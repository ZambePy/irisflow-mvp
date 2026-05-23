import { useNavigate } from 'react-router-dom'
import GazeButton from '../components/GazeButton'
import GlassPanel from '../components/GlassPanel'
import { useAppStore } from '../store/appStore'

export default function Dashboard() {
  const navigate = useNavigate()
  const { activeMessage } = useAppStore()

  return (
    <>
      {/* Conteúdo principal — offset para sidebar (w-80) e topbar (h-20) */}
      <main className="ml-80 pt-24 pb-32 px-margin-desktop min-h-screen grid grid-cols-12 gap-gutter">

        {/* Mensagem ativa */}
        <section className="col-span-12 glass-panel rounded-3xl p-8 mb-4 flex items-center justify-between border-l-4 border-l-primary shadow-2xl">
          <div>
            <span className="font-label-caps text-label-caps text-primary mb-2 block">
              ACTIVE MESSAGE
            </span>
            <h1 className="font-display text-display text-on-surface opacity-40">
              {activeMessage || 'Gaze to start typing...'}
            </h1>
          </div>
          <button className="w-hit-area-min h-hit-area-min rounded-full bg-surface-container-high flex items-center justify-center hover:bg-primary/20 transition-colors">
            <span className="material-symbols-outlined text-primary text-3xl">volume_up</span>
          </button>
        </section>

        {/* Bento grid 2×2 */}
        <div className="col-span-12 grid grid-cols-2 grid-rows-2 gap-gutter h-[614px]">

          {/* YES / NO */}
          <div className="grid grid-cols-2 gap-gutter">
            <GazeButton
              className="rounded-[2rem] flex flex-col items-center justify-center gap-4 group"
              onActivate={() => console.log('YES')}
            >
              <div className="w-24 h-24 rounded-full bg-secondary-container/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span
                  className="material-symbols-outlined text-secondary text-5xl"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  check_circle
                </span>
              </div>
              <span className="font-headline-lg text-headline-lg">YES</span>
            </GazeButton>

            <GazeButton
              className="rounded-[2rem] flex flex-col items-center justify-center gap-4 group"
              onActivate={() => console.log('NO')}
            >
              <div className="w-24 h-24 rounded-full bg-error-container/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <span
                  className="material-symbols-outlined text-error text-5xl"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  cancel
                </span>
              </div>
              <span className="font-headline-lg text-headline-lg">NO</span>
            </GazeButton>
          </div>

          {/* Frases rápidas */}
          <GazeButton
            className="rounded-[2rem] p-8 flex flex-col items-start justify-end gap-2 relative overflow-hidden group"
            onActivate={() => navigate('/phrases')}
          >
            <div className="absolute top-8 right-8 w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-4xl">forum</span>
            </div>
            <div className="space-y-1">
              <span className="font-label-caps text-label-caps text-on-surface-variant">
                CATEGORIES
              </span>
              <h3 className="font-headline-lg text-headline-lg">Phrases</h3>
            </div>
            <div className="flex gap-2 mt-4">
              <span className="px-4 py-2 rounded-full bg-surface-variant/50 text-label-caps text-xs">NEEDS</span>
              <span className="px-4 py-2 rounded-full bg-surface-variant/50 text-label-caps text-xs">EMOTIONS</span>
              <span className="px-4 py-2 rounded-full bg-surface-variant/50 text-label-caps text-xs">SOCIAL</span>
            </div>
          </GazeButton>

          {/* Teclado */}
          <GazeButton
            className="rounded-[2rem] p-8 flex flex-col items-start justify-end gap-2 relative overflow-hidden group"
            onActivate={() => navigate('/keyboard')}
          >
            <div className="absolute top-8 right-8 w-20 h-20 bg-secondary/10 rounded-2xl flex items-center justify-center">
              <span className="material-symbols-outlined text-secondary text-4xl">keyboard</span>
            </div>
            <div>
              <span className="font-label-caps text-label-caps text-on-surface-variant">FREE TEXT</span>
              <h3 className="font-headline-lg text-headline-lg">Keyboard</h3>
            </div>
          </GazeButton>

          {/* Calibração + History/Profile */}
          <div className="grid grid-rows-2 gap-gutter">
            <GazeButton
              className="rounded-[2rem] px-8 flex items-center gap-6"
              onActivate={() => navigate('/calibration')}
            >
              <div className="w-16 h-16 bg-surface-bright rounded-xl flex items-center justify-center">
                <span className="material-symbols-outlined text-on-surface-variant">
                  center_focus_weak
                </span>
              </div>
              <div className="text-left">
                <h4 className="font-headline-md text-headline-md leading-tight">Calibration</h4>
                <span className="font-body-md text-on-surface-variant">Check accuracy</span>
              </div>
            </GazeButton>

            <div className="grid grid-cols-2 gap-gutter">
              <GazeButton
                className="rounded-[2rem] flex flex-col items-center justify-center"
                onActivate={() => console.log('History')}
              >
                <span className="material-symbols-outlined text-on-surface-variant mb-2">history</span>
                <span className="font-label-caps text-label-caps">History</span>
              </GazeButton>

              <GazeButton
                className="rounded-[2rem] flex flex-col items-center justify-center"
                onActivate={() => console.log('Profile')}
              >
                <span className="material-symbols-outlined text-on-surface-variant mb-2">person</span>
                <span className="font-label-caps text-label-caps">Profile</span>
              </GazeButton>
            </div>
          </div>
        </div>
      </main>

      {/* Footer com informações — pointer-events-none para não bloquear o EmergencyButton global */}
      <footer className="fixed bottom-0 left-0 w-full p-gutter flex justify-start items-end z-50 pointer-events-none">
        <div className="ml-80 glass-panel rounded-full px-8 py-4 flex items-center gap-6 border-t border-primary/20 pointer-events-auto">
          <span className="font-label-caps text-label-caps text-primary">
            IRISFLOW ASSISTIVE TECHNOLOGY
          </span>
          <div className="flex gap-4">
            <a className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary" href="#">
              SAFETY
            </a>
            <a className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary" href="#">
              PRIVACY
            </a>
          </div>
        </div>
      </footer>
    </>
  )
}
