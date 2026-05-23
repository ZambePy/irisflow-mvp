import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', icon: 'home', label: 'Home', end: true },
  { to: '/phrases', icon: 'chat_bubble', label: 'Phrases' },
  { to: '/keyboard', icon: 'keyboard', label: 'Keyboard' },
  { to: '/calibration', icon: 'center_focus_weak', label: 'Calibration' },
  { to: '/settings', icon: 'settings', label: 'Settings' },
]

const activeClass =
  'flex items-center gap-4 p-4 bg-secondary-container text-on-secondary-container rounded-xl border-2 border-secondary shadow-[0_0_15px_rgba(0,166,147,0.4)] transition-all'

const inactiveClass =
  'flex items-center gap-4 p-4 text-on-surface-variant opacity-70 hover:bg-surface-variant/30 hover:backdrop-blur-md transition-all rounded-xl'

export default function SideNav() {
  return (
    <nav className="fixed left-0 top-0 h-full w-80 flex flex-col py-margin-desktop bg-surface-container-lowest/40 backdrop-blur-2xl border-r border-outline-variant/15 z-40">
      {/* Logo e perfil */}
      <div className="px-8 mt-20 mb-12">
        <div className="w-20 h-20 rounded-2xl bg-primary-container flex items-center justify-center mb-4">
          <span
            className="material-symbols-outlined text-primary text-4xl"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            fluid_med
          </span>
        </div>
        <h2 className="font-headline-md text-headline-md text-on-surface">IrisFlow</h2>
        <p className="font-body-md text-on-surface-variant">Assistive Interface</p>
      </div>

      {/* Links de navegação */}
      <div className="flex-1 flex flex-col gap-4 px-4">
        {links.map(({ to, icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
          >
            <span className="material-symbols-outlined">{icon}</span>
            <span className="font-label-caps text-label-caps">{label}</span>
          </NavLink>
        ))}
      </div>

      {/* Botão de ajuda e emergência rápida */}
      <div className="px-4 mt-auto flex flex-col gap-4">
        <NavLink
          to="/help"
          className={({ isActive }) => (isActive ? activeClass : inactiveClass)}
        >
          <span className="material-symbols-outlined">help</span>
          <span className="font-label-caps text-label-caps">Help</span>
        </NavLink>

        <button className="w-full h-24 bg-error-container text-on-error-container border-2 border-error/50 rounded-2xl flex flex-col items-center justify-center emergency-pulse transition-all active:scale-95">
          <span className="material-symbols-outlined text-3xl">emergency_home</span>
          <span className="font-label-caps mt-1">EMERGENCY</span>
        </button>
      </div>
    </nav>
  )
}
