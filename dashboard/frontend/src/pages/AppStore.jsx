import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Download, Trash2, Play, Square, Star, ExternalLink } from 'lucide-react'

function AppStore() {
  const [allApps, setAllApps] = useState([])
  const [loading, setLoading] = useState({})
  const [error, setError] = useState(null)

  const fetchApps = async () => {
    try {
      const res = await fetch('/api/apps')
      const data = await res.json()
      
      // Combine all apps into single list
      const combined = [
        ...data.official.map(app => ({ ...app, source: 'official' })),
        ...data.community.map(app => ({ ...app, source: 'community' })),
        ...data.installed
          .filter(app => !data.official.find(o => o.id === app.id))
          .map(app => ({ ...app, source: 'installed' }))
      ]
      
      setAllApps(combined)
      setError(null)
    } catch (err) {
      setError('Failed to fetch apps')
    }
  }

  useEffect(() => {
    fetchApps()
    const interval = setInterval(fetchApps, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleInstall = async (app) => {
    setLoading({ ...loading, [`install-${app.id}`]: true })
    try {
      const res = await fetch('/api/apps/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_id: app.id,
          repository: app.repository
        })
      })
      const data = await res.json()
      if (res.ok) {
        await fetchApps()
      } else {
        alert(`Install failed: ${data.detail}`)
      }
    } catch (err) {
      alert(`Install error: ${err.message}`)
    } finally {
      setLoading({ ...loading, [`install-${app.id}`]: false })
    }
  }

  const handleUninstall = async (appId) => {
    if (!confirm('Are you sure you want to uninstall this app?')) return

    setLoading({ ...loading, [`uninstall-${appId}`]: true })
    try {
      const res = await fetch('/api/apps/uninstall', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId })
      })
      const data = await res.json()
      if (res.ok) {
        await fetchApps()
      } else {
        alert(`Uninstall failed: ${data.detail}`)
      }
    } catch (err) {
      alert(`Uninstall error: ${err.message}`)
    } finally {
      setLoading({ ...loading, [`uninstall-${appId}`]: false })
    }
  }

  const handleRun = async (appId) => {
    setLoading({ ...loading, [`run-${appId}`]: true })
    try {
      const res = await fetch('/api/apps/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId })
      })
      const data = await res.json()
      if (res.ok) {
        await fetchApps()
      } else {
        alert(`Run failed: ${data.detail}`)
      }
    } catch (err) {
      alert(`Run error: ${err.message}`)
    } finally {
      setLoading({ ...loading, [`run-${appId}`]: false })
    }
  }

  const handleStop = async (appId) => {
    setLoading({ ...loading, [`stop-${appId}`]: true })
    try {
      const res = await fetch('/api/apps/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId })
      })
      const data = await res.json()
      if (res.ok) {
        await fetchApps()
      } else {
        alert(`Stop failed: ${data.detail}`)
      }
    } catch (err) {
      alert(`Stop error: ${err.message}`)
    } finally {
      setLoading({ ...loading, [`stop-${appId}`]: false })
    }
  }

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

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Apps</h1>

      <div className="space-y-3">
        {allApps.map(app => (
          <Card key={app.id} className={app.featured ? 'border-primary' : ''}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="flex items-center gap-2">
                    {app.name}
                    {app.featured && <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />}
                    {app.official && !app.featured && (
                      <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">Official</span>
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1">{app.description}</CardDescription>
                  <div className="text-xs text-muted-foreground mt-2">
                    by {app.author}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 flex-wrap">
                {!app.installed ? (
                  <Button
                    onClick={() => handleInstall(app)}
                    disabled={loading[`install-${app.id}`]}
                    size="sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {loading[`install-${app.id}`] ? 'Installing...' : 'Install'}
                  </Button>
                ) : (
                  <>
                    {!app.running ? (
                      <Button
                        onClick={() => handleRun(app.id)}
                        disabled={loading[`run-${app.id}`]}
                        size="sm"
                        variant="default"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        {loading[`run-${app.id}`] ? 'Starting...' : 'Run'}
                      </Button>
                    ) : (
                      <Button
                        onClick={() => handleStop(app.id)}
                        disabled={loading[`stop-${app.id}`]}
                        size="sm"
                        variant="secondary"
                      >
                        <Square className="w-4 h-4 mr-2" />
                        {loading[`stop-${app.id}`] ? 'Stopping...' : 'Stop'}
                      </Button>
                    )}
                    <Button
                      onClick={() => handleUninstall(app.id)}
                      disabled={loading[`uninstall-${app.id}`]}
                      size="sm"
                      variant="destructive"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      {loading[`uninstall-${app.id}`] ? 'Removing...' : 'Uninstall'}
                    </Button>
                  </>
                )}
                {app.url && (
                  <Button
                    onClick={() => window.open(app.url, '_blank')}
                    size="sm"
                    variant="ghost"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                )}
              </div>
              {app.installed && (
                <div className="mt-3 text-xs text-muted-foreground">
                  Status: <span className={app.running ? 'text-green-500' : 'text-muted-foreground'}>
                    {app.running ? 'Running' : 'Stopped'}
                  </span>
                  {app.version && <> | v{app.version}</>}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default AppStore
