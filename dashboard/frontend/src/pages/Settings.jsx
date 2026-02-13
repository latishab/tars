import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Download, RefreshCw, Wifi, AlertCircle, CheckCircle } from 'lucide-react'

function SettingsPage() {
  const [version, setVersion] = useState(null)
  const [update, setUpdate] = useState(null)
  const [wifiStatus, setWifiStatus] = useState(null)
  const [checking, setChecking] = useState(false)
  const [installing, setInstalling] = useState(false)

  useEffect(() => {
    // Get current version
    fetch('/api/updates/current')
      .then(res => res.json())
      .then(setVersion)
      .catch(console.error)

    // Get WiFi status
    fetch('/api/wifi/status')
      .then(res => res.json())
      .then(setWifiStatus)
      .catch(console.error)
  }, [])

  const checkForUpdates = async () => {
    setChecking(true)
    try {
      const res = await fetch('/api/updates/check')
      const data = await res.json()
      setUpdate(data)
    } catch (err) {
      console.error('Update check failed:', err)
    }
    setChecking(false)
  }

  const installUpdate = async () => {
    setInstalling(true)
    try {
      const res = await fetch('/api/updates/install', { method: 'POST' })
      const data = await res.json()
      if (data.requires_restart) {
        alert('Update installed. System will restart.')
      }
    } catch (err) {
      console.error('Update install failed:', err)
      alert('Update failed. Check logs for details.')
    }
    setInstalling(false)
  }

  const restartService = async () => {
    if (!confirm('Restart TARS service?')) return
    try {
      await fetch('/api/updates/restart', { method: 'POST' })
      alert('Service restarting...')
    } catch (err) {
      console.error('Restart failed:', err)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold text-foreground">Settings</h1>

      {/* Version & Updates */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Download className="w-5 h-5" />
            System Updates
          </CardTitle>
          <CardDescription>
            Current version: {version?.version || 'Loading...'}
            {version?.git_commit && (
              <span className="text-xs ml-2">({version.git_commit})</span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button
              onClick={checkForUpdates}
              disabled={checking}
              variant="outline"
            >
              {checking ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              Check for Updates
            </Button>
          </div>

          {update && (
            <div className={`p-4 rounded-lg ${
              update.update_available ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-green-500/10 border border-green-500/20'
            }`}>
              {update.update_available ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-yellow-500" />
                    <span className="font-medium">
                      Update available: {update.current_version} → {update.latest_version}
                    </span>
                  </div>
                  {update.release_notes && (
                    <p className="text-sm text-muted-foreground">{update.release_notes}</p>
                  )}
                  <Button
                    onClick={installUpdate}
                    disabled={installing}
                  >
                    {installing ? 'Installing...' : 'Install Update'}
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>You're up to date!</span>
                </div>
              )}
            </div>
          )}

          <div className="pt-4 border-t">
            <Button variant="outline" onClick={restartService}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Restart Service
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* WiFi */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            Network
          </CardTitle>
        </CardHeader>
        <CardContent>
          {wifiStatus ? (
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <span className={wifiStatus.connected ? 'text-green-500' : 'text-red-500'}>
                  {wifiStatus.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {wifiStatus.ssid && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Network</span>
                  <span>{wifiStatus.ssid}</span>
                </div>
              )}
              {wifiStatus.ip_address && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">IP Address</span>
                  <span>{wifiStatus.ip_address}</span>
                </div>
              )}
              {wifiStatus.signal && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Signal</span>
                  <span>{wifiStatus.signal} dBm</span>
                </div>
              )}
              {wifiStatus.hotspot_active && (
                <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg">
                  <p className="text-sm">
                    Setup hotspot is active. Connect to <strong>tars-wifi-setup</strong> to configure WiFi.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">Loading...</p>
          )}
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">About</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-1">
          <p>TARS Robot Dashboard</p>
          <p>Version {version?.version || '...'}</p>
          <p className="pt-2">
            <a
              href="https://github.com/latishab/tars"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              GitHub Repository
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default SettingsPage
