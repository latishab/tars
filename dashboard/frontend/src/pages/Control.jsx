import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight,
  Hand, Smile, Frown, Meh, Zap, RotateCcw, Camera
} from 'lucide-react'

const EMOTIONS = ['neutral', 'happy', 'sad', 'angry', 'excited', 'afraid', 'sleepy', 'sideeye_left', 'sideeye_right', 'curious', 'skeptical', 'smug', 'surprised']
const EMOTION_LABELS = {
  'neutral': 'Neutral',
  'happy': 'Happy',
  'sad': 'Sad',
  'angry': 'Angry',
  'excited': 'Excited',
  'sleepy': 'Sleepy',
  'afraid': 'Afraid',
  'sideeye_left': 'Side Eye L',
  'sideeye_right': 'Side Eye R',
  'curious': 'Curious',
  'skeptical': 'Skeptical',
  'smug': 'Smug',
  'surprised': 'Surprised'
}

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
    { name: 'pose', label: 'Pose', icon: null },
    { name: 'laugh', label: 'Laugh', icon: Smile },
    { name: 'neutral_legs', label: 'Neutral', icon: null },
  ],
  balance: [
    { name: 'tilt_left', label: 'Tilt L', icon: null },
    { name: 'tilt_right', label: 'Tilt R', icon: null },
    { name: 'side_side', label: 'Side-Side', icon: null },
    { name: 'swing_legs', label: 'Swing', icon: null },
  ],
  quickGestures: [
    { name: 'Tilt R Fast', label: 'Tilt R Fast', icon: null },
    { name: 'Tilt L Fast', label: 'Tilt L Fast', icon: null },
    { name: 'Wiggle', label: 'Wiggle', icon: null },
    { name: 'Wave Fast', label: 'Wave Fast', icon: null },
  ],
}

function Control() {
  const [executing, setExecuting] = useState(null)
  const [cameraUrl, setCameraUrl] = useState(null)
  const [emotion, setEmotion] = useState('neutral')
  const [eyeState, setEyeState] = useState('idle')
  const [savedSequences, setSavedSequences] = useState({})
  const [sequencePlaying, setSequencePlaying] = useState(false)
  const [expressionMap, setExpressionMap] = useState({})
  const [activeExpression, setActiveExpression] = useState(null)

  useEffect(() => {
    fetch('/api/control/saved-sequences')
      .then(r => r.json())
      .then(setSavedSequences)
      .catch(() => {})
    fetch('/api/expressions/map')
      .then(r => r.json())
      .then(data => setExpressionMap(data.map || {}))
      .catch(() => {})
  }, [])

  const playSaved = async (name) => {
    setSequencePlaying(true)
    try {
      await fetch(`/api/control/play-saved/${encodeURIComponent(name)}`, { method: 'POST' })
    } catch (err) {
      console.error('play-saved failed:', err)
    }
    setSequencePlaying(false)
  }

  const getSeqType = (entry) =>
    entry && typeof entry === 'object' && !Array.isArray(entry) ? (entry.type || 'movement') : 'movement'

  const normalize = (s) => s.toLowerCase().replace(/[_\s]/g, '')

  const executeMovement = async (movement) => {
    setExecuting(movement)
    try {
      await fetch('/api/control/move', {
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
      await fetch('/api/control/emotion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotion: newEmotion }),
      })
      setEmotion(newEmotion)
    } catch (err) {
      console.error('Set emotion failed:', err)
    }
  }

  const setEyeStateApi = async (state) => {
    try {
      await fetch('/api/control/eye-state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state }),
      })
      setEyeState(state)
    } catch (err) {
      console.error('Set eye state failed:', err)
    }
  }

  const captureCamera = () => {
    setCameraUrl(`/api/status/camera?t=${Date.now()}`)
  }

  const resetPosition = async () => {
    setExecuting('reset')
    try {
      await fetch('/api/control/reset', { method: 'POST' })
    } catch (err) {
      console.error('Reset failed:', err)
    }
    setExecuting(null)
  }

  const triggerExpression = async (emotion, intensity) => {
    const key = `${emotion}:${intensity}`
    setActiveExpression(key)
    try {
      await fetch('/api/expressions/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotion, intensity }),
      })
    } catch (err) {
      console.error('Expression trigger failed:', err)
    }
  }

  const overrideMap = Object.fromEntries(
    Object.keys(savedSequences).map(k => [normalize(k), k])
  )
  // Also build a label-based lookup so saved sequences match button labels too
  const allMovements = Object.values(MOVEMENT_GROUPS).flat()
  const labelOverrideMap = Object.fromEntries(
    allMovements
      .map(m => {
        const match = Object.keys(savedSequences).find(k => normalize(k) === normalize(m.label))
        return match ? [m.name, match] : null
      })
      .filter(Boolean)
  )
  // Sequences that override a preexisting button shouldn't appear in Custom Sequences
  const buttonNamesNormalized = new Set(allMovements.map(m => normalize(m.name)))
  const isButtonOverride = (name) => buttonNamesNormalized.has(normalize(name))

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Control</h1>

      {/* Camera + Emotions - Stack on mobile, 40/60 split on desktop */}
      <div className="grid grid-cols-1 md:grid-cols-[2fr,3fr] gap-4">
        {/* Camera - 40% on desktop */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Camera className="w-4 h-4" />
                Camera
              </span>
              <Button size="sm" variant="outline" onClick={captureCamera}>
                Capture
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            {cameraUrl ? (
              <img
                src={cameraUrl}
                alt="Camera"
                className="w-full aspect-square object-cover rounded-lg bg-muted"
                onError={() => setCameraUrl(null)}
              />
            ) : (
              <div className="w-full aspect-square bg-muted rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                Click Capture
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right column: Eye State + Emotions stacked */}
        <div className="flex flex-col gap-4">
          {/* Eye State */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Eye State</CardTitle>
            </CardHeader>
            <CardContent className="pb-3">
              <div className="grid grid-cols-4 gap-2">
                {['idle', 'listening', 'thinking', 'speaking'].map((s) => (
                  <Button
                    key={s}
                    variant={eyeState === s ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setEyeStateApi(s)}
                    className="h-9 text-xs capitalize"
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Emotions */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Emotion</CardTitle>
            </CardHeader>
            <CardContent className="pb-3">
              <div className="grid grid-cols-2 gap-2">
                {EMOTIONS.map((e) => (
                  <Button
                    key={e}
                    variant={emotion === e ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setEmotionApi(e)}
                    className="h-10 text-xs"
                  >
                    {EMOTION_LABELS[e] || e}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Expressions Quick Access */}
      {Object.keys(expressionMap).filter(k => expressionMap[k]?.gesture).length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Expressions</span>
              <Link to="/expressions" className="text-xs text-muted-foreground hover:text-foreground">
                All Expressions →
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {Object.entries(expressionMap)
                .filter(([, entry]) => entry?.gesture)
                .map(([key]) => {
                  const [emotion, intensity] = key.split(':')
                  const label = `${emotion.charAt(0).toUpperCase() + emotion.slice(1).replace('_', ' ')} (${intensity})`
                  return (
                    <Button
                      key={key}
                      variant={activeExpression === key ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => triggerExpression(emotion, intensity)}
                      className="h-9 text-xs"
                    >
                      {label}
                    </Button>
                  )
                })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Movement Controls - Full width */}
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
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.walking.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => { const ov = overrideMap[normalize(m.name)] || labelOverrideMap[m.name]; ov ? playSaved(ov) : executeMovement(m.name) }}
                  disabled={executing !== null}
                  className="flex flex-col h-16 sm:h-auto py-2"
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
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.turning.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => { const ov = overrideMap[normalize(m.name)] || labelOverrideMap[m.name]; ov ? playSaved(ov) : executeMovement(m.name) }}
                  disabled={executing !== null}
                  className="flex flex-col h-16 sm:h-auto py-2"
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
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {MOVEMENT_GROUPS.expressions.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => { const ov = overrideMap[normalize(m.name)] || labelOverrideMap[m.name]; ov ? playSaved(ov) : executeMovement(m.name) }}
                  disabled={executing !== null}
                  className="flex flex-col h-16 sm:h-auto py-2"
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
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.balance.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => { const ov = overrideMap[normalize(m.name)] || labelOverrideMap[m.name]; ov ? playSaved(ov) : executeMovement(m.name) }}
                  disabled={executing !== null}
                  className="flex flex-col h-16 sm:h-auto py-2"
                >
                  <span className="text-xs">{m.label}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Quick Gestures */}
          <div>
            <div className="text-sm text-muted-foreground mb-2">Quick Gestures</div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {MOVEMENT_GROUPS.quickGestures.map((m) => (
                <Button
                  key={m.name}
                  variant="outline"
                  size="sm"
                  onClick={() => { const ov = overrideMap[normalize(m.name)] || labelOverrideMap[m.name]; ov ? playSaved(ov) : executeMovement(m.name) }}
                  disabled={executing !== null}
                  className="flex flex-col h-16 sm:h-auto py-2"
                >
                  <span className="text-xs">{m.label}</span>
                </Button>
              ))}
            </div>
          </div>

        </CardContent>
      </Card>

      {/* Custom Sequences (all saved sequences, excluding button overrides) */}
      {Object.entries(savedSequences).some(([name, entry]) => !isButtonOverride(name)) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Custom Sequences</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(savedSequences).some(([name, entry]) => getSeqType(entry) === 'expression' && entry.quick && !isButtonOverride(name)) && (
              <div>
                <div className="text-sm text-muted-foreground mb-2">Quick Expressions</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(savedSequences)
                    .filter(([name, entry]) => getSeqType(entry) === 'expression' && entry.quick && !isButtonOverride(name))
                    .map(([name]) => (
                      <Button
                        key={name}
                        variant="outline"
                        size="sm"
                        onClick={() => playSaved(name)}
                        disabled={executing !== null || sequencePlaying}
                        className="flex flex-col h-16 sm:h-auto py-2"
                      >
                        <span className="text-xs">{name}</span>
                      </Button>
                    ))}
                </div>
              </div>
            )}
            {Object.entries(savedSequences).some(([name, entry]) => getSeqType(entry) === 'expression' && !entry.quick && !isButtonOverride(name)) && (
              <div>
                <div className="text-sm text-muted-foreground mb-2">Expressions</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(savedSequences)
                    .filter(([name, entry]) => getSeqType(entry) === 'expression' && !entry.quick && !isButtonOverride(name))
                    .map(([name]) => (
                      <Button
                        key={name}
                        variant="outline"
                        size="sm"
                        onClick={() => playSaved(name)}
                        disabled={executing !== null || sequencePlaying}
                        className="flex flex-col h-16 sm:h-auto py-2"
                      >
                        <span className="text-xs">{name}</span>
                      </Button>
                    ))}
                </div>
              </div>
            )}
            {Object.entries(savedSequences).some(([name, entry]) => getSeqType(entry) === 'movement' && !isButtonOverride(name)) && (
              <div>
                <div className="text-sm text-muted-foreground mb-2">Movements</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(savedSequences)
                    .filter(([name, entry]) => getSeqType(entry) === 'movement' && !isButtonOverride(name))
                    .map(([name]) => (
                      <Button
                        key={name}
                        variant="outline"
                        size="sm"
                        onClick={() => playSaved(name)}
                        disabled={sequencePlaying}
                        className="h-10"
                      >
                        {name}
                      </Button>
                    ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Control
