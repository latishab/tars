import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Download, RefreshCw, Wifi, AlertCircle, CheckCircle, Signal, Lock, WifiOff, Gamepad2 } from 'lucide-react'

const FACE_BUTTONS = [
  { key: 'BTN_SOUTH',    label: '✕' },
  { key: 'BTN_SOUTH+R1', label: '✕ + R1' },
  { key: 'BTN_EAST',     label: '○' },
  { key: 'BTN_EAST+R1',  label: '○ + R1' },
  { key: 'BTN_EAST+R2',  label: '○ + R2' },
  { key: 'BTN_NORTH',    label: '△' },
  { key: 'BTN_NORTH+R1', label: '△ + R1' },
  { key: 'BTN_WEST',     label: '□' },
  { key: 'BTN_WEST+R1',  label: '□ + R1' },
]

const DPAD_BUTTONS = [
  { key: 'DPAD_UP',       label: 'Up' },
  { key: 'DPAD_UP+L2',    label: 'Up + L2' },
  { key: 'DPAD_DOWN',     label: 'Down' },
  { key: 'DPAD_DOWN+L2',  label: 'Down + L2' },
  { key: 'DPAD_LEFT',     label: 'Left' },
  { key: 'DPAD_LEFT+L2',  label: 'Left + L2' },
  { key: 'DPAD_RIGHT',    label: 'Right' },
  { key: 'DPAD_RIGHT+L2', label: 'Right + L2' },
]

const DEFAULT_MAPPINGS = {
  BTN_SOUTH: 'pose', 'BTN_SOUTH+R1': 'wave_right',
  BTN_EAST: 'bow', 'BTN_EAST+R1': 'wave_left', 'BTN_EAST+R2': 'side_side',
  BTN_NORTH: 'laugh', 'BTN_NORTH+R1': 'tilt_right',
  BTN_WEST: 'wiggle', 'BTN_WEST+R1': 'tilt_left',
  DPAD_UP: 'walk_forward', 'DPAD_UP+L2': 'step_forward',
  DPAD_DOWN: 'walk_backward', 'DPAD_DOWN+L2': 'step_backward',
  DPAD_LEFT: 'turn_left_slow', 'DPAD_LEFT+L2': 'turn_left',
  DPAD_RIGHT: 'turn_right_slow', 'DPAD_RIGHT+L2': 'turn_right',
}

function ControllerCard() {
  const [mappings, setMappings] = useState(DEFAULT_MAPPINGS)
  const [movements, setMovements] = useState([])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetch('/api/settings')
      .then(r => r.json())
      .then(data => {
        if (data.controller?.mappings) setMappings(data.controller.mappings)
      })
      .catch(console.error)

    fetch('/api/control/movements')
      .then(r => r.json())
      .then(data => setMovements(data.movements || []))
      .catch(console.error)
  }, [])

  const locomotion = movements.filter(m => m.type === 'locomotion')
  const gestures = movements.filter(m => m.type === 'gesture')

  const handleChange = (key, value) => {
    setMappings(prev => ({ ...prev, [key]: value }))
    setSaved(false)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ controller: { mappings } }),
      })
      setSaved(true)
    } catch (err) {
      console.error('Failed to save controller mappings:', err)
    }
    setSaving(false)
  }

  const handleReset = () => {
    setMappings(DEFAULT_MAPPINGS)
    setSaved(false)
  }

  const MovementSelect = ({ btnKey }) => (
    <select
      value={mappings[btnKey] || ''}
      onChange={e => handleChange(btnKey, e.target.value)}
      className="bg-background border border-border rounded px-2 py-1 text-sm flex-1 min-w-0"
    >
      <option value="">— none —</option>
      {locomotion.length > 0 && (
        <optgroup label="Locomotion">
          {locomotion.map(m => (
            <option key={m.name} value={m.name}>{m.name}</option>
          ))}
        </optgroup>
      )}
      {gestures.length > 0 && (
        <optgroup label="Gesture">
          {gestures.map(m => (
            <option key={m.name} value={m.name}>{m.name}</option>
          ))}
        </optgroup>
      )}
    </select>
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Gamepad2 className="w-5 h-5" />
          Controller
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4 sm:gap-0">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">Face Buttons</p>
            <div className="space-y-1.5">
              {FACE_BUTTONS.map(({ key, label }) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground font-mono w-14 shrink-0 text-right">{label}</span>
                  <MovementSelect btnKey={key} />
                </div>
              ))}
            </div>
          </div>

          <div className="hidden sm:block w-px bg-border mx-4 self-stretch" />

          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">D-Pad</p>
            <div className="space-y-1.5">
              {DPAD_BUTTONS.map(({ key, label }) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-14 shrink-0 text-right">{label}</span>
                  <MovementSelect btnKey={key} />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-2 pt-2 border-t">
          <Button variant="outline" size="sm" onClick={handleReset}>
            Reset Defaults
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving}>
            {saving ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : null}
            {saved ? 'Saved' : 'Save'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

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
  const [connectionReady, setConnectionReady] = useState(false)
  const [connectionPayload, setConnectionPayload] = useState(null)
  const [successInfo, setSuccessInfo] = useState(null)

  useEffect(() => {
    // Get current version
    fetch('/api/system/updates/current')
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

  // Step 1: Prepare connection and show modal (DON'T connect yet)
  const prepareConnection = async () => {
    setConnecting(true)
    setWifiError(null)
    try {
      const ssid = isManualEntry ? manualSsid : selectedNetwork.ssid

      if (!ssid) {
        setWifiError('Please enter network SSID')
        setConnecting(false)
        return
      }

      const payload = {
        ssid,
        password: password || '',
        is_enterprise: isEnterprise
      }

      if (isEnterprise) {
        if (!username) {
          setWifiError('Username required for enterprise WiFi')
          setConnecting(false)
          return
        }
        payload.username = username
        payload.eap_method = 'peap'
        payload.phase2_auth = 'mschapv2'
      }

      // Get Tailscale IP
      const statusRes = await fetch('/api/wifi/status')
      const statusData = await statusRes.json()
      const tailscaleIp = statusData.tailscale_ip || 'unknown'

      // Save payload for later
      setConnectionPayload(payload)

      // Show modal with URLs (DON'T connect yet)
      setSuccessInfo({
        ssid: ssid,
        tailscale_ip: tailscaleIp
      })
      setShowSuccessModal(true)
      setConnectionReady(true)
      setConnecting(false)
    } catch (err) {
      setWifiError(err.message)
      setConnecting(false)
    }
  }

  // Step 2: Actually make the connection (called from modal button)
  const actuallyConnect = async () => {
    if (!connectionPayload || !connectionReady) return

    setConnecting(true)
    try {
      const res = await fetch('/api/wifi/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(connectionPayload)
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Connection failed')
      }

      // Success - hotspot will shut down now
      setShowWifiSetup(false)
      setSelectedNetwork(null)
      setPassword('')
      setUsername('')
      setManualSsid('')
      setIsManualEntry(false)
      setIsEnterprise(false)
      setNetworks([])
      setConnectionReady(false)
      setConnectionPayload(null)
    } catch (err) {
      setWifiError(err.message)
      setShowSuccessModal(false)
      setConnectionReady(false)
    }
    setConnecting(false)
  }

  const cancelConnection = () => {
    setShowSuccessModal(false)
    setConnectionReady(false)
    setConnectionPayload(null)
    setConnecting(false)
  }

  const startHotspot = async () => {
    try {
      const res = await fetch('/api/wifi/hotspot', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: true })
      })
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
      const res = await fetch('/api/wifi/hotspot', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: false })
      })
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
      const res = await fetch('/api/system/updates/check')
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
      // Start the update
      const res = await fetch('/api/system/updates/install', { method: 'POST' })
      const data = await res.json()
      
      if (data.requires_restart) {
        // Update is starting - monitor the restart process
        await monitorUpdateRestart()
      }
    } catch (err) {
      console.error('Update install failed:', err)
      alert('Update failed. Check logs for details.')
      setInstalling(false)
    }
  }

  const monitorUpdateRestart = async () => {
    // Wait a bit for update to start
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    // Poll for service to go down (max 30s)
    let serviceDown = false
    for (let i = 0; i < 30; i++) {
      try {
        await fetch('/api/system/updates/current', { signal: AbortSignal.timeout(2000) })
        await new Promise(resolve => setTimeout(resolve, 1000))
      } catch {
        serviceDown = true
        break
      }
    }
    
    if (!serviceDown) {
      alert('Update may still be in progress. Refresh page in a moment.')
      setInstalling(false)
      return
    }
    
    // Service is down - wait for it to come back up (max 60s)
    for (let i = 0; i < 60; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000))
      try {
        const res = await fetch('/api/system/updates/current', { signal: AbortSignal.timeout(2000) })
        if (res.ok) {
          // Service is back! Refresh version info
          const newVersion = await res.json()
          setVersion(newVersion)
          setUpdate(null) // Clear update notification
          setInstalling(false)
          alert(`✓ Updated to v${newVersion.version}!`)
          return
        }
      } catch {
        // Still down, keep waiting
      }
    }
    
    // Timeout - ask user to refresh
    alert('Update completed but service did not restart. Please refresh the page.')
    setInstalling(false)
  }

  const restartService = async () => {
    if (!confirm('Restart TARS service?')) return
    try {
      await fetch('/api/system/updates/restart', { method: 'POST' })
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

      {/* Success Modal - Manual confirmation before connecting */}
      {showSuccessModal && successInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-500">
                <Wifi className="w-6 h-6" />
                Ready to Connect
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="font-medium">Network:</p>
                <p className="text-2xl font-bold mt-1">{successInfo.ssid}</p>
              </div>

              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 space-y-3">
                <p className="font-medium text-sm">📋 Save these URLs before connecting:</p>

                <div className="bg-background p-3 rounded border space-y-2">
                  <div>
                    <p className="text-xs text-muted-foreground">Tailscale (works everywhere):</p>
                    <p className="text-base font-mono font-bold select-all">http://tars:8000</p>
                  </div>
                  <div className="pt-2 border-t">
                    <p className="text-xs text-muted-foreground">Local network (home WiFi only):</p>
                    <p className="text-base font-mono font-bold select-all">http://tars.local:8000</p>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground">💡 Tailscale works from anywhere - dorm, home, or mobile data</p>
              </div>

              <div className="space-y-2 text-sm bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                <p className="font-medium">⚠️ After clicking "Connect Now":</p>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                  <li>TARS will connect to <span className="font-medium text-foreground">{successInfo.ssid}</span></li>
                  <li>This setup page will disconnect (hotspot shuts down)</li>
                  <li>Reconnect your device to <span className="font-medium text-foreground">{successInfo.ssid}</span></li>
                  <li>Open the Tailscale URL above to access TARS</li>
                </ol>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={cancelConnection}
                  variant="outline"
                  className="flex-1"
                  disabled={connecting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={actuallyConnect}
                  className="flex-1"
                  disabled={connecting}
                >
                  {connecting ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    "Connect Now"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Controller Mappings */}
      <ControllerCard />

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
                  <span className={wifiStatus.mode === 'wlan' ? 'text-green-500' : wifiStatus.mode === 'hotspot' ? 'text-yellow-500' : 'text-red-500'}>
                    {wifiStatus.mode === 'wlan' ? 'Connected' : wifiStatus.mode === 'hotspot' ? 'Hotspot Active' : 'Disconnected'}
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

              {/* Dashboard Access URLs */}
              {wifiStatus.mode === 'wlan' && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 space-y-2">
                  <p className="text-sm font-medium">Dashboard Access:</p>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-start gap-2">
                      <span className="text-muted-foreground min-w-20">Local:</span>
                      <span className="font-mono">http://tars.local:8000</span>
                      <span className="text-muted-foreground">(home networks)</span>
                    </div>
                    {wifiStatus.tailscale_ip && (
                      <div className="flex items-start gap-2">
                        <span className="text-muted-foreground min-w-20">Tailscale:</span>
                        <span className="font-mono">http://tars:8000</span>
                        <span className="text-muted-foreground">(works everywhere)</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

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
                        onClick={prepareConnection}
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
            <div className="space-y-1">
              <div>
                Current version: {version?.version || 'Loading...'}
                {version?.git_commit && (
                  <span className="text-xs ml-2">({version.git_commit})</span>
                )}
              </div>
              {version?.install_mode && (
                <div className="text-xs">
                  Update Source: <span className="capitalize">{version.install_mode === 'git' ? 'Git (Developer)' : 'PyPI (Stable)'}</span>
                </div>
              )}
            </div>
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
