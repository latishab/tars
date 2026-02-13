import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Activity, Gamepad2, MessageSquare, Settings, Wifi } from 'lucide-react'
import Status from './pages/Status'
import Control from './pages/Control'
import Chat from './pages/Chat'
import SettingsPage from './pages/Settings'
import Setup from './pages/Setup'

function App() {
  const [needsSetup, setNeedsSetup] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if WiFi setup is needed
    fetch('/api/wifi/status')
      .then(res => res.json())
      .then(data => {
        setNeedsSetup(data.hotspot_active && !data.connected)
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  // Show setup wizard if hotspot is active
  if (needsSetup) {
    return <Setup onComplete={() => setNeedsSetup(false)} />
  }

  return (
    <div className="min-h-screen bg-background dark">
      {/* Main Content */}
      <main className="pb-20">
        <Routes>
          <Route path="/" element={<Status />} />
          <Route path="/control" element={<Control />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/setup" element={<Setup onComplete={() => setNeedsSetup(false)} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border">
        <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <Activity className="w-5 h-5" />
            <span className="text-xs">Status</span>
          </NavLink>

          <NavLink
            to="/control"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <Gamepad2 className="w-5 h-5" />
            <span className="text-xs">Control</span>
          </NavLink>

          <NavLink
            to="/chat"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <MessageSquare className="w-5 h-5" />
            <span className="text-xs">Chat</span>
          </NavLink>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }`
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
