import { useState, useEffect } from 'react'
import { Pencil, X, RotateCcw } from 'lucide-react'

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

const BG = 'hsl(214 35% 5%)'
const EW = 44
const EH = 64
const R  = 10

function Eye({ cx, cy, open, lid, lidSide, curve, color, lookX }) {
  const eh = Math.max(4, EH * open)
  const er = Math.min(R, EW / 2, eh / 2)
  const lx = lookX * EW * 0.22
  const ex = cx - EW / 2 + lx
  const ey = cy - eh / 2
  const lidPx = eh * lid
  const curveH = eh * 0.5 * curve
  const curveY = ey + eh * 0.75
  const curvePath = curve > 0.01
    ? `M ${ex},${curveY} Q ${cx + lx},${curveY - curveH} ${ex + EW},${curveY} L ${ex + EW},${ey + eh + 4} L ${ex},${ey + eh + 4} Z`
    : null
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
      {lidPoints && <polygon points={lidPoints} fill="#0a0e14" />}
      {curvePath && <path d={curvePath} fill="#0a0e14" />}
    </g>
  )
}

function EyePreview({ emotion }) {
  const p = EYE_PARAMS[emotion] || EYE_PARAMS.neutral
  return (
    <svg viewBox="0 0 200 90" width="180" height="81"
      style={{ background: 'hsl(214 35% 5%)', border: '1px solid hsl(214 28% 11%)' }}>
      <Eye cx={55}  cy={45} open={p.openL} lid={p.lidL} lidSide={p.lidSideL} curve={p.curveL} color={p.color} lookX={p.lookX} />
      <Eye cx={145} cy={45} open={p.openR} lid={p.lidR} lidSide={p.lidSideR} curve={p.curveR} color={p.color} lookX={p.lookX} />
    </svg>
  )
}

function Panel({ title, children }) {
  return (
    <div className="tars-panel tars-panel-inner-br">
      <div className="tars-panel-header">
        <span className="tars-panel-title">{title}</span>
      </div>
      <div className="tars-panel-body">{children}</div>
    </div>
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
      .then(data => { setExpressionMap(data.map || {}); setCustomKeys(data.custom_keys || []) })
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
    } catch {}
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

  const previewEmotion = editingCell
    ? (editEyes || editingCell.split(':')[0])
    : activeCell
      ? (expressionMap[activeCell]?.eyes || activeCell.split(':')[0])
      : 'neutral'

  return (
    <div style={{ padding: '12px 12px 24px', fontFamily: "'Share Tech Mono', monospace" }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14, paddingBottom: 12, borderBottom: '1px solid hsl(214 28% 11%)' }}>
        <div>
          <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 18, letterSpacing: '0.15em', color: 'hsl(191 100% 55%)' }}>EXPRESSION MATRIX</div>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 38%)', marginTop: 1 }}>TARS UNIT — FACIAL CONTROL</div>
          {activeCell && (
            <div style={{ fontSize: 9, letterSpacing: '0.15em', color: 'hsl(191 100% 55%)', marginTop: 4 }}>
              ACTIVE: {activeCell.replace(':', ' / ').toUpperCase()}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
          <EyePreview emotion={previewEmotion} />
          <div style={{ fontSize: 9, letterSpacing: '0.15em', color: 'hsl(214 14% 38%)', textAlign: 'right' }}>
            {(EMOTION_LABELS[previewEmotion] || previewEmotion).toUpperCase()}
          </div>
        </div>
      </div>

      {/* Expression Grid */}
      <Panel title="Expression Map">
        {/* Column headers */}
        <div style={{ display: 'grid', gridTemplateColumns: '72px 1fr 1fr 1fr', gap: 4, marginBottom: 6 }}>
          <div />
          {INTENSITIES.map(i => (
            <div key={i} style={{ fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 35%)', textAlign: 'center', paddingBottom: 2, borderBottom: '1px solid hsl(214 28% 11%)' }}>{i}</div>
          ))}
        </div>
        {/* Rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {EMOTIONS.map(emotion => (
            <div key={emotion} style={{ display: 'grid', gridTemplateColumns: '72px 1fr 1fr 1fr', gap: 4, alignItems: 'center' }}>
              <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'hsl(214 14% 45%)', textTransform: 'uppercase', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {EMOTION_LABELS[emotion]}
              </div>
              {INTENSITIES.map(intensity => {
                const key = `${emotion}:${intensity}`
                const entry = expressionMap[key]
                const isActive = activeCell === key
                const isExecuting = executing === key
                const isEditing = editingCell === key
                const hasGesture = !!entry?.gesture
                const isCustom = customKeys.includes(key)
                const label = isExecuting ? '…' : entry ? (entry.gesture ? entry.gesture.split(' ')[0] : 'eyes') : '—'

                return (
                  <div key={intensity} style={{ position: 'relative' }} className="group">
                    <button
                      onClick={() => trigger(emotion, intensity)}
                      disabled={isExecuting}
                      style={{
                        width: '100%',
                        padding: '5px 4px',
                        fontSize: 9,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        fontFamily: "'Share Tech Mono', monospace",
                        cursor: isExecuting ? 'wait' : 'pointer',
                        background: isActive ? 'hsl(191 100% 46% / 0.15)' : isEditing ? 'hsl(191 100% 44% / 0.08)' : 'hsl(214 35% 5%)',
                        border: isActive
                          ? '1px solid hsl(191 100% 46% / 0.6)'
                          : isEditing
                          ? '1px solid hsl(191 100% 44% / 0.5)'
                          : hasGesture
                          ? '1px solid hsl(214 28% 16%)'
                          : '1px solid hsl(214 28% 11%)',
                        borderLeft: isCustom && !isActive ? '2px solid hsl(191 100% 46% / 0.4)' : undefined,
                        color: isActive ? 'hsl(191 100% 60%)' : isEditing ? 'hsl(191 100% 55%)' : entry ? 'hsl(210 22% 65%)' : 'hsl(214 14% 28%)',
                        transition: 'all 0.15s ease',
                        textAlign: 'center',
                      }}
                    >
                      {label}
                    </button>
                    <button
                      onClick={e => { e.stopPropagation(); openEditor(emotion, intensity) }}
                      className="group-hover:flex"
                      style={{
                        display: 'none',
                        position: 'absolute',
                        top: -4, right: -4,
                        width: 14, height: 14,
                        background: 'hsl(214 28% 14%)',
                        border: '1px solid hsl(214 28% 22%)',
                        cursor: 'pointer',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: 0,
                        zIndex: 10,
                      }}
                    >
                      <Pencil size={7} style={{ color: 'hsl(191 100% 46%)' }} />
                    </button>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </Panel>

      {/* Editor */}
      {editingCell && (
        <div style={{ marginTop: 12 }}>
          <Panel title={`EDIT / ${editingCell.replace(':', ' / ').toUpperCase()}`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <div style={{ fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 40%)', marginBottom: 6 }}>Eyes</div>
                  <select
                    value={editEyes}
                    onChange={e => setEditEyes(e.target.value)}
                    className="tars-select"
                    style={{ width: '100%' }}
                  >
                    {EMOTIONS.map(e => (
                      <option key={e} value={e}>{EMOTION_LABELS[e]}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <div style={{ fontSize: 8, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 40%)', marginBottom: 6 }}>Gesture</div>
                  <select
                    value={editGesture || '__none__'}
                    onChange={e => setEditGesture(e.target.value === '__none__' ? '' : e.target.value)}
                    className="tars-select"
                    style={{ width: '100%' }}
                  >
                    <option value="__none__">None</option>
                    {gestures.map(g => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={saveEdit} className="tars-btn tars-btn-amber" style={{ flex: 1 }}>Save</button>
                {customKeys.includes(editingCell) && (
                  <button onClick={resetEntry} className="tars-btn tars-btn-ghost" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <RotateCcw size={11} />
                    Reset
                  </button>
                )}
                <button
                  onClick={() => setEditingCell(null)}
                  className="tars-btn tars-btn-ghost"
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 10px' }}
                >
                  <X size={12} />
                </button>
              </div>
            </div>
          </Panel>
        </div>
      )}
    </div>
  )
}
