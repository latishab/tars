import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Play, Plus, X, Zap, Pencil, Download, RotateCcw, Trash2, GripVertical } from 'lucide-react'

const DEFAULT_STEP = () => ({ left_height: 50, right_height: 50, left_leg: 50, right_leg: 50, speed: 0.85, hold_time: 0 })

function PositionStepRow({ step, index, onUpdate, onDelete, onRelease, onGripPointerDown }) {
  const sliders = [
    { field: 'left_height', label: 'LH', min: 1, max: 100, step: 1, live: true },
    { field: 'right_height', label: 'RH', min: 1, max: 100, step: 1, live: true },
    { field: 'left_leg', label: 'LL', min: 1, max: 100, step: 1, live: true },
    { field: 'right_leg', label: 'RL', min: 1, max: 100, step: 1, live: true },
    { field: 'speed', label: 'Spd', min: 0.1, max: 1.0, step: 0.05, live: true },
    { field: 'hold_time', label: 'Hold', min: 0, max: 5, step: 0.1, live: false },
  ]
  return (
    <div className="flex items-start gap-2 p-2 bg-muted/30 rounded-lg">
      <div className="mt-1 cursor-grab active:cursor-grabbing text-muted-foreground shrink-0" onPointerDown={onGripPointerDown}>
        <GripVertical className="w-4 h-4" />
      </div>
      <div className="flex-1 grid grid-cols-3 sm:grid-cols-6 gap-x-3 gap-y-2">
        {sliders.map(({ field, label, min, max, step: stepVal, live }) => (
          <div key={field} className="flex flex-col gap-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{label}</span>
              <span className="font-mono">
                {field === 'speed' ? step[field].toFixed(2) : field === 'hold_time' ? step[field].toFixed(1) : step[field]}
              </span>
            </div>
            <input
              type="range" min={min} max={max} step={stepVal} value={step[field]}
              onChange={e => onUpdate(index, field, field === 'speed' || field === 'hold_time' ? parseFloat(e.target.value) : parseInt(e.target.value))}
              onMouseUp={live ? () => onRelease(step) : undefined}
              onTouchEnd={live ? () => onRelease(step) : undefined}
              className="w-full h-2 accent-primary cursor-pointer"
            />
          </div>
        ))}
      </div>
      <button onClick={() => onDelete(index)} className="mt-1 p-1 text-muted-foreground hover:text-destructive transition-colors">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

function MovementStepRow({ step, index, onDelete, onGripPointerDown }) {
  return (
    <div className="flex items-center gap-2 p-2 bg-muted/30 rounded-lg">
      <div className="cursor-grab active:cursor-grabbing text-muted-foreground shrink-0" onPointerDown={onGripPointerDown}>
        <GripVertical className="w-4 h-4" />
      </div>
      <Zap className="w-4 h-4 text-muted-foreground shrink-0" />
      <span className="flex-1 text-sm font-mono">{step.movement}</span>
      <button onClick={() => onDelete(index)} className="p-1 text-muted-foreground hover:text-destructive transition-colors">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

function SectionLabel({ children }) {
  return <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide pt-1">{children}</div>
}

const MOVEMENTS = [
  'step_forward', 'walk_forward', 'step_backward', 'walk_backward',
  'turn_right', 'turn_right_slow', 'turn_left', 'turn_left_slow',
  'pose', 'bow', 'tilt_right', 'tilt_left', 'side_side',
  'wave_right', 'wave_left', 'neutral_legs', 'excited', 'laugh', 'swing_legs',
  'tilt_quick_right', 'tilt_quick_left', 'wiggle', 'wave_short',
]

function MovementBuilder() {
  const [steps, setSteps] = useState([DEFAULT_STEP()])
  const [sequenceName, setSequenceName] = useState('')
  const [savedSequences, setSavedSequences] = useState({})
  const [sequencePlaying, setSequencePlaying] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [selectedMovement, setSelectedMovement] = useState(MOVEMENTS[0])
  const [importing, setImporting] = useState(false)
  const [livePreview, setLivePreview] = useState(false)
  const [confirmOverwrite, setConfirmOverwrite] = useState(false)
  const [seqType, setSeqType] = useState('movement')
  const [isQuick, setIsQuick] = useState(false)
  const dragIndex = useRef(null)
  const dragFromHandle = useRef(false)

  useEffect(() => { loadSavedSequences() }, [])

  const loadSavedSequences = () => {
    fetch('/api/control/saved-sequences').then(r => r.json()).then(setSavedSequences).catch(() => {})
  }

  const addPositionStep = () => setSteps(s => [...s, DEFAULT_STEP()])
  const addMovementStep = () => setSteps(s => [...s, { movement: selectedMovement, hold_time: 0 }])
  const deleteStep = (i) => setSteps(s => s.filter((_, idx) => idx !== i))
  const updateStep = (i, field, value) => setSteps(s => s.map((step, idx) => idx === i ? { ...step, [field]: value } : step))
  const resetSteps = () => { setSteps([DEFAULT_STEP()]); setSequenceName(''); setFeedback('') }

  const handleDragStart = (e, i) => {
    if (!dragFromHandle.current) { e.preventDefault(); return }
    dragIndex.current = i
  }
  const handleDragEnd = () => { dragFromHandle.current = false }
  const handleDragOver = (e) => { e.preventDefault() }
  const handleDrop = (i) => {
    const from = dragIndex.current
    if (from === null || from === i) return
    setSteps(s => {
      const arr = [...s]
      const [moved] = arr.splice(from, 1)
      arr.splice(i, 0, moved)
      return arr
    })
    dragIndex.current = null
  }

  const sendMoveLeg = async (step) => {
    if (!livePreview) return
    try {
      await fetch('/api/control/move-legs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ left_height: step.left_height, right_height: step.right_height, left_leg: step.left_leg, right_leg: step.right_leg, speed: step.speed }),
      })
    } catch (err) { console.error('move-legs failed:', err) }
  }

  const resetToNeutral = () => fetch('/api/control/move-legs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ left_height: 50, right_height: 50, left_leg: 50, right_leg: 50, speed: 0.8 }),
  }).catch(() => {})

  const playSequence = async () => {
    setSequencePlaying(true)
    setFeedback('')
    try {
      const res = await fetch('/api/control/play-sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps }),
      })
      setFeedback(res.ok ? 'Sequence complete' : `Error: ${(await res.json()).detail || res.statusText}`)
    } catch (err) { setFeedback(`Error: ${err.message}`) }
    setSequencePlaying(false)
  }

  const saveSequence = async () => {
    if (!sequenceName.trim()) { setFeedback('Enter a name before saving'); return }
    const name = sequenceName.trim()
    if (savedSequences[name] && !confirmOverwrite) {
      setConfirmOverwrite(true)
      return
    }
    setConfirmOverwrite(false)
    try {
      const res = await fetch('/api/control/save-sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, steps, type: seqType, quick: isQuick }),
      })
      if (res.ok) { setFeedback(`Saved "${name}"`); setSequenceName(''); loadSavedSequences() }
      else setFeedback('Save failed')
    } catch (err) { setFeedback(`Error: ${err.message}`) }
  }

  const playSaved = async (name) => {
    setSequencePlaying(true)
    setFeedback('')
    try {
      const res = await fetch(`/api/control/play-saved/${encodeURIComponent(name)}`, { method: 'POST' })
      setFeedback(res.ok ? `"${name}" complete` : `Error: ${(await res.json()).detail || res.statusText}`)
    } catch (err) { setFeedback(`Error: ${err.message}`) }
    setSequencePlaying(false)
  }

  const deleteSaved = async (name) => {
    try {
      await fetch(`/api/control/saved-sequences/${encodeURIComponent(name)}`, { method: 'DELETE' })
      loadSavedSequences()
    } catch (err) { console.error('Delete failed:', err) }
  }

  const loadIntoEditor = (name) => {
    const loaded = savedSequences[name]
    if (!loaded) return
    const steps = Array.isArray(loaded) ? loaded : (loaded.steps || [])
    const type = Array.isArray(loaded) ? 'movement' : (loaded.type || 'movement')
    setSteps(steps.map(s => s.movement
      ? { movement: s.movement, hold_time: s.hold_time ?? 0 }
      : { left_height: s.left_height, right_height: s.right_height, left_leg: s.left_leg, right_leg: s.right_leg, speed: s.speed, hold_time: s.hold_time ?? 0 }
    ))
    setSequenceName(name)
    setSeqType(type)
    setFeedback(`Loaded "${name}"`)
  }

  const importFromMovement = async (name) => {
    setImporting(true)
    setFeedback('')
    try {
      const res = await fetch(`/api/control/movement-steps/${encodeURIComponent(name)}`)
      if (res.ok) {
        const data = await res.json()
        setSteps(data.steps)
        setSequenceName('')
        setFeedback(`Imported "${name}" — edit then save under a new name`)
      } else {
        setFeedback(`Import failed: ${(await res.json()).detail}`)
      }
    } catch (err) { setFeedback(`Error: ${err.message}`) }
    setImporting(false)
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Movement Builder</h1>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center justify-between">
            <span>Sequence Editor</span>
            <button
              onClick={() => setLivePreview(v => !v)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${livePreview ? 'border-primary text-primary bg-primary/10' : 'border-input text-muted-foreground'}`}
            >
              {livePreview ? 'Live: on' : 'Live: off'}
            </button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">

          {/* Channel legend + safety note */}
          <div className="text-xs text-muted-foreground space-y-1">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-0.5 font-mono">
              <span><span className="text-foreground">LH</span> ch0 — left height</span>
              <span><span className="text-foreground">RH</span> ch1 — right height</span>
              <span><span className="text-foreground">LL</span> ch2 — left leg fwd/back</span>
              <span><span className="text-foreground">RL</span> ch3 — right leg fwd/back</span>
            </div>
            <p>Heights same direction (20,20 or 80,80) may tip. Tilts (35,65) are safer.</p>
          </div>

          {/* Steps list */}
          <div className="space-y-2">
            {steps.map((step, i) => (
              <div
                key={i}
                draggable
                onDragStart={(e) => handleDragStart(e, i)}
                onDragEnd={handleDragEnd}
                onDragOver={handleDragOver}
                onDrop={() => handleDrop(i)}
                className="cursor-default"
              >
                <div className="text-xs text-muted-foreground mb-1">Step {i + 1}</div>
                {step.movement
                  ? <MovementStepRow step={step} index={i} onDelete={deleteStep} onGripPointerDown={() => { dragFromHandle.current = true }} />
                  : <PositionStepRow step={step} index={i} onUpdate={updateStep} onDelete={deleteStep} onRelease={sendMoveLeg} onGripPointerDown={() => { dragFromHandle.current = true }} />
                }
              </div>
            ))}
          </div>

          {/* Add steps */}
          <div className="space-y-2">
            <SectionLabel>Add Steps</SectionLabel>
            <Button size="sm" variant="outline" onClick={addPositionStep} className="w-full">
              <Plus className="w-4 h-4 mr-1" />
              Add Position Step
            </Button>
            <div className="flex gap-1">
              <select
                value={selectedMovement}
                onChange={e => setSelectedMovement(e.target.value)}
                className="flex-1 h-9 rounded-md border border-input bg-background px-2 text-sm"
              >
                {MOVEMENTS.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
              <Button size="sm" variant="outline" onClick={addMovementStep} title="Append as named step">
                <Zap className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={() => importFromMovement(selectedMovement)} disabled={importing} title="Import as editable position steps">
                <Download className="w-4 h-4" />
              </Button>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground px-0.5">
              <span><Zap className="w-3 h-3 inline mr-1" />append as named step</span>
              <span><Download className="w-3 h-3 inline mr-1" />import as editable steps</span>
            </div>
          </div>

          {/* Playback */}
          <div className="space-y-2">
            <SectionLabel>Playback</SectionLabel>
            <div className="flex gap-2">
              <Button size="sm" onClick={playSequence} disabled={sequencePlaying} className="flex-1">
                <Play className="w-4 h-4 mr-1" />
                {sequencePlaying ? 'Playing...' : 'Play Sequence'}
              </Button>
              <Button size="sm" variant="outline" onClick={resetToNeutral} disabled={sequencePlaying}>
                <RotateCcw className="w-4 h-4 mr-1" />
                Neutral
              </Button>
            </div>
          </div>

          {/* Save */}
          <div className="space-y-2">
            <SectionLabel>Save</SectionLabel>
            <div className="flex gap-2">
              <Input
                placeholder="Sequence name"
                value={sequenceName}
                onChange={e => { setSequenceName(e.target.value); setConfirmOverwrite(false) }}
                className="flex-1 h-9 text-sm"
              />
              <select
                value={seqType}
                onChange={e => setSeqType(e.target.value)}
                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              >
                <option value="movement">Movement</option>
                <option value="expression">Expression</option>
              </select>
              <label className="flex items-center gap-1.5 text-sm cursor-pointer select-none whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={isQuick}
                  onChange={e => setIsQuick(e.target.checked)}
                  className="w-4 h-4 accent-primary"
                />
                Quick
              </label>
              <Button size="sm" onClick={saveSequence}>Save</Button>
              <Button size="sm" variant="outline" onClick={resetSteps} title="Clear all steps">
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
            {confirmOverwrite && (
              <div className="flex items-center gap-2 p-2 rounded-md bg-muted text-sm">
                <span className="flex-1 text-muted-foreground">"{sequenceName}" already exists. Replace?</span>
                <Button size="sm" variant="destructive" onClick={saveSequence}>Replace</Button>
                <Button size="sm" variant="outline" onClick={() => setConfirmOverwrite(false)}>Cancel</Button>
              </div>
            )}
          </div>

          {/* Feedback */}
          {feedback && <p className="text-sm text-muted-foreground">{feedback}</p>}

          {/* Saved sequences */}
          {Object.keys(savedSequences).length > 0 && (
            <div className="space-y-2">
              <SectionLabel>Saved Sequences</SectionLabel>
              <div className="flex flex-wrap gap-2">
                {Object.keys(savedSequences).map(name => (
                  <div key={name} className="flex items-center gap-1 bg-muted rounded-md px-2 py-1">
                    <button onClick={() => playSaved(name)} disabled={sequencePlaying} className="text-sm hover:text-primary transition-colors disabled:opacity-50">
                      {name}
                    </button>
                    <button onClick={() => loadIntoEditor(name)} title="Load into editor" className="text-muted-foreground hover:text-primary transition-colors">
                      <Pencil className="w-3 h-3" />
                    </button>
                    <button onClick={() => deleteSaved(name)} className="text-muted-foreground hover:text-destructive transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

        </CardContent>
      </Card>
    </div>
  )
}

export default MovementBuilder
