import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Download, RefreshCw, Wifi, AlertCircle, CheckCircle, Signal, Lock, WifiOff } from 'lucide-react'

function SettingsPage() {
  const [version, setVersion] = useState(null)
  const [update, setUpdate] = useState(null)
  const [wifiStatus, setWifiStatus] = useState(null)
  const [networks, setNetworks] = useState([])
  const [selectedNetwork, setSelectedNetwork] = useState(null)
  const [password, setPassword] = useState('')
  const [checking, setChecking] = useState(false)
  const [installing, setInstalling] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [wifiError, setWifiError] = useState(null)
  const [showWifiSetup, setShowWifiSetup] = useState(false)
  const [isManualEntry, setIsManualEntry] = useState(false)
  const [manualSsid, setManualSsid] = useState('')
  const [isEnterprise, setIsEnterprise] = useState(false)
  const [username, setUsername] = useState('')
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [successInfo, setSuccessInfo] = useState(null)

  useEffect(() => {
    // Get current version
    fetch('/api/updates/current')
      .then(res => res.json())
      .then(setVersion)
      .catch(console.error)

    // Get WiFi status
    loadWifiStatus()
  }, [])

  const loadWifiStatus = async () => {
    try {
      const res = await fetch('/api/wifi/status')
      const data = await res.json()
      setWifiStatus(data)
    } catch (err) {
      console.error('Failed to load WiFi status:', err)
    }
  }

  const scanNetworks = async () => {
    setScanning(true)
    setWifiError(null)
    try {
      const res = await fetch('/api/wifi/networks')
      const data = await res.json()
      setNetworks(data.networks || [])
    } catch (err) {
      setWifiError('Failed to scan networks')
    }
    setScanning(false)
  }

  const connectToNetwork = async () => {
    setConnecting(true)
    setWifiError(null)
    try {
      const ssid = isManualEntry ? manualSsid : selectedNetwork.ssid

      if (!ssid) {
        setWifiError('Please enter network SSID')
        setConnecting(false)
        return
      }

      // Get Tailscale IP before connecting
      const statusRes = await fetch('/api/wifi/status')
      const statusData = await statusRes.json()
      const tailscaleIp = statusData.tailscale_ip || '100.84.133.74'

      // Show modal FIRST with instructions
      setSuccessInfo({
        ssid: ssid,
        tailscale_ip: tailscaleIp
      })
      setShowSuccessModal(true)

      const payload = {
        ssid,
        password: password || '',
        is_enterprise: isEnterprise
      }

      if (isEnterprise) {
        if (!username) {
          setWifiError('Username required for enterprise WiFi')
          setConnecting(false)
          setShowSuccessModal(false)
          return
        }
        payload.username = username
        payload.eap_method = 'peap'
        payload.phase2_auth = 'mschapv2'
      }

      // Now connect (hotspot will shut down after this)
      const res = await fetch('/api/wifi/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const error = await res.json()
        setShowSuccessModal(false)
        throw new Error(error.detail || 'Connection failed')
      }

      setShowWifiSetup(false)
      setSelectedNetwork(null)
      setPassword('')
      setUsername('')
      setManualSsid('')
      setIsManualEntry(false)
      setIsEnterprise(false)
      setNetworks([])
    } catch (err) {
      setWifiError(err.message)
      setShowSuccessModal(false)
    }
    setConnecting(false)
  }

  const startHotspot = async () => {
    try {
      const res = await fetch('/api/wifi/hotspot/start', { method: 'POST' })
      const data = await res.json()
      if (data.success) {
        await loadWifiStatus()
        alert('Hotspot started: TARS-Setup (password: tars1234)')
      }
    } catch (err) {
      alert('Failed to start hotspot')
    }
  }

  const stopHotspot = async () => {
    try {
      const res = await fetch('/api/wifi/hotspot/stop', { method: 'POST' })
      const data = await res.json()
      if (data.success) {
        await loadWifiStatus()
      }
    } catch (err) {
      alert('Failed to stop hotspot')
    }
  }

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

  const getSignalIcon = (signal) => {
    if (signal >= 70) return <Signal className="w-4 h-4 text-green-500" />
    if (signal >= 50) return <Signal className="w-4 h-4 text-yellow-500" />
    return <Signal className="w-4 h-4 text-red-500" />
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Success Modal */}
      {showSuccessModal && successInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-500">
                <Wifi className="w-6 h-6" />
                Connecting to WiFi...
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="font-medium">Connecting to:</p>
                <p className="text-2xl font-bold mt-1">{successInfo.ssid}</p>
              </div>

              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 space-y-2">
                <p className="font-medium text-sm">⚠️ Important - Save this address:</p>
                <div className="bg-background p-3 rounded border">
                  <p className="text-xs text-muted-foreground">Dashboard URL (via Tailscale):</p>
                  <p className="text-lg font-mono font-bold select-all">http://{successInfo.tailscale_ip}:8080</p>
                </div>
                <p className="text-xs text-muted-foreground">This link works from anywhere - home, dorm, or mobile data</p>
              </div>

              <div className="space-y-2 text-sm bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                <p className="font-medium">What happens next:</p>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                  <li>TARS will connect to <span className="font-medium text-foreground">{successInfo.ssid}</span></li>
                  <li>This setup hotspot will shut down</li>
                  <li>Reconnect your device to <span className="font-medium text-foreground">{successInfo.ssid}</span></li>
                  <li>Open: <span className="font-mono font-medium text-foreground">http://{successInfo.tailscale_ip}:8080</span></li>
                </ol>
              </div>

              <Button
                onClick={() => setShowSuccessModal(false)}
                className="w-full"
              >
                I saved the address!
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* WiFi */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            Network
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {wifiStatus ? (
            <>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <span className={wifiStatus.mode === 'client' ? 'text-green-500' : wifiStatus.mode === 'hotspot' ? 'text-yellow-500' : 'text-red-500'}>
                    {wifiStatus.mode === 'client' ? 'Connected' : wifiStatus.mode === 'hotspot' ? 'Hotspot Active' : 'Disconnected'}
                  </span>
                </div>
                {wifiStatus.ssid && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Network</span>
                    <span>{wifiStatus.ssid}</span>
                  </div>
                )}
                {wifiStatus.ip && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">IP Address</span>
                    <span className="font-mono text-sm">{wifiStatus.ip}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-2 pt-2 border-t">
                {!showWifiSetup ? (
                  <>
                    <Button onClick={() => setShowWifiSetup(true)} variant="outline">
                      <Wifi className="w-4 h-4 mr-2" />
                      Change Network
                    </Button>
                    {wifiStatus.mode === 'hotspot' ? (
                      <Button onClick={stopHotspot} variant="outline">
                        <WifiOff className="w-4 h-4 mr-2" />
                        Stop Hotspot
                      </Button>
                    ) : (
                      <Button onClick={startHotspot} variant="outline">
                        <Wifi className="w-4 h-4 mr-2" />
                        Start Hotspot
                      </Button>
                    )}
                  </>
                ) : (
                  <Button onClick={() => { setShowWifiSetup(false); setSelectedNetwork(null); setNetworks([]); }} variant="outline">
                    Cancel
                  </Button>
                )}
              </div>

              {/* WiFi Setup Section */}
              {showWifiSetup && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="flex justify-between items-center">
                    <h3 className="font-medium">Available Networks</h3>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={scanNetworks}
                      disabled={scanning}
                    >
                      <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>

                  {wifiError && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-500">
                      {wifiError}
                    </div>
                  )}

                  {networks.length === 0 && !scanning && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Wifi className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Click the refresh button to scan for networks</p>
                    </div>
                  )}

                  {scanning && (
                    <div className="text-center py-8 text-muted-foreground">
                      <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
                      <p>Scanning for networks...</p>
                    </div>
                  )}

                  {networks.length > 0 && (
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {networks.map((network) => (
                        <button
                          key={network.ssid}
                          onClick={() => setSelectedNetwork(network)}
                          className={`w-full p-3 rounded-lg border text-left transition-colors ${
                            selectedNetwork?.ssid === network.ssid
                              ? 'border-primary bg-primary/10'
                              : 'border-border hover:border-primary/50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getSignalIcon(network.signal)}
                              <span className="font-medium">{network.ssid}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              {network.security !== 'open' && (
                                <Lock className="w-3 h-3" />
                              )}
                              <span>{network.signal}%</span>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Manual Entry Toggle */}
                  {networks.length > 0 && (
                    <div className="pt-2 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setIsManualEntry(!isManualEntry)
                          setSelectedNetwork(null)
                        }}
                        className="w-full"
                      >
                        {isManualEntry ? 'Select from list' : 'Enter network manually'}
                      </Button>
                    </div>
                  )}

                  {/* Connection Form */}
                  {(selectedNetwork || isManualEntry) && (
                    <div className="space-y-3 pt-2 border-t">
                      <div className="space-y-3">
                        <h4 className="font-medium">
                          {isManualEntry ? 'Manual Network Entry' : `Connect to ${selectedNetwork.ssid}`}
                        </h4>

                        {/* Manual SSID Entry */}
                        {isManualEntry && (
                          <Input
                            type="text"
                            placeholder="Network SSID"
                            value={manualSsid}
                            onChange={(e) => setManualSsid(e.target.value)}
                            disabled={connecting}
                          />
                        )}

                        {/* Network Type Selector */}
                        <div className="space-y-2">
                          <label className="text-sm text-muted-foreground">Network Type</label>
                          <div className="flex gap-2">
                            <Button
                              variant={!isEnterprise ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => setIsEnterprise(false)}
                              disabled={connecting}
                              className="flex-1"
                            >
                              Personal
                            </Button>
                            <Button
                              variant={isEnterprise ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => setIsEnterprise(true)}
                              disabled={connecting}
                              className="flex-1"
                            >
                              Enterprise
                            </Button>
                          </div>
                        </div>

                        {/* Enterprise Username */}
                        {isEnterprise && (
                          <Input
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            disabled={connecting}
                          />
                        )}

                        {/* Password Field */}
                        <Input
                          type="password"
                          placeholder={isEnterprise ? "Password" : "WiFi Password"}
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          disabled={connecting}
                        />
                      </div>

                      <Button
                        onClick={connectToNetwork}
                        disabled={connecting || (isEnterprise && !username) || (!isManualEntry && !selectedNetwork)}
                        className="w-full"
                      >
                        {connecting ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Connecting...
                          </>
                        ) : (
                          'Connect'
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="text-muted-foreground">Loading...</p>
          )}
        </CardContent>
      </Card>

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
