import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Battery, Cpu, Thermometer, Wifi, Radio, Eye, Copy, Check, Zap, Activity, Signal } from 'lucide-react'
import { Button } from '@/components/ui/button'

function Status() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/status')
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
      <div className="container max-w-4xl mx-auto p-4">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive flex items-center gap-2">
              <Activity className="w-4 h-4 animate-pulse" />
              {error}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="container max-w-4xl mx-auto p-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Activity className="w-4 h-4 animate-spin" />
              <span>Loading system status...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const battery = status.battery || {}
  const system = status.system || {}
  const display = status.display || {}
  const connections = status.connections || {}
  const network = status.network || {}

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getBatteryColor = (level) => {
    if (level > 60) return 'text-green-500'
    if (level > 20) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getTempColor = (temp) => {
    if (temp > 70) return 'text-red-500'
    if (temp > 60) return 'text-yellow-500'
    return 'text-green-500'
  }

  return (
    <div className="container max-w-4xl mx-auto p-4 space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Status</h1>
          <p className="text-muted-foreground">Real-time monitoring and diagnostics</p>
        </div>
        <Badge variant="success" className="flex items-center gap-1.5 px-3 py-1.5">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          Online
        </Badge>
      </div>

      {/* Battery Card */}
      <Card className="overflow-hidden border-border/50 hover:border-primary/50 transition-colors">
        <CardHeader className="pb-3 bg-gradient-to-r from-primary/10 via-transparent to-transparent">
          <CardTitle className="text-lg flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Battery className={`w-5 h-5 ${getBatteryColor(battery.level)}`} />
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2">
                <span>Battery</span>
                <span className={`text-2xl font-bold ${getBatteryColor(battery.level)}`}>
                  {battery.level}%
                </span>
              </div>
            </div>
            <Badge variant={battery.charging ? 'success' : 'secondary'} className="gap-1.5">
              {battery.charging ? (
                <>
                  <Zap className="w-3 h-3" />
                  Charging
                </>
              ) : (
                'Discharging'
              )}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 space-y-3">
          <Progress value={battery.level} className="h-3" />
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-muted/50">
              <span className="text-muted-foreground">Voltage</span>
              <span className="font-semibold">{battery.voltage?.toFixed(2)}V</span>
            </div>
            <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-muted/50">
              <span className="text-muted-foreground">Current</span>
              <span className="font-semibold">{battery.current?.toFixed(0)}mA</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Resources */}
      <Card className="border-border/50 hover:border-primary/50 transition-colors">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Cpu className="w-5 h-5 text-primary" />
            </div>
            System Resources
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4">
            {/* CPU */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground font-medium">CPU Usage</span>
                <span className="font-bold">{system.cpu_percent?.toFixed(1)}%</span>
              </div>
              <Progress value={system.cpu_percent} className="h-2" />
            </div>

            {/* Memory */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground font-medium">Memory</span>
                <span className="font-bold">
                  {system.memory_used_mb?.toFixed(0)}MB / {system.memory_total_mb?.toFixed(0)}MB
                </span>
              </div>
              <Progress value={system.memory_percent} className="h-2" />
            </div>

            {/* Temperature */}
            <div className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2">
                <Thermometer className={`w-4 h-4 ${getTempColor(system.cpu_temp)}`} />
                <span className="text-sm font-medium text-muted-foreground">CPU Temperature</span>
              </div>
              <span className={`text-lg font-bold ${getTempColor(system.cpu_temp)}`}>
                {system.cpu_temp ? `${system.cpu_temp.toFixed(1)}°C` : 'N/A'}
              </span>
            </div>

            {/* Platform */}
            <div className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-muted/50">
              <span className="text-sm font-medium text-muted-foreground">Platform</span>
              <Badge variant="outline">{system.platform}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Network & Connections */}
      <Card className="border-border/50 hover:border-primary/50 transition-colors">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Wifi className="w-5 h-5 text-primary" />
            </div>
            Network & Connections
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Connection Mode */}
          {network.connection_mode && (
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-2">Connection Mode</div>
              <div className="flex items-center gap-2">
                <Badge variant="default" className="text-base px-3 py-1.5 capitalize">
                  <Signal className="w-3.5 h-3.5 mr-1.5" />
                  {network.connection_mode}
                </Badge>
              </div>
              {network.connection_mode === 'tailscale' && network.tailscale_ip && (
                <div className="mt-3 flex items-center gap-2 p-3 rounded-lg bg-muted/50 border border-border/50">
                  <code className="text-sm flex-1 font-mono">{network.tailscale_ip}</code>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => copyToClipboard(network.tailscale_ip)}
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              )}
            </div>
          )}

          <Separator />

          {/* Connection Status */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-muted/50 border border-border/50">
              <div className={`p-1.5 rounded-full ${connections.webrtc ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                <Radio className={`w-4 h-4 ${connections.webrtc ? 'text-green-500' : 'text-red-500'}`} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">WebRTC</div>
                <div className={`text-xs ${connections.webrtc ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {connections.webrtc ? 'Connected' : 'Disconnected'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-muted/50 border border-border/50">
              <div className={`p-1.5 rounded-full ${connections.grpc ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                <Radio className={`w-4 h-4 ${connections.grpc ? 'text-green-500' : 'text-red-500'}`} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">gRPC</div>
                <div className={`text-xs ${connections.grpc ? 'text-green-500' : 'text-muted-foreground'}`}>
                  {connections.grpc ? 'Ready' : 'Error'}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Display State */}
      <Card className="border-border/50 hover:border-primary/50 transition-colors">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Eye className="w-5 h-5 text-primary" />
            </div>
            Display State
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="px-4 py-3 rounded-lg bg-muted/50 border border-border/50">
              <div className="text-sm text-muted-foreground mb-1">Emotion</div>
              <Badge variant="secondary" className="text-base px-3 py-1 capitalize">
                {display.emotion}
              </Badge>
            </div>
            <div className="px-4 py-3 rounded-lg bg-muted/50 border border-border/50">
              <div className="text-sm text-muted-foreground mb-1">Eye State</div>
              <Badge variant="secondary" className="text-base px-3 py-1 capitalize">
                {display.eye_state}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Status
