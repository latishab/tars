import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { Activity, Gamepad2, SlidersHorizontal, Grid3X3, Download, Settings } from 'lucide-react'
import Status from './pages/Status'
import Control from './pages/Control'
import MovementBuilder from './pages/MovementBuilder'
import SettingsPage from './pages/Settings'
import AppStore from './pages/AppStore'
import Expressions from './pages/Expressions'

const NAV = [
  { to: '/',           icon: Activity,          label: 'STATUS'  },
  { to: '/control',    icon: Gamepad2,           label: 'CONTROL' },
  { to: '/builder',    icon: SlidersHorizontal,  label: 'BUILD'   },
  { to: '/expressions',icon: Grid3X3,            label: 'EXPR'    },
  { to: '/apps',       icon: Download,           label: 'APPS'    },
  { to: '/settings',   icon: Settings,           label: 'SET'     },
]

function App() {
  return (
    <div style={{ minHeight: '100vh', background: 'hsl(214 35% 4%)', fontFamily: "'Share Tech Mono', monospace" }}>

      {/* Top bar */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'hsl(214 35% 3%)',
        borderBottom: '1px solid hsl(214 28% 11%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 44, padding: '0 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Corner bracket logo mark */}
            <div style={{ position: 'relative', width: 18, height: 18, flexShrink: 0 }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: 7, height: 7, borderTop: '2px solid hsl(36 100% 46%)', borderLeft: '2px solid hsl(36 100% 46%)' }} />
              <div style={{ position: 'absolute', bottom: 0, right: 0, width: 7, height: 7, borderBottom: '2px solid hsl(36 100% 46%)', borderRight: '2px solid hsl(36 100% 46%)' }} />
            </div>
            <span style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 16, letterSpacing: '0.25em', color: 'hsl(36 100% 55%)' }}>TARS</span>
            <span style={{ fontSize: 8, letterSpacing: '0.2em', color: 'hsl(214 14% 32%)', paddingTop: 1 }}>MISSION CONTROL</span>
          </div>
          {/* Live indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'hsl(141 70% 45%)', boxShadow: '0 0 5px hsl(141 70% 45%)', animation: 'tars-pulse-green 2s ease-in-out infinite' }} />
            <span style={{ fontSize: 8, letterSpacing: '0.2em', color: 'hsl(214 14% 35%)' }}>LIVE</span>
          </div>
        </div>
      </header>

      {/* Content */}
      <main style={{ paddingBottom: 64 }}>
        <Routes>
          <Route path="/"            element={<Status />} />
          <Route path="/control"     element={<Control />} />
          <Route path="/builder"     element={<MovementBuilder />} />
          <Route path="/apps"        element={<AppStore />} />
          <Route path="/expressions" element={<Expressions />} />
          <Route path="/settings"    element={<SettingsPage />} />
          <Route path="*"            element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Bottom nav */}
      <nav style={{
        position: 'fixed', bottom: 0, left: 0, right: 0,
        background: 'hsl(214 35% 3%)',
        borderTop: '1px solid hsl(214 28% 11%)',
        zIndex: 50,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', height: 56, maxWidth: 480, margin: '0 auto' }}>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              style={({ isActive }) => ({
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                padding: '6px 8px',
                textDecoration: 'none',
                color: isActive ? 'hsl(36 100% 55%)' : 'hsl(214 14% 35%)',
                borderTop: isActive ? '2px solid hsl(36 100% 46%)' : '2px solid transparent',
                marginTop: -1,
                transition: 'color 0.15s ease',
              })}
            >
              {({ isActive }) => (
                <>
                  <Icon size={16} style={{ filter: isActive ? 'drop-shadow(0 0 4px hsl(36 100% 46%))' : 'none' }} />
                  <span style={{ fontSize: 7, letterSpacing: '0.15em' }}>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}

export default App
