import { NavLink, useNavigate } from 'react-router-dom'
import { useDwell } from '../hooks/useDwell'
import { useGazeSocket } from '../context/GazeSocketContext'

const links = [
  { to: '/',            icon: 'home',     label: 'Home',     end: true },
  { to: '/favorites',   icon: 'star',     label: 'Favorites'          },
  { to: '/settings',    icon: 'settings', label: 'Settings'           },
  { to: '/profile-setup', icon: 'person', label: 'Profile'            },
]

export default function SideNav() {
  const navigate = useNavigate()
  const { connected, sendMessage } = useGazeSocket()
  const handleEmergency = () => sendMessage('emergency')
  const { onMouseEnter, onMouseLeave } = useDwell(handleEmergency)

  return (
    <aside className="h-full w-80 shrink-0 bg-surface-container/90 backdrop-blur-2xl border-r border-white/5 flex flex-col py-8 z-50">
      {/* Logo */}
      <div className="px-8 mb-12">
        <div className="w-16 h-16 rounded-2xl bg-primary-container flex items-center justify-center mb-4">
          <span
            className="material-symbols-outlined text-primary text-3xl"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            fluid_med
          </span>
        </div>
        <h1 className="font-headline-md text-headline-md text-primary">IrisFlow Control</h1>
        <p className="font-label-lg text-label-lg text-on-surface-variant">Eye-Track Ready</p>
      </div>

      {/* Nav */}
      <nav className="flex-grow">
        {links.map(({ to, icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            data-dwell-target={label === 'Favorites' || label === 'Settings' ? true : undefined}
            data-dwell-label={label}
            className={({ isActive }) =>
              isActive
                ? 'flex items-center text-secondary border-l-4 border-secondary bg-secondary/10 px-8 py-6 transition-all duration-300'
                : 'flex items-center text-on-surface-variant px-8 py-6 transition-all duration-300 hover:bg-surface-bright'
            }
          >
            <span className="material-symbols-outlined mr-4 text-3xl">{icon}</span>
            <span className="font-eye-track-label text-eye-track-label">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom: Emergency + Help */}
      <div className="px-8 mt-auto">
        <button
          data-dwell-target
          data-dwell-label="Emergency"
          className="pulse-emergency w-full bg-error-container text-error px-6 py-5 rounded-xl font-bold hover:scale-95 transition-transform flex items-center justify-center gap-3"
          onMouseEnter={connected ? undefined : onMouseEnter}
          onMouseLeave={onMouseLeave}
          onClick={handleEmergency}
        >
          <span className="material-symbols-outlined">emergency_home</span>
          EMERGENCY
        </button>

        <button
          data-dwell-target
          data-dwell-label="Calibration"
          className="mt-6 flex items-center text-on-surface-variant hover:text-primary transition-colors w-full py-4"
          onClick={() => navigate('/calibration')}
        >
          <span className="material-symbols-outlined mr-3">adjust</span>
          <span className="font-label-lg text-label-lg">Calibrar</span>
        </button>
      </div>
    </aside>
  )
}
