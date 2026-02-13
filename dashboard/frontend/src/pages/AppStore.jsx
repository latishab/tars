import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, Github, MessageSquare, ExternalLink } from 'lucide-react'

function AppStore() {
  const apps = [
    {
      id: 'tars-conversation-app',
      name: 'TARS Conversation App',
      description: 'Desktop application for voice conversations with TARS. Features real-time audio streaming, push-to-talk, and seamless integration with your TARS robot.',
      icon: MessageSquare,
      github: 'https://github.com/latishab/tars-conversation-app',
      downloads: [
        {
          platform: 'macOS',
          label: 'Download for macOS',
          url: 'https://github.com/latishab/tars-conversation-app/releases/latest/download/tars-conversation-app-macos.dmg',
        },
        {
          platform: 'Windows',
          label: 'Download for Windows',
          url: 'https://github.com/latishab/tars-conversation-app/releases/latest/download/tars-conversation-app-windows.exe',
        },
        {
          platform: 'Linux',
          label: 'Download for Linux',
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
      tags: ['Voice', 'AI', 'Desktop'],
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

      <div className="grid gap-6">
        {apps.map((app) => (
          <Card key={app.id} className="border-border/50 hover:border-primary/50 transition-colors">
            <CardHeader className="pb-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                  <app.icon className="w-8 h-8 text-primary" />
                </div>
                <div className="flex-1">
                  <CardTitle className="text-2xl mb-2">{app.name}</CardTitle>
                  <CardDescription className="text-base">
                    {app.description}
                  </CardDescription>
                  <div className="flex gap-2 mt-3">
                    {app.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Features */}
              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground">
                  Features
                </h3>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {app.features.map((feature) => (
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
                  {app.downloads.map((download) => (
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
                    href={app.github}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Github className="w-4 h-4 mr-2" />
                    View on GitHub
                  </a>
                </Button>
                <Button variant="ghost" size="sm" asChild>
                  <a
                    href={`${app.github}/releases`}
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
        ))}
      </div>

      {/* Coming Soon */}
      <Card className="border-dashed">
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">
            More apps coming soon. Check back later!
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default AppStore
