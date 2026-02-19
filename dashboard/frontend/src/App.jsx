import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { Activity, Gamepad2, Settings, Download } from 'lucide-react'
import Status from './pages/Status'
import Control from './pages/Control'
import SettingsPage from './pages/Settings'
import AppStore from './pages/AppStore'

function App() {
  return (
    <div className="min-h-screen bg-background dark">
      {/* Main Content */}
      <main className="pb-20">
        <Routes>
          <Route path="/" element={<Status />} />
          <Route path="/control" element={<Control />} />
          <Route path="/apps" element={<AppStore />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
        <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
          <NavLink
            to="/"
            className={({ isActive }) =>
              \`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors \${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }\`
            }
          >
            <Activity className="w-5 h-5" />
            <span className="text-xs">Status</span>
          </NavLink>

          <NavLink
            to="/control"
            className={({ isActive }) =>
              \`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors \${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }\`
            }
          >
            <Gamepad2 className="w-5 h-5" />
            <span className="text-xs">Control</span>
          </NavLink>

          <NavLink
            to="/apps"
            className={({ isActive }) =>
              \`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors \${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }\`
            }
          >
            <Download className="w-5 h-5" />
            <span className="text-xs">Apps</span>
          </NavLink>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              \`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors \${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }\`
            }
          >
            <Settings className="w-5 h-5" />
            <span className="text-xs">Settings</span>
          </NavLink>
        </div>
      </nav>
    </div>
  )
}

export default App
