import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight,
  Hand, Smile, Frown, Meh, Zap, RotateCcw, Camera
} from 'lucide-react'

const EMOTIONS = ['neutral', 'happy', 'sad', 'angry', 'surprised', 'thinking']

const MOVEMENT_GROUPS = {
  walking: [
    { name: 'step_forward', label: 'Step Fwd', icon: ArrowUp },
    { name: 'step_backward', label: 'Step Back', icon: ArrowDown },
    { name: 'walk_forward', label: 'Walk Fwd', icon: ArrowUp },
    { name: 'walk_backward', label: 'Walk Back', icon: ArrowDown },
  ],
  turning: [
    { name: 'turn_left', label: 'Turn Left', icon: ArrowLeft },
    { name: 'turn_right', label: 'Turn Right', icon: ArrowRight },
    { name: 'turn_left_slow', label: 'Slow Left', icon: ArrowLeft },
    { name: 'turn_right_slow', label: 'Slow Right', icon: ArrowRight },
  ],
  expressions: [
    { name: 'wave_right', label: 'Wave R', icon: Hand },
    { name: 'wave_left', label: 'Wave L', icon: Hand },
    { name: 'bow', label: 'Bow', icon: null },
    { name: 'excited', label: 'Excited', icon: Zap },
    { name: 'laugh', label: 'Laugh', icon: Smile },
  ],
  balance: [
    { name: 'tilt_left', label: 'Tilt L', icon: null },
    { name: 'tilt_right', label: 'Tilt R', icon: null },
    { name: 'side_side', label: 'Side-Side', icon: null },
    { name: 'swing_legs', label: 'Swing', icon: null },
  ],
}

function Control() {
  const [executing, setExecuting] = useState(null)
  const [cameraUrl, setCameraUrl] = useState(null)
  const [emotion, setEmotion] = useState('neutral')

  const executeMovement = async (movement) => {
    setExecuting(movement)
    try {
      await fetch('/api/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movement }),
      })
    } catch (err) {
      console.error('Movement failed:', err)
    }
    setExecuting(null)
  }

  const setEmotionApi = async (newEmotion) => {
    try {
      await fetch('/api/emotion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotion: newEmotion }),
      })
      setEmotion(newEmotion)
    } catch (err) {
      console.error('Set emotion failed:', err)
    }
  }

  const captureCamera = () => {
    // Add timestamp to force refresh
    setCameraUrl(`/api/camera?t=${Date.now()}`)
  }

  const resetPosition = async () => {
    setExecuting('reset')
    try {
      await fetch('/api/reset', { method: 'POST' })
    } catch (err) {
      console.error('Reset failed:', err)
    }
    setExecuting(null)
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Control</h1>

      {/* Camera Preview */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Camera
            </span>
            <Button size="sm" variant="outline" onClick={captureCamera}>
              Capture
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {cameraUrl ? (
            <img
              src={cameraUrl}
              alt="Camera"
              className="w-full rounded-lg bg-muted"
              onError={() => setCameraUrl(null)}
            />
          ) : (
            <div className="w-full aspect-video bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
              Click Capture to view camera
            </div>
          )}
        </CardContent>
      </Card>

      {/* Emotions */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Emotion</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2">
            {EMOTIONS.map((e) => (
              <Button
                key={e}
                variant={emotion === e ? 'default' : 'outline'}
                size="sm"
                onClick={() => setEmotionApi(e)}
                className="capitalize"
              >
                {e}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Movement Controls */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>Movement</span>
            <Button
              size="sm"
              variant="outline"
              onClick={resetPosition}
              disabled={executing === 'reset'}
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              Reset
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Walking */}
          <div>
            <div className="text-sm text-muted-foreground mb-2">Walking</div>
            <div className="grid grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.walking.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => executeMovement(m.name)}
                  disabled={executing !== null}
                  className="flex flex-col h-auto py-2"
                >
                  {m.icon && <m.icon className="w-4 h-4 mb-1" />}
                  <span className="text-xs">{m.label}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Turning */}
          <div>
            <div className="text-sm text-muted-foreground mb-2">Turning</div>
            <div className="grid grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.turning.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => executeMovement(m.name)}
                  disabled={executing !== null}
                  className="flex flex-col h-auto py-2"
                >
                  {m.icon && <m.icon className="w-4 h-4 mb-1" />}
                  <span className="text-xs">{m.label}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Expressions */}
          <div>
            <div className="text-sm text-muted-foreground mb-2">Expressions</div>
            <div className="grid grid-cols-5 gap-2">
              {MOVEMENT_GROUPS.expressions.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => executeMovement(m.name)}
                  disabled={executing !== null}
                  className="flex flex-col h-auto py-2"
                >
                  {m.icon && <m.icon className="w-4 h-4 mb-1" />}
                  <span className="text-xs">{m.label}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Balance */}
          <div>
            <div className="text-sm text-muted-foreground mb-2">Balance</div>
            <div className="grid grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.balance.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => executeMovement(m.name)}
                  disabled={executing !== null}
                  className="flex flex-col h-auto py-2"
                >
                  <span className="text-xs">{m.label}</span>
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Control
