import { useState, useEffect, useRef } from 'react'
import { Play, Plus, X, Zap, Pencil, Download, RotateCcw, GripVertical, Repeat2, Square } from 'lucide-react'
import TarsPreview from './TarsPreview'

const DEFAULT_STEP = () => ({ left_height: 50, right_height: 50, left_leg: 50, right_leg: 50, speed: 0.85, hold_time: 0 })
const DEFAULT_LOOP = () => ({ repeat: 2, steps: [DEFAULT_STEP()] })

// ── Servo slider field ─────────────────────────────────────────────────────
function ServoField({ field, label, min, max, step: stepVal, value, onChange, onRelease }) {
  const pct = ((value - min) / (max - min) * 100).toFixed(1)
  const displayVal = field === 'speed' ? value.toFixed(2) : field === 'hold_time' ? value.toFixed(1) : value
  return (
    <div className="servo-field">
      <div className="servo-meta">
        <span className="servo-label">{label}</span>
        <span className="servo-value">{displayVal}</span>
      </div>
      <input
        type="range" min={min} max={max} step={stepVal} value={value}
        style={{ '--pct': `${pct}%` }}
        onChange={e => onChange(field, field === 'speed' || field === 'hold_time' ? parseFloat(e.target.value) : parseInt(e.target.value))}
        onMouseUp={onRelease}
        onTouchEnd={onRelease}
        className="servo-slider"
      />
    </div>
  )
}

const SERVO_FIELDS = [
  { field: 'left_height',  label: 'LH', min: 1,   max: 100, step: 1,    live: true },
  { field: 'right_height', label: 'RH', min: 1,   max: 100, step: 1,    live: true },
  { field: 'left_leg',     label: 'LL', min: 1,   max: 100, step: 1,    live: true },
  { field: 'right_leg',    label: 'RL', min: 1,   max: 100, step: 1,    live: true },
  { field: 'speed',        label: 'SPD', min: 0.1, max: 1.0, step: 0.05, live: true },
  { field: 'hold_time',    label: 'HLD', min: 0,   max: 5.0, step: 0.1,  live: false },
]

function PositionStepRow({ step, index, onUpdate, onDelete, onRelease, onGripPointerDown }) {
  return (
    <div className="tars-step-row">
      <div className="tars-drag-handle" onPointerDown={onGripPointerDown}>
        <GripVertical size={14} />
      </div>
      <div className="servo-grid">
        {SERVO_FIELDS.map(({ field, label, min, max, step: sv }) => (
          <ServoField
            key={field}
            field={field} label={label} min={min} max={max} step={sv}
            value={step[field]}
            onChange={(f, v) => onUpdate(index, f, v)}
            onRelease={() => onRelease(step)}
          />
        ))}
      </div>
      <button onClick={() => onDelete(index)} style={{ marginTop: 2, padding: '2px 4px', color: 'hsl(214 14% 35%)', background: 'none', border: 'none', cursor: 'pointer' }}
        onMouseEnter={e => e.currentTarget.style.color = 'hsl(0 80% 60%)'}
        onMouseLeave={e => e.currentTarget.style.color = 'hsl(214 14% 35%)'}
      >
        <X size={13} />
      </button>
    </div>
  )
}

function MovementStepRow({ step, index, onDelete, onGripPointerDown }) {
  return (
    <div className="tars-movement-row">
      <div className="tars-drag-handle" onPointerDown={onGripPointerDown}>
        <GripVertical size={14} />
      </div>
      <Zap size={12} style={{ color: 'hsl(191 100% 44%)', flexShrink: 0 }} />
      <span style={{ flex: 1, fontSize: 11, letterSpacing: '0.06em', color: 'hsl(191 100% 60%)' }}>{step.movement}</span>
      <button onClick={() => onDelete(index)} style={{ padding: '2px 4px', color: 'hsl(214 14% 35%)', background: 'none', border: 'none', cursor: 'pointer' }}
        onMouseEnter={e => e.currentTarget.style.color = 'hsl(0 80% 60%)'}
        onMouseLeave={e => e.currentTarget.style.color = 'hsl(214 14% 35%)'}
      >
        <X size={13} />
      </button>
    </div>
  )
}

function LoopBlock({ loop, index, onUpdateRepeat, onUpdateInnerStep, onDeleteInnerStep, onAddInnerStep, onDelete, onGripPointerDown, onRelease }) {
  return (
    <div className="tars-loop-block">
      <div className="tars-loop-header">
        <div className="tars-drag-handle" onPointerDown={onGripPointerDown}>
          <GripVertical size={14} />
        </div>
        <span style={{ color: 'hsl(191 100% 50%)', fontSize: 13 }}>↺</span>
        <span style={{ fontSize: 9, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'hsl(191 100% 44% / 0.7)' }}>Loop</span>
        <input
          type="number" min={1} max={20} value={loop.repeat}
          onChange={e => onUpdateRepeat(index, Math.max(1, parseInt(e.target.value) || 1))}
          className="tars-num-input"
        />
        <span style={{ fontSize: 9, letterSpacing: '0.12em', color: 'hsl(191 100% 44% / 0.5)' }}>×</span>
        <button onClick={() => onDelete(index)} style={{ marginLeft: 'auto', padding: '2px 4px', color: 'hsl(214 14% 35%)', background: 'none', border: 'none', cursor: 'pointer' }}
          onMouseEnter={e => e.currentTarget.style.color = 'hsl(0 80% 60%)'}
          onMouseLeave={e => e.currentTarget.style.color = 'hsl(214 14% 35%)'}
        >
          <X size={13} />
        </button>
      </div>
      <div className="tars-loop-body">
        {loop.steps.map((step, si) => (
          <PositionStepRow
            key={si} step={step} index={si}
            onUpdate={(_, field, value) => onUpdateInnerStep(index, si, field, value)}
            onDelete={() => onDeleteInnerStep(index, si)}
            onRelease={onRelease}
            onGripPointerDown={() => {}}
          />
        ))}
        <button className="tars-loop-add" onClick={() => onAddInnerStep(index)}>+ step</button>
      </div>
    </div>
  )
}

// ── Panel component ──────────────────────────────────────────────────────────
function Panel({ title, badge, actions, children, style }) {
  return (
    <div className="tars-panel tars-panel-inner-br" style={style}>
      <div className="tars-panel-header">
        <span className="tars-panel-title">{title}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {badge && <span style={{ fontSize: 9, letterSpacing: '0.12em', color: 'hsl(214 14% 40%)' }}>{badge}</span>}
          {actions}
        </div>
      </div>
      <div className="tars-panel-body">{children}</div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────
function MovementBuilder() {
  const [steps, setSteps] = useState([DEFAULT_STEP()])
  const [sequenceName, setSequenceName] = useState('')
  const [savedSequences, setSavedSequences] = useState({})
  const [sequencePlaying, setSequencePlaying] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [movements, setMovements] = useState([])
  const [selectedMovement, setSelectedMovement] = useState('')
  const [importing, setImporting] = useState(false)
  const [livePreview, setLivePreview] = useState(false)
  const [confirmOverwrite, setConfirmOverwrite] = useState(false)
  const [seqType, setSeqType] = useState('gesture')
  const [isQuick, setIsQuick] = useState(false)
  const [importedFrom, setImportedFrom] = useState('')
  // movement name -> type map, populated by loadMovements
  const movementTypes = useRef({})
  const dragIndex = useRef(null)
  const dragFromHandle = useRef(false)

  useEffect(() => { loadSavedSequences(); loadMovements() }, [])

  const loadSavedSequences = () => {
    fetch('/api/control/saved-sequences').then(r => r.json()).then(setSavedSequences).catch(() => {})
  }
  const loadMovements = () => {
    fetch('/api/control/movements').then(r => r.json()).then(data => {
      const raw = data.movements || []
      // Support both old flat string list and new [{name, type}] format
      const typed = raw.map(m => typeof m === 'string' ? { name: m, type: 'gesture' } : m)
      const typeMap = {}
      typed.forEach(m => { typeMap[m.name] = m.type })
      movementTypes.current = typeMap
      const list = typed.map(m => m.name)
      setMovements(list)
      if (list.length > 0) setSelectedMovement(list[0])
    }).catch(() => {})
  }

  const addPositionStep = () => setSteps(s => [...s, DEFAULT_STEP()])
  const addMovementStep = () => { setSteps(s => [...s, { movement: selectedMovement, hold_time: 0 }]); setImportedFrom('') }
  const addLoop = () => setSteps(s => [...s, DEFAULT_LOOP()])
  const deleteStep = (i) => setSteps(s => s.filter((_, idx) => idx !== i))
  const updateStep = (i, field, value) => setSteps(s => s.map((step, idx) => idx === i ? { ...step, [field]: value } : step))
  const updateLoopRepeat = (i, val) => setSteps(s => s.map((step, idx) => idx === i ? { ...step, repeat: val } : step))
  const updateLoopInnerStep = (i, si, field, value) => setSteps(s => s.map((step, idx) => idx === i ? { ...step, steps: step.steps.map((inner, sidx) => sidx === si ? { ...inner, [field]: value } : inner) } : step))
  const deleteLoopInnerStep = (i, si) => setSteps(s => s.map((step, idx) => idx === i ? { ...step, steps: step.steps.filter((_, sidx) => sidx !== si) } : step))
  const addLoopInnerStep = (i) => setSteps(s => s.map((step, idx) => idx === i ? { ...step, steps: [...step.steps, DEFAULT_STEP()] } : step))
  const resetSteps = () => { setSteps([DEFAULT_STEP()]); setSequenceName(''); setFeedback(''); setImportedFrom('') }

  const handleDragStart = (e, i) => {
    if (!dragFromHandle.current) { e.preventDefault(); return }
    dragIndex.current = i
  }
  const handleDragEnd = () => { dragFromHandle.current = false }
  const handleDragOver = (e) => { e.preventDefault() }
  const handleDrop = (i) => {
    const from = dragIndex.current
    if (from === null || from === i) return
    setSteps(s => { const a = [...s]; const [m] = a.splice(from, 1); a.splice(i, 0, m); return a })
    dragIndex.current = null
  }

  const sendMoveLeg = async (step) => {
    if (!livePreview) return
    try {
      await fetch('/api/control/move-legs', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ left_height: step.left_height, right_height: step.right_height, left_leg: step.left_leg, right_leg: step.right_leg, speed: step.speed }),
      })
    } catch {}
  }

  const resetToNeutral = () => fetch('/api/control/move-legs', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ left_height: 50, right_height: 50, left_leg: 50, right_leg: 50, speed: 0.8 }),
  }).catch(() => {})

  const playSequence = async () => {
    setSequencePlaying(true); setFeedback('')
    try {
      const res = await fetch('/api/control/play-sequence', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steps }),
      })
      setFeedback(res.ok ? '» SEQUENCE COMPLETE' : `» ERR ${(await res.json()).detail || res.statusText}`)
    } catch (err) { setFeedback(`» ERR ${err.message}`) }
    setSequencePlaying(false)
  }

  const saveSequence = async () => {
    if (!sequenceName.trim()) { setFeedback('» NAME REQUIRED'); return }
    const name = sequenceName.trim()
    if (savedSequences[name] && !confirmOverwrite) { setConfirmOverwrite(true); return }
    setConfirmOverwrite(false)
    try {
      const res = await fetch('/api/control/save-sequence', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, steps, type: seqType, quick: isQuick }),
      })
      if (res.ok) { setFeedback(`» SAVED "${name}"`); setSequenceName(''); loadSavedSequences() }
      else setFeedback('» SAVE FAILED')
    } catch (err) { setFeedback(`» ERR ${err.message}`) }
  }

  const playSaved = async (name) => {
    setSequencePlaying(true); setFeedback('')
    try {
      const res = await fetch(`/api/control/play-saved/${encodeURIComponent(name)}`, { method: 'POST' })
      setFeedback(res.ok ? `» "${name}" COMPLETE` : `» ERR ${(await res.json()).detail || res.statusText}`)
    } catch (err) { setFeedback(`» ERR ${err.message}`) }
    setSequencePlaying(false)
  }

  const deleteSaved = async (name) => {
    try { await fetch(`/api/control/saved-sequences/${encodeURIComponent(name)}`, { method: 'DELETE' }); loadSavedSequences() }
    catch {}
  }

  const normalizeStep = (s) => {
    if (s.repeat !== undefined) return { repeat: s.repeat, steps: (s.steps || []).map(normalizeStep) }
    if (s.movement) return { movement: s.movement, hold_time: s.hold_time ?? 0 }
    return { left_height: s.left_height ?? 50, right_height: s.right_height ?? 50, left_leg: s.left_leg ?? 50, right_leg: s.right_leg ?? 50, speed: s.speed ?? 0.85, hold_time: s.hold_time ?? 0 }
  }

  const loadIntoEditor = (name) => {
    const loaded = savedSequences[name]; if (!loaded) return
    const rawSteps = Array.isArray(loaded) ? loaded : (loaded.steps || [])
    const type = Array.isArray(loaded) ? 'gesture' : (loaded.type || 'gesture')
    setSteps(rawSteps.map(normalizeStep)); setSequenceName(name); setSeqType(type)
    setImportedFrom(name); setFeedback(`» LOADED "${name}"`)
  }

  const importFromMovement = async (name) => {
    setImporting(true); setFeedback('')
    try {
      const res = await fetch(`/api/control/movement-steps/${encodeURIComponent(name)}`)
      if (res.ok) {
        const data = await res.json()
        setSteps((data.steps || []).map(normalizeStep))
        const type = movementTypes.current[name] || 'gesture'
        setSequenceName(name); setImportedFrom(name); setSeqType(type)
        setFeedback(`» IMPORTED "${name}" — SAVE UNDER NEW NAME`)
      } else setFeedback(`» IMPORT FAILED: ${(await res.json()).detail}`)
    } catch (err) { setFeedback(`» ERR ${err.message}`) }
    setImporting(false)
  }

  const previewMovementName = importedFrom || sequenceName
  const previewIsLocomotion = seqType === 'locomotion'

  return (
    <div style={{ padding: '12px 12px 24px', fontFamily: "'Share Tech Mono', monospace" }}>

      {/* ── Header bar ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid hsl(214 28% 11%)' }}>
        <div>
          <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 18, letterSpacing: '0.15em', color: 'hsl(191 100% 55%)' }}>
            MOVEMENT BUILDER
          </div>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 38%)', marginTop: 1 }}>
            SEQUENCE DESIGN INTERFACE
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`tars-status-dot ${sequencePlaying ? 'active' : ''}`} />
            <span style={{ fontSize: 9, letterSpacing: '0.15em', color: sequencePlaying ? 'hsl(191 100% 55%)' : 'hsl(214 14% 42%)' }}>
              {sequencePlaying ? 'EXECUTING' : 'STANDBY'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`tars-status-dot ${livePreview ? 'active' : ''}`} />
            <span style={{ fontSize: 9, letterSpacing: '0.15em', color: livePreview ? 'hsl(191 100% 55%)' : 'hsl(214 14% 42%)' }}>
              LIVE
            </span>
          </div>
        </div>
      </div>

      {/* ── Two-column grid ─────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 12, alignItems: 'start' }}>

        {/* ── LEFT: Sequence Editor ───────────────────────────────── */}
        <Panel
          title="Sequence Editor"
          badge={`${steps.length} STEP${steps.length !== 1 ? 'S' : ''}`}
          actions={
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={() => setLivePreview(v => !v)}
                className={`tars-btn tars-btn-icon ${livePreview ? 'tars-btn-cyan' : 'tars-btn-ghost'}`}
                title="Toggle live robot preview"
                style={{ fontSize: 9, letterSpacing: '0.12em', padding: '4px 8px' }}
              >
                {livePreview ? 'LIVE ●' : 'LIVE ○'}
              </button>
              <button onClick={resetSteps} className="tars-btn tars-btn-ghost tars-btn-icon" title="Clear all steps" style={{ padding: '4px 8px', fontSize: 9, letterSpacing: '0.1em' }}>
                CLR
              </button>
            </div>
          }
        >
          {/* Channel legend */}
          <div className="tars-ch-grid" style={{ marginBottom: 12 }}>
            <span><span className="tars-ch-label">LH</span> ch0 — left height</span>
            <span><span className="tars-ch-label">RH</span> ch1 — right height</span>
            <span><span className="tars-ch-label">LL</span> ch2 — left fwd/back</span>
            <span><span className="tars-ch-label">RL</span> ch3 — right fwd/back</span>
          </div>

          {/* Steps */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
            {steps.map((step, i) => (
              <div
                key={i} draggable
                onDragStart={(e) => handleDragStart(e, i)}
                onDragEnd={handleDragEnd}
                onDragOver={handleDragOver}
                onDrop={() => handleDrop(i)}
                className="tars-step-outer"
              >
                <div className="tars-step-num">STEP {String(i + 1).padStart(3, '0')}</div>
                {step.repeat !== undefined
                  ? <LoopBlock loop={step} index={i} onUpdateRepeat={updateLoopRepeat} onUpdateInnerStep={updateLoopInnerStep} onDeleteInnerStep={deleteLoopInnerStep} onAddInnerStep={addLoopInnerStep} onDelete={deleteStep} onGripPointerDown={() => { dragFromHandle.current = true }} onRelease={sendMoveLeg} />
                  : step.movement
                    ? <MovementStepRow step={step} index={i} onDelete={deleteStep} onGripPointerDown={() => { dragFromHandle.current = true }} />
                    : <PositionStepRow step={step} index={i} onUpdate={updateStep} onDelete={deleteStep} onRelease={sendMoveLeg} onGripPointerDown={() => { dragFromHandle.current = true }} />
                }
              </div>
            ))}
          </div>

          {/* Add steps */}
          <div style={{ borderTop: '1px solid hsl(214 28% 11%)', paddingTop: 12 }}>
            <div className="tars-section-label">Add Steps</div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
              <button className="tars-btn tars-btn-ghost" onClick={addPositionStep} style={{ flex: 1 }}>
                <Plus size={12} /> Position
              </button>
              <button className="tars-btn tars-btn-ghost" onClick={addLoop} style={{ flex: 1 }}>
                <Repeat2 size={12} /> Loop
              </button>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <select value={selectedMovement} onChange={e => setSelectedMovement(e.target.value)} className="tars-select" style={{ flex: 1 }}>
                {movements.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
              <button className="tars-btn tars-btn-ghost tars-btn-icon" onClick={addMovementStep} title="Append as named movement step">
                <Zap size={13} />
              </button>
              <button className="tars-btn tars-btn-amber tars-btn-icon" onClick={() => importFromMovement(selectedMovement)} disabled={importing} title="Import as editable position steps">
                <Download size={13} />
              </button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 9, letterSpacing: '0.1em', color: 'hsl(214 14% 35%)' }}>
              <span>⚡ append named</span>
              <span>⬇ import editable</span>
            </div>
          </div>
        </Panel>

        {/* ── RIGHT: Preview + Execution + Saved ───────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* 3D Preview */}
          <Panel title="3D Preview" badge={previewMovementName ? previewMovementName.toUpperCase() : 'EDITOR'}>
            <TarsPreview steps={steps} movementName={previewMovementName} isLocomotion={previewIsLocomotion} />
          </Panel>

          {/* Execution */}
          <Panel title="Execution">
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <button className="tars-btn tars-btn-amber" onClick={playSequence} disabled={sequencePlaying} style={{ flex: 1 }}>
                {sequencePlaying ? <><Square size={11} /> HALT</> : <><Play size={11} /> Execute</>}
              </button>
              <button className="tars-btn tars-btn-ghost" onClick={resetToNeutral} disabled={sequencePlaying}>
                <RotateCcw size={11} /> Neutral
              </button>
            </div>

            <div className="tars-section-label">Save Sequence</div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
              <input
                placeholder="sequence_name"
                value={sequenceName}
                onChange={e => { setSequenceName(e.target.value); setConfirmOverwrite(false) }}
                className="tars-input"
                style={{ flex: 1, minWidth: 120 }}
              />
              <select value={seqType} onChange={e => setSeqType(e.target.value)} className="tars-select">
                <option value="movement">Movement</option>
                <option value="expression">Expression</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, letterSpacing: '0.12em', color: 'hsl(214 14% 50%)', cursor: 'pointer' }}>
                <input type="checkbox" checked={isQuick} onChange={e => setIsQuick(e.target.checked)} style={{ accentColor: 'hsl(191 100% 46%)' }} />
                QUICK
              </label>
              <button className="tars-btn tars-btn-amber" onClick={saveSequence} style={{ marginLeft: 'auto' }}>
                Save
              </button>
            </div>
            {confirmOverwrite && (
              <div className="tars-confirm-bar" style={{ marginTop: 8 }}>
                <span style={{ flex: 1 }}>"{sequenceName}" EXISTS — OVERWRITE?</span>
                <button className="tars-btn tars-btn-danger" style={{ padding: '4px 10px', fontSize: 10 }} onClick={saveSequence}>YES</button>
                <button className="tars-btn tars-btn-ghost" style={{ padding: '4px 10px', fontSize: 10 }} onClick={() => setConfirmOverwrite(false)}>NO</button>
              </div>
            )}
            {feedback && <div className="tars-feedback" style={{ marginTop: 10 }}>{feedback}</div>}
          </Panel>

          {/* Saved Sequences */}
          {Object.keys(savedSequences).length > 0 && (
            <Panel title="Saved Sequences" badge={`${Object.keys(savedSequences).length} ENTRIES`}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {Object.keys(savedSequences).map(name => (
                  <div key={name} className="tars-chip">
                    <button onClick={() => playSaved(name)} disabled={sequencePlaying}
                      style={{ fontSize: 10, letterSpacing: '0.06em', color: 'hsl(210 22% 70%)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                      onMouseEnter={e => e.currentTarget.style.color = 'hsl(191 100% 60%)'}
                      onMouseLeave={e => e.currentTarget.style.color = 'hsl(210 22% 70%)'}
                    >
                      {name}
                    </button>
                    <button onClick={() => loadIntoEditor(name)} title="Load into editor"
                      style={{ color: 'hsl(214 14% 35%)', background: 'none', border: 'none', cursor: 'pointer', padding: '0 2px', display: 'flex' }}
                      onMouseEnter={e => e.currentTarget.style.color = 'hsl(191 100% 55%)'}
                      onMouseLeave={e => e.currentTarget.style.color = 'hsl(214 14% 35%)'}
                    >
                      <Pencil size={10} />
                    </button>
                    <button onClick={() => deleteSaved(name)}
                      style={{ color: 'hsl(214 14% 35%)', background: 'none', border: 'none', cursor: 'pointer', padding: '0 2px', display: 'flex' }}
                      onMouseEnter={e => e.currentTarget.style.color = 'hsl(0 80% 60%)'}
                      onMouseLeave={e => e.currentTarget.style.color = 'hsl(214 14% 35%)'}
                    >
                      <X size={10} />
                    </button>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  )
}

export default MovementBuilder
