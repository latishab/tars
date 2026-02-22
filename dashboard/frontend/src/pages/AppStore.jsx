import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Download, Trash2, Play, Square, CheckCircle, ExternalLink } from 'lucide-react'

function AppStore() {
  const [officialApps, setOfficialApps] = useState([])
  const [communityApps, setCommunityApps] = useState([])
  const [loading, setLoading] = useState({})
  const [error, setError] = useState(null)

  const fetchApps = async () => {
    try {
      const res = await fetch('/api/apps')
      const data = await res.json()
      
      setOfficialApps(data.official || [])
      setCommunityApps(data.community || [])
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

  const AppCard = ({ app }) => (
    <div className="p-4 border border-border rounded-lg h-full flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-sm truncate">{app.name}</h3>
            {app.installed && (
              <CheckCircle className="w-3 h-3 text-green-500 flex-shrink-0" />
            )}
          </div>
        </div>
      </div>

      <p className="text-xs text-muted-foreground mb-2 line-clamp-2 flex-1">
        {app.description}
      </p>

      <div className="text-xs text-muted-foreground mb-3">
        by {app.author}
      </div>

      <div className="flex items-center gap-2 flex-wrap mt-auto">
        {!app.installed ? (
          <>
            <Button
              onClick={() => handleInstall(app)}
              disabled={loading[`install-${app.id}`]}
              size="sm"
              className="text-xs h-8"
            >
              <Download className="w-3 h-3 mr-1" />
              {loading[`install-${app.id}`] ? 'Installing...' : 'Install'}
            </Button>
            {app.url && (
              <Button
                onClick={() => window.open(app.url, '_blank')}
                size="sm"
                variant="outline"
                className="text-xs h-8"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                View
              </Button>
            )}
          </>
        ) : (
          <>
            {!app.running ? (
              <Button
                onClick={() => handleRun(app.id)}
                disabled={loading[`run-${app.id}`]}
                size="sm"
                variant="default"
                className="text-xs h-8"
              >
                <Play className="w-3 h-3 mr-1" />
                {loading[`run-${app.id}`] ? 'Starting...' : 'Run'}
              </Button>
            ) : (
              <Button
                onClick={() => handleStop(app.id)}
                disabled={loading[`stop-${app.id}`]}
                size="sm"
                variant="secondary"
                className="text-xs h-8"
              >
                <Square className="w-3 h-3 mr-1" />
                {loading[`stop-${app.id}`] ? 'Stopping...' : 'Stop'}
              </Button>
            )}
            <Button
              onClick={() => handleUninstall(app.id)}
              disabled={loading[`uninstall-${app.id}`]}
              size="sm"
              variant="outline"
              className="text-xs h-8"
            >
              <Trash2 className="w-3 h-3 mr-1" />
              Uninstall
            </Button>
            {app.url && (
              <Button
                onClick={() => window.open(app.url, '_blank')}
                size="sm"
                variant="outline"
                className="text-xs h-8"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                View
              </Button>
            )}
          </>
        )}
        {app.installed && app.version && (
          <span className="text-xs text-muted-foreground ml-auto">
            v{app.version}
          </span>
        )}
      </div>
    </div>
  )

  const PlaceholderCard = () => (
    <div className="p-4 border-2 border-dashed border-border rounded-lg h-full flex items-center justify-center">
      <p className="text-xs text-muted-foreground">More coming soon</p>
    </div>
  )

  const renderGrid = (apps) => {
    const items = [...apps]
    // Fill up to 4 items (2x2 grid)
    while (items.length < 4) {
      items.push(null)
    }
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {items.map((app, idx) => 
          app ? <AppCard key={app.id} app={app} /> : <PlaceholderCard key={`placeholder-${idx}`} />
        )}
      </div>
    )
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

      {/* Official Apps */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Official Apps</CardTitle>
          <CardDescription>
            Verified apps maintained by the TARS team
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderGrid(officialApps)}
        </CardContent>
      </Card>

      {/* Community Apps */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Community Apps</CardTitle>
          <CardDescription>
            Apps created by the TARS community
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderGrid(communityApps)}
        </CardContent>
      </Card>
    </div>
  )
}

export default AppStore
