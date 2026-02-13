import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, Github, MessageSquare, ExternalLink, X, ChevronDown } from 'lucide-react'

function AppStore() {
  const [selectedApp, setSelectedApp] = useState(null)
  const [expandedApp, setExpandedApp] = useState(null)

  const apps = [
    {
      id: 'tars-conversation-app',
      name: 'TARS Conversation',
      description: 'Voice conversations with TARS using real-time audio streaming and push-to-talk.',
      icon: MessageSquare,
      github: 'https://github.com/latishab/tars-conversation-app',
      downloads: [
        {
          platform: 'macOS',
          url: 'https://github.com/latishab/tars-conversation-app/releases/latest/download/tars-conversation-app-macos.dmg',
        },
        {
          platform: 'Windows',
          url: 'https://github.com/latishab/tars-conversation-app/releases/latest/download/tars-conversation-app-windows.exe',
        },
        {
          platform: 'Linux',
          url: 'https://github.com/latishab/tars-conversation-app/releases/latest/download/tars-conversation-app-linux.AppImage',
        },
      ],
      features: [
        'Real-time voice conversations',
        'Push-to-talk or voice activation',
        'WebRTC audio streaming',
        'Automatic TARS discovery',
        'Cross-platform support',
      ],
      tags: ['Voice', 'AI'],
    },
  ]

  return (
    <div className="container max-w-7xl mx-auto p-4 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">App Store</h1>
          <p className="text-muted-foreground mt-1">
            Extend TARS with powerful applications
          </p>
        </div>
      </div>

      {/* Official Apps Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold">Official Apps</h2>
          <Badge variant="default" className="text-xs">
            {apps.length}
          </Badge>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {apps.map((app) => (
            <Card
              key={app.id}
              className="border-border/50 hover:border-primary/50 transition-all"
            >
              <CardHeader className="pb-3">
                <div className="flex flex-col items-center text-center gap-3">
                  <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20">
                    <app.icon className="w-8 h-8 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-base leading-tight">
                      {app.name}
                    </CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                <p className="text-xs text-muted-foreground text-center line-clamp-2">
                  {app.description}
                </p>
                <div className="flex gap-1 justify-center flex-wrap">
                  {app.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs px-2 py-0">
                      {tag}
                    </Badge>
                  ))}
                </div>

                {/* Install Dropdown */}
                <div className="relative">
                  <Button
                    className="w-full"
                    size="sm"
                    onClick={() => setExpandedApp(expandedApp === app.id ? null : app.id)}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Install
                    <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${expandedApp === app.id ? 'rotate-180' : ''}`} />
                  </Button>

                  {expandedApp === app.id && (
                    <div className="absolute top-full left-0 right-0 mt-2 z-10">
                      <Card className="border-border/50 shadow-lg">
                        <CardContent className="p-2 space-y-1">
                          {app.downloads.map((download) => (
                            <Button
                              key={download.platform}
                              variant="ghost"
                              size="sm"
                              className="w-full justify-start"
                              asChild
                            >
                              <a
                                href={download.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <Download className="w-4 h-4 mr-2" />
                                {download.platform}
                              </a>
                            </Button>
                          ))}
                          <div className="pt-1 border-t border-border/50">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full justify-start text-xs"
                              onClick={() => setSelectedApp(app)}
                            >
                              <ExternalLink className="w-3 h-3 mr-2" />
                              View Details
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Coming Soon placeholder cards */}
          {[...Array(7)].map((_, i) => (
            <Card
              key={`coming-${i}`}
              className="border-dashed border-border/50 opacity-50"
            >
              <CardContent className="flex items-center justify-center h-full min-h-[250px]">
                <p className="text-xs text-muted-foreground text-center">
                  Coming Soon
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* App Detail Modal */}
      {selectedApp && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedApp(null)}
        >
          <Card
            className="w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                    <selectedApp.icon className="w-8 h-8 text-primary" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-2xl mb-2">
                      {selectedApp.name}
                    </CardTitle>
                    <CardDescription className="text-base">
                      {selectedApp.description}
                    </CardDescription>
                    <div className="flex gap-2 mt-3">
                      {selectedApp.tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedApp(null)}
                  className="h-8 w-8 ml-2"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Features */}
              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground">
                  Features
                </h3>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {selectedApp.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-center gap-2 text-sm"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Downloads */}
              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground">
                  Downloads
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {selectedApp.downloads.map((download) => (
                    <Button
                      key={download.platform}
                      variant="outline"
                      className="h-auto py-4 flex-col gap-2"
                      asChild
                    >
                      <a
                        href={download.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Download className="w-5 h-5" />
                        <div className="text-center">
                          <div className="font-semibold">
                            {download.platform}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Latest Release
                          </div>
                        </div>
                      </a>
                    </Button>
                  ))}
                </div>
              </div>

              {/* Links */}
              <div className="flex gap-3 pt-2 border-t border-border/50">
                <Button variant="ghost" size="sm" asChild>
                  <a
                    href={selectedApp.github}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Github className="w-4 h-4 mr-2" />
                    View on GitHub
                  </a>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <a
                    href={`${selectedApp.github}/releases`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    All Releases
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default AppStore
