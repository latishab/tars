import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { Activity, Gamepad2, Settings, Download, Sun, Moon, SlidersHorizontal } from 'lucide-react'
import { Button } from './components/ui/button'
import Status from './pages/Status'
import Control from './pages/Control'
import MovementBuilder from './pages/MovementBuilder'
import SettingsPage from './pages/Settings'
import AppStore from './pages/AppStore'

function App() {
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    document.documentElement.classList.toggle('dark', savedTheme === 'dark')
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 bg-card border-b border-border">
        <div className="flex items-center justify-between h-14 px-4 max-w-6xl mx-auto">
          <h1 className="text-xl font-bold">TARS</h1>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="pb-20 pt-2">
        <Routes>
          <Route path="/" element={<Status />} />
          <Route path="/control" element={<Control />} />
          <Route path="/builder" element={<MovementBuilder />} />
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
            to="/builder"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <SlidersHorizontal className="w-5 h-5" />
            <span className="text-xs">Builder</span>
          </NavLink>

          <NavLink
            to="/apps"
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <Download className="w-5 h-5" />
            <span className="text-xs">Apps</span>
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
