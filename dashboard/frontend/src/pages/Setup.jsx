import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Wifi, RefreshCw, CheckCircle, Loader2, Signal, Key, ChevronRight, ChevronLeft, Radio } from 'lucide-react'

function Setup({ onComplete }) {
  // Step management
  const [step, setStep] = useState(1)

  // Step 1: WiFi
  const [networks, setNetworks] = useState([])
  const [scanning, setScanning] = useState(false)
  const [selectedNetwork, setSelectedNetwork] = useState(null)
  const [password, setPassword] = useState('')

  // Step 1.5: Network mode
  const [connectionMode, setConnectionMode] = useState('local')
  const [tailscaleAuthKey, setTailscaleAuthKey] = useState('')

  // Step 2: API Keys
  const [anthropicApiKey, setAnthropicApiKey] = useState('')
  const [deepgramApiKey, setDeepgramApiKey] = useState('')

  // Final step
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [tailscaleIp, setTailscaleIp] = useState(null)

  const scanNetworks = async () => {
    setScanning(true)
    setError(null)
    try {
      const res = await fetch('/api/wifi/networks')
      const data = await res.json()
      setNetworks(data.networks || [])
    } catch (err) {
      setError('Failed to scan for networks')
    }
    setScanning(false)
  }

  useEffect(() => {
    scanNetworks()
  }, [])

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)

    try {
      const res = await fetch('/api/setup/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wifi_ssid: selectedNetwork.ssid,
          wifi_password: password || null,
          anthropic_api_key: anthropicApiKey,
          deepgram_api_key: deepgramApiKey || null,
          tailscale_enabled: connectionMode === 'tailscale',
          tailscale_auth_key: connectionMode === 'tailscale' ? tailscaleAuthKey : null,
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Setup failed')
      }

      const data = await res.json()

      setSuccess(true)

      // If Tailscale, poll for IP (simulated - in real scenario firstboot script sets it)
      if (connectionMode === 'tailscale') {
        // In production, this would poll /api/status for tailscale_ip
        setTimeout(() => {
          setTailscaleIp('100.x.x.x')  // Placeholder
        }, 3000)
      }

      // Wait then complete
      setTimeout(() => {
        onComplete?.()
      }, connectionMode === 'tailscale' ? 6000 : 3000)

    } catch (err) {
      setError(err.message || 'Setup failed')
    }

    setSubmitting(false)
  }

  const getSignalIcon = (signal) => {
    if (signal > -50) return 'text-green-500'
    if (signal > -70) return 'text-yellow-500'
    return 'text-red-500'
  }

  const canProceedStep1 = selectedNetwork !== null
  const canProceedStep1_5 = connectionMode === 'local' || (connectionMode === 'tailscale' && tailscaleAuthKey)
  const canProceedStep2 = anthropicApiKey.trim() !== ''

  // Success screen
  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Setup Complete!</h2>
            <p className="text-muted-foreground mb-4">
              TARS is now connected to {selectedNetwork.ssid}
            </p>

            {connectionMode === 'tailscale' ? (
              <div className="space-y-3">
                {tailscaleIp ? (
                  <>
                    <p className="text-sm text-muted-foreground">
                      Your Tailscale IP:
                    </p>
                    <div className="bg-secondary p-3 rounded-lg font-mono text-lg">
                      {tailscaleIp}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Access TARS from any device on your Tailscale network at this IP on port 8080
                    </p>
                  </>
                ) : (
                  <div className="flex items-center justify-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Connecting to Tailscale...</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  The hotspot will turn off. Reconnect to your home WiFi and access TARS at:
                </p>
                <div className="bg-secondary p-3 rounded-lg font-mono">
                  http://tars.local:8080
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-md mx-auto space-y-4">
        {/* Header */}
        <div className="text-center py-8">
          <Wifi className="w-16 h-16 mx-auto mb-4 text-primary" />
          <h1 className="text-3xl font-bold">TARS Setup</h1>
          <p className="text-muted-foreground mt-2">
            Step {step} of 3
          </p>
        </div>

        {/* Step 1: WiFi Network Selection */}
        {step === 1 && (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center justify-between">
                  <span>Select WiFi Network</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={scanNetworks}
                    disabled={scanning}
                  >
                    <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {scanning && networks.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground">
                    <Loader2 className="w-6 h-6 animate-spin mr-2" />
                    Scanning...
                  </div>
                ) : networks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    No networks found. Click refresh to scan again.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {networks.map((network) => (
                      <button
                        key={network.ssid}
                        onClick={() => setSelectedNetwork(network)}
                        className={`w-full flex items-center justify-between p-3 rounded-lg border transition-colors ${
                          selectedNetwork?.ssid === network.ssid
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Signal className={`w-4 h-4 ${getSignalIcon(network.signal)}`} />
                          <span>{network.ssid}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {network.security !== 'open' && '🔒'}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {selectedNetwork && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">
                    {selectedNetwork.ssid}
                  </CardTitle>
                  <CardDescription>
                    {selectedNetwork.security === 'open'
                      ? 'This is an open network'
                      : 'Enter the network password'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {selectedNetwork.security !== 'open' && (
                    <Input
                      type="password"
                      placeholder="WiFi Password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  )}

                  {error && <p className="text-sm text-destructive">{error}</p>}

                  <Button
                    className="w-full"
                    onClick={() => setStep(2)}
                    disabled={!canProceedStep1 || (selectedNetwork.security !== 'open' && !password)}
                  >
                    Next <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Step 2: Network Mode */}
        {step === 2 && (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Radio className="w-5 h-5" />
                  Connection Mode
                </CardTitle>
                <CardDescription>
                  Choose how you'll access TARS
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <button
                  onClick={() => setConnectionMode('local')}
                  className={`w-full p-4 rounded-lg border text-left transition-colors ${
                    connectionMode === 'local'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="font-semibold mb-1">Local Network</div>
                  <div className="text-sm text-muted-foreground">
                    For home networks. Access via tars.local
                  </div>
                </button>

                <button
                  onClick={() => setConnectionMode('tailscale')}
                  className={`w-full p-4 rounded-lg border text-left transition-colors ${
                    connectionMode === 'tailscale'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="font-semibold mb-1">Tailscale</div>
                  <div className="text-sm text-muted-foreground">
                    For dorm/work networks with client isolation
                  </div>
                </button>
              </CardContent>
            </Card>

            {connectionMode === 'tailscale' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Tailscale Auth Key</CardTitle>
                  <CardDescription>
                    Get an auth key from{' '}
                    <a
                      href="https://login.tailscale.com/admin/settings/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      tailscale.com/admin/settings/keys
                    </a>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Input
                    type="password"
                    placeholder="tskey-auth-..."
                    value={tailscaleAuthKey}
                    onChange={(e) => setTailscaleAuthKey(e.target.value)}
                  />
                </CardContent>
              </Card>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                <ChevronLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <Button
                onClick={() => setStep(3)}
                disabled={!canProceedStep1_5}
                className="flex-1"
              >
                Next <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </>
        )}

        {/* Step 3: API Keys */}
        {step === 3 && (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Key className="w-5 h-5" />
                  API Keys
                </CardTitle>
                <CardDescription>
                  Configure TARS services
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Anthropic API Key <span className="text-destructive">*</span>
                  </label>
                  <Input
                    type="password"
                    placeholder="sk-ant-..."
                    value={anthropicApiKey}
                    onChange={(e) => setAnthropicApiKey(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Required for TARS AI functionality
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Deepgram API Key <span className="text-muted-foreground">(Optional)</span>
                  </label>
                  <Input
                    type="password"
                    placeholder="Enter Deepgram API key"
                    value={deepgramApiKey}
                    onChange={(e) => setDeepgramApiKey(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    For speech recognition features
                  </p>
                </div>

                {error && <p className="text-sm text-destructive">{error}</p>}
              </CardContent>
            </Card>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)} className="flex-1" disabled={submitting}>
                <ChevronLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!canProceedStep2 || submitting}
                className="flex-1"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Setting up...
                  </>
                ) : (
                  'Complete Setup'
                )}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Setup
