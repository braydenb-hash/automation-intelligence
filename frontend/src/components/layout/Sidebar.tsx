import { NavLink } from 'react-router-dom'
import { HomeIcon, WorkflowsIcon, ToolsIcon, SavedIcon } from './NavIcons'

const navItems = [
  { to: '/', label: 'Home', Icon: HomeIcon },
  { to: '/workflows', label: 'Workflows', Icon: WorkflowsIcon },
  { to: '/tools', label: 'Tools', Icon: ToolsIcon },
  { to: '/saved', label: 'Saved', Icon: SavedIcon },
]

export default function Sidebar() {
  return (
    <aside className="fixed top-0 left-0 z-40 flex h-screen w-52 flex-col border-r border-border bg-surface">
      <div className="px-5 py-6">
        <h1 className="font-serif text-2xl font-semibold tracking-tight text-cream">
          Autumn
        </h1>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-2">
        {navItems.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-ember/10 text-ember'
                  : 'text-cream-dim hover:bg-surface-light hover:text-cream'
              }`
            }
          >
            <Icon />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
