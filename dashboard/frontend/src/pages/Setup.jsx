import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Wifi, RefreshCw, CheckCircle, Loader2, Signal } from 'lucide-react'

function Setup({ onComplete }) {
  const [networks, setNetworks] = useState([])
  const [scanning, setScanning] = useState(false)
  const [selectedNetwork, setSelectedNetwork] = useState(null)
  const [password, setPassword] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

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

  const connectToNetwork = async (e) => {
    e.preventDefault()
    if (!selectedNetwork) return

    setConnecting(true)
    setError(null)

    try {
      const res = await fetch('/api/wifi/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ssid: selectedNetwork.ssid,
          password: password || null,
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Connection failed')
      }

      setSuccess(true)

      // Wait a bit then call onComplete
      setTimeout(() => {
        onComplete?.()
      }, 3000)

    } catch (err) {
      setError(err.message || 'Failed to connect')
    }

    setConnecting(false)
  }

  const getSignalIcon = (signal) => {
    if (signal > -50) return 'text-green-500'
    if (signal > -70) return 'text-yellow-500'
    return 'text-red-500'
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Connected!</h2>
            <p className="text-muted-foreground mb-4">
              TARS is now connected to {selectedNetwork.ssid}
            </p>
            <p className="text-sm text-muted-foreground">
              The hotspot will turn off. Reconnect to your home WiFi
              and open <strong>http://tars.local:8080</strong>
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-md mx-auto space-y-4">
        <div className="text-center py-8">
          <Wifi className="w-16 h-16 mx-auto mb-4 text-primary" />
          <h1 className="text-3xl font-bold">TARS Setup</h1>
          <p className="text-muted-foreground mt-2">
            Connect TARS to your WiFi network
          </p>
        </div>

        {/* Network Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              <span>Available Networks</span>
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

        {/* Password Input */}
        {selectedNetwork && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Connect to {selectedNetwork.ssid}
              </CardTitle>
              <CardDescription>
                {selectedNetwork.security === 'open'
                  ? 'This is an open network'
                  : 'Enter the network password'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={connectToNetwork} className="space-y-4">
                {selectedNetwork.security !== 'open' && (
                  <Input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={connecting}
                  />
                )}

                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  disabled={connecting || (selectedNetwork.security !== 'open' && !password)}
                >
                  {connecting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    'Connect'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Help Text */}
        <Card>
          <CardContent className="pt-6 text-sm text-muted-foreground">
            <p>
              After connecting, the setup hotspot will turn off. Reconnect your
              device to your home WiFi network and access TARS at:
            </p>
            <p className="mt-2 font-mono">
              http://tars.local:8080
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Setup
