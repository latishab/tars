import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Pencil, X, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'

const EMOTIONS = [
  'neutral', 'happy', 'sad', 'angry', 'excited', 'afraid',
  'sleepy', 'sideeye_left', 'sideeye_right', 'curious', 'skeptical', 'smug', 'surprised'
]

const EMOTION_LABELS = {
  neutral: 'Neutral', happy: 'Happy', sad: 'Sad', angry: 'Angry',
  excited: 'Excited', sleepy: 'Sleepy', afraid: 'Afraid',
  sideeye_left: 'Side Eye L', sideeye_right: 'Side Eye R',
  curious: 'Curious', skeptical: 'Skeptical', smug: 'Smug', surprised: 'Surprised'
}

const INTENSITIES = ['low', 'medium', 'high']

// SVG eye simulation parameters per emotion
// openL/R: eye openness (1.0 = normal, >1.0 = wide, <1.0 = narrow)
// lookX: horizontal look direction (-1 left, +1 right)
// lidL/R: top lid coverage as fraction of eye height (0 = none)
// lidSideL/R: 'flat' | 'left' | 'right' — which corner of the triangular lid droops
// curveL/R: bottom curved lid amount for happy/smug (0 = none, ~0.5 = full smile)
// color: eye fill color
const EYE_PARAMS = {
  neutral:       { openL: 1.0,  openR: 1.0,  lookX: 0,    lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#00CED1' },
  happy:         { openL: 0.85, openR: 0.85, lookX: 0,    lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0.48, curveR: 0.48, color: '#00CED1' },
  sad:           { openL: 0.8,  openR: 0.8,  lookX: 0,    lidL: 0.3,  lidR: 0.3,  lidSideL: 'left',  lidSideR: 'right', curveL: 0,    curveR: 0,    color: '#00CED1' },
  angry:         { openL: 1.0,  openR: 1.0,  lookX: 0,    lidL: 0.4,  lidR: 0.4,  lidSideL: 'right', lidSideR: 'left',  curveL: 0,    curveR: 0,    color: '#FF4500' },
  excited:       { openL: 1.0,  openR: 1.0,  lookX: 0,    lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0.48, curveR: 0.48, color: '#00CED1' },
  afraid:        { openL: 0.8,  openR: 0.8,  lookX: 0,    lidL: 0.3,  lidR: 0.3,  lidSideL: 'left',  lidSideR: 'right', curveL: 0,    curveR: 0,    color: '#00CED1' },
  sleepy:        { openL: 0.12, openR: 0.12, lookX: 0,    lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#00CED1' },
  sideeye_left:  { openL: 1.3,  openR: 0.8,  lookX: -0.9, lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#00CED1' },
  sideeye_right: { openL: 0.8,  openR: 1.3,  lookX: 0.9,  lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#00CED1' },
  curious:       { openL: 1.2,  openR: 0.85, lookX: -0.2, lidL: 0,    lidR: 0.12, lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#00CED1' },
  skeptical:     { openL: 0.6,  openR: 0.6,  lookX: 0,    lidL: 0.25, lidR: 0.25, lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#00CED1' },
  smug:          { openL: 0.7,  openR: 0.7,  lookX: 0,    lidL: 0.12, lidR: 0.12, lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0.25, curveR: 0.25, color: '#00CED1' },
  surprised:     { openL: 1.35, openR: 1.35, lookX: 0,    lidL: 0,    lidR: 0,    lidSideL: 'flat',  lidSideR: 'flat',  curveL: 0,    curveR: 0,    color: '#FFFFFF' },
}

const BG = '#0D1117'
const EW = 44   // eye width
const EH = 64   // eye base height
const R  = 10   // border radius

function Eye({ cx, cy, open, lid, lidSide, curve, color, lookX }) {
  const eh = Math.max(4, EH * open)
  const er = Math.min(R, EW / 2, eh / 2)
  const lx = lookX * EW * 0.22
  const ex = cx - EW / 2 + lx
  const ey = cy - eh / 2
  const lidPx = eh * lid
  // Curved bottom lid path (happy/smug)
  const curveH = eh * 0.5 * curve
  const curveY = ey + eh * 0.75
  const curvePath = curve > 0.01
    ? `M ${ex},${curveY} Q ${cx + lx},${curveY - curveH} ${ex + EW},${curveY} L ${ex + EW},${ey + eh + 4} L ${ex},${ey + eh + 4} Z`
    : null
  // Top lid polygon points
  let lidPoints = null
  if (lidPx > 0.5) {
    if (lidSide === 'left')
      lidPoints = `${ex},${ey - 1} ${ex + EW},${ey - 1} ${ex},${ey + lidPx}`
    else if (lidSide === 'right')
      lidPoints = `${ex},${ey - 1} ${ex + EW},${ey - 1} ${ex + EW},${ey + lidPx}`
    else
      lidPoints = `${ex},${ey - 1} ${ex + EW},${ey - 1} ${ex + EW},${ey + lidPx} ${ex},${ey + lidPx}`
  }
  return (
    <g>
      <rect x={ex} y={ey} width={EW} height={eh} rx={er} ry={er} fill={color} />
      {lidPoints && <polygon points={lidPoints} fill={BG} />}
      {curvePath && <path d={curvePath} fill={BG} />}
    </g>
  )
}

function EyePreview({ emotion }) {
  const p = EYE_PARAMS[emotion] || EYE_PARAMS.neutral
  return (
    <svg viewBox="0 0 200 90" width="200" height="90" style={{ background: BG, borderRadius: 8 }}>
      <Eye cx={55}  cy={45} open={p.openL} lid={p.lidL} lidSide={p.lidSideL} curve={p.curveL} color={p.color} lookX={p.lookX} />
      <Eye cx={145} cy={45} open={p.openR} lid={p.lidR} lidSide={p.lidSideR} curve={p.curveR} color={p.color} lookX={p.lookX} />
    </svg>
  )
}

export default function Expressions() {
  const [expressionMap, setExpressionMap] = useState({})
  const [customKeys, setCustomKeys] = useState([])
  const [gestures, setGestures] = useState([])
  const [activeCell, setActiveCell] = useState(null)
  const [editingCell, setEditingCell] = useState(null)
  const [editEyes, setEditEyes] = useState('')
  const [editGesture, setEditGesture] = useState('')
  const [executing, setExecuting] = useState(null)

  const fetchMap = () => {
    fetch('/api/expressions/map')
      .then(r => r.json())
      .then(data => {
        setExpressionMap(data.map || {})
        setCustomKeys(data.custom_keys || [])
      })
      .catch(() => {})
  }

  useEffect(() => {
    fetchMap()
    fetch('/api/expressions/gestures')
      .then(r => r.json())
      .then(data => setGestures(data.gestures || []))
      .catch(() => {})
  }, [])

  const trigger = async (emotion, intensity) => {
    const key = `${emotion}:${intensity}`
    setExecuting(key)
    try {
      const res = await fetch('/api/expressions/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotion, intensity }),
      })
      if (res.ok) setActiveCell(key)
    } catch (err) {
      console.error('Trigger failed:', err)
    }
    setExecuting(null)
  }

  const openEditor = (emotion, intensity) => {
    const key = `${emotion}:${intensity}`
    const entry = expressionMap[key]
    setEditingCell(key)
    setEditEyes(entry?.eyes || emotion)
    setEditGesture(entry?.gesture || '')
  }

  const saveEdit = async () => {
    if (!editingCell) return
    const entry = { eyes: editEyes }
    if (editGesture) entry.gesture = editGesture
    await fetch('/api/expressions/map', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries: { [editingCell]: entry } }),
    })
    fetchMap()
    setEditingCell(null)
  }

  const resetEntry = async () => {
    if (!editingCell) return
    const [emotion, intensity] = editingCell.split(':')
    await fetch(`/api/expressions/map/${emotion}/${intensity}`, { method: 'DELETE' })
    fetchMap()
    setEditingCell(null)
  }

  // Active emotion for eye preview: show eyes of the edited/triggered cell
  const previewEmotion = editingCell
    ? (expressionMap[editingCell]?.eyes || editingCell.split(':')[0])
    : activeCell
      ? (expressionMap[activeCell]?.eyes || activeCell.split(':')[0])
      : 'neutral'

  return (
    <div className="p-4 space-y-4">

      {/* Header with eye preview */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Expressions</h1>
          {activeCell && (
            <p className="text-sm text-muted-foreground mt-0.5">
              Active: <span className="text-foreground font-medium">{activeCell.replace(':', ' / ')}</span>
            </p>
          )}
        </div>
        <div className="shrink-0">
          <EyePreview emotion={previewEmotion} />
          <p className="text-xs text-center text-muted-foreground mt-1">{EMOTION_LABELS[previewEmotion] || previewEmotion}</p>
        </div>
      </div>

      {/* Expression Grid */}
      <Card>
        <CardContent className="p-3">
          <div className="grid grid-cols-[80px,1fr,1fr,1fr] gap-1 mb-1">
            <div />
            {INTENSITIES.map(i => (
              <div key={i} className="text-xs text-center text-muted-foreground font-medium capitalize pb-1">{i}</div>
            ))}
          </div>
          <div className="space-y-1">
            {EMOTIONS.map(emotion => (
              <div key={emotion} className="grid grid-cols-[80px,1fr,1fr,1fr] gap-1 items-center">
                <div className="text-xs text-muted-foreground truncate pr-1">{EMOTION_LABELS[emotion]}</div>
                {INTENSITIES.map(intensity => {
                  const key = `${emotion}:${intensity}`
                  const entry = expressionMap[key]
                  const hasGesture = !!entry?.gesture
                  const isCustom = customKeys.includes(key)
                  const isActive = activeCell === key
                  const isExecuting = executing === key
                  // Show first word of gesture name, or 'eyes', or '—'
                  const label = isExecuting ? '...' : entry
                    ? (entry.gesture ? entry.gesture.split(' ')[0] : 'eyes')
                    : '—'
                  return (
                    <div key={intensity} className="relative group">
                      <Button
                        variant={isActive ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => trigger(emotion, intensity)}
                        disabled={isExecuting}
                        className={cn(
                          'w-full h-8 text-xs px-1',
                          hasGesture && !isActive && 'border-l-2 border-l-primary',
                          isCustom && !isActive && 'ring-1 ring-amber-500',
                        )}
                      >
                        {label}
                      </Button>
                      <button
                        onClick={() => openEditor(emotion, intensity)}
                        className="absolute -top-1 -right-1 hidden group-hover:flex items-center justify-center w-4 h-4 rounded-full bg-muted border border-border text-muted-foreground hover:text-foreground z-10"
                      >
                        <Pencil className="w-2 h-2" />
                      </button>
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Editor */}
      {editingCell && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Edit: <span className="font-normal text-muted-foreground">{editingCell.replace(':', ' / ')}</span></span>
              <Button variant="ghost" size="icon" className="w-6 h-6" onClick={() => setEditingCell(null)}>
                <X className="w-4 h-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pb-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Eyes</label>
                <Select value={editEyes} onValueChange={setEditEyes}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EMOTIONS.map(e => (
                      <SelectItem key={e} value={e}>{EMOTION_LABELS[e]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground">Gesture</label>
                <Select value={editGesture || '__none__'} onValueChange={v => setEditGesture(v === '__none__' ? '' : v)}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None</SelectItem>
                    {gestures.map(g => (
                      <SelectItem key={g} value={g}>{g}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={saveEdit} className="flex-1">Save</Button>
              {customKeys.includes(editingCell) && (
                <Button size="sm" variant="outline" onClick={resetEntry}>
                  <RotateCcw className="w-3 h-3 mr-1" />
                  Reset
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
