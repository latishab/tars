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
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 max-w-screen-2xl items-center">
          <div className="mr-4 flex">
            <span className="font-bold text-xl bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
              TARS
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pb-20 pt-2">
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
      <nav className="fixed bottom-0 left-0 right-0 bg-card/95 backdrop-blur border-t border-border/40 supports-[backdrop-filter]:bg-card/80">
        <div className="flex justify-around items-center h-16 max-w-lg mx-auto px-4">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`
            }
          >
            <Activity className="w-5 h-5" />
            <span className="text-xs font-medium">Status</span>
          </NavLink>

          <NavLink
            to="/control"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`
            }
          >
            <Gamepad2 className="w-5 h-5" />
            <span className="text-xs font-medium">Control</span>
          </NavLink>

          <NavLink
            to="/chat"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`
            }
          >
            <MessageSquare className="w-5 h-5" />
            <span className="text-xs font-medium">Chat</span>
          </NavLink>

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`
            }
          >
            <Settings className="w-5 h-5" />
            <span className="text-xs font-medium">Settings</span>
          </NavLink>
        </div>
      </nav>
    </div>
  )
}

export default App
