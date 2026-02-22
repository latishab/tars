import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Battery, Cpu, Thermometer, Wifi, Radio, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'

function Status() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/status/')
        const data = await res.json()
        setStatus(data)
        setError(null)
      } catch (err) {
        setError('Failed to fetch status')
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  if (error) {
    return (
      <div className="p-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="p-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Loading...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const battery = status.battery || {}
  const system = status.system || {}
  const connections = status.connections || {}
  const network = status.network || {}

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">TARS Status</h1>

      {/* Battery */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Battery className="w-5 h-5" />
            Battery
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold">{battery.level}%</div>
              <div className="text-sm text-muted-foreground">
              </div>
            </div>
            <div className="text-right text-sm text-muted-foreground">
              <div>{battery.voltage?.toFixed(2)}V</div>
              <div>{battery.current?.toFixed(0)}mA</div>
            </div>
          </div>
          <div className="mt-2 h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                battery.level > 20 ? 'bg-green-500' : 'bg-red-500'
              }`}
              style={{ width: `${battery.level}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* System */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Cpu className="w-5 h-5" />
            System
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* 2 columns on mobile, 3 on tablet+ */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">CPU</div>
              <div className="text-xl font-semibold">{system.cpu_percent?.toFixed(0)}%</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Memory</div>
              <div className="text-xl font-semibold">{system.memory_percent?.toFixed(0)}%</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground flex items-center gap-1">
                <Thermometer className="w-3 h-3" /> Temp
              </div>
              <div className="text-xl font-semibold">
                {system.cpu_temp ? `${system.cpu_temp.toFixed(1)}C` : 'N/A'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Network & Connections */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            Network & Connections
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Connection mode */}
          {network.connection_mode && (
            <div>
              <div className="text-sm text-muted-foreground mb-2">Connection Mode</div>
              <div className="text-lg font-semibold capitalize">{network.connection_mode}</div>
              {network.connection_mode === 'tailscale' && network.tailscale_ip && (
                <div className="mt-2 flex items-center gap-2 bg-secondary p-2 rounded">
                  <code className="text-sm flex-1">{network.tailscale_ip}</code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(network.tailscale_ip)}
                  >
                    {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Connection status - stack on mobile */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <Radio className={`w-4 h-4 ${connections.webrtc ? 'text-green-500' : 'text-red-500'}`} />
              <span>WebRTC</span>
              <span className={`text-sm ${connections.webrtc ? 'text-green-500' : 'text-muted-foreground'}`}>
                {connections.webrtc ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Radio className={`w-4 h-4 ${connections.grpc ? 'text-green-500' : 'text-red-500'}`} />
              <span>gRPC</span>
              <span className={`text-sm ${connections.grpc ? 'text-green-500' : 'text-muted-foreground'}`}>
                {connections.grpc ? 'Ready' : 'Error'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Status
