import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Camera, RotateCcw } from 'lucide-react'

const EMOTIONS = ['neutral','happy','sad','angry','excited','sleepy','afraid','sideeye_left','sideeye_right','curious','skeptical','smug','surprised']
const EMOTION_LABELS = { neutral:'Neutral', happy:'Happy', sad:'Sad', angry:'Angry', excited:'Excited', sleepy:'Sleepy', afraid:'Afraid', sideeye_left:'Side-L', sideeye_right:'Side-R', curious:'Curious', skeptical:'Skeptic', smug:'Smug', surprised:'Surprise' }
const EYE_STATES = ['idle','listening','thinking','speaking']


// ── Reusable command button ───────────────────────────────────────────────
function CmdBtn({ label, icon: Icon, onClick, disabled, active, variant = 'ghost', style }) {
  const base = {
    display: 'inline-flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    gap: 3, padding: '8px 6px', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase',
    fontFamily: "'Share Tech Mono', monospace", cursor: disabled ? 'not-allowed' : 'pointer',
    border: '1px solid', transition: 'all 0.12s', opacity: disabled ? 0.45 : 1, ...style,
  }
  const variants = {
    ghost:  { background: active ? 'hsl(36 100% 46% / 0.15)' : 'transparent', borderColor: active ? 'hsl(36 100% 46% / 0.6)' : 'hsl(214 28% 14%)', color: active ? 'hsl(36 100% 60%)' : 'hsl(214 14% 55%)' },
    amber:  { background: 'hsl(36 100% 46% / 0.1)', borderColor: 'hsl(36 100% 46% / 0.5)', color: 'hsl(36 100% 60%)' },
    cyan:   { background: active ? 'hsl(191 100% 44% / 0.18)' : 'hsl(191 100% 44% / 0.06)', borderColor: active ? 'hsl(191 100% 44% / 0.7)' : 'hsl(191 100% 44% / 0.25)', color: active ? 'hsl(191 100% 60%)' : 'hsl(191 100% 44% / 0.7)' },
    danger: { background: 'transparent', borderColor: 'hsl(0 80% 50% / 0.4)', color: 'hsl(0 80% 65%)' },
  }
  const s = { ...base, ...variants[variant] }
  return (
    <button style={s} onClick={onClick} disabled={disabled}
      onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = variants[variant].background.replace('0.1','0.22').replace('0.06','0.18'); e.currentTarget.style.boxShadow = variant === 'amber' ? '0 0 8px hsl(36 100% 46% / 0.2)' : ''; }}}
      onMouseLeave={e => { e.currentTarget.style.background = s.background; e.currentTarget.style.boxShadow = ''; }}
    >
      {Icon && <Icon size={14} />}
      {label}
    </button>
  )
}

// ── Chip button (for emotions, eye states, sequences) ─────────────────────
function Chip({ label, active, onClick, disabled, color = 'amber' }) {
  const colors = {
    amber: { bg: active ? 'hsl(36 100% 46% / 0.18)' : 'hsl(214 35% 6%)', border: active ? 'hsl(36 100% 46% / 0.7)' : 'hsl(214 28% 12%)', text: active ? 'hsl(36 100% 60%)' : 'hsl(214 14% 55%)' },
    cyan:  { bg: active ? 'hsl(191 100% 44% / 0.15)' : 'hsl(214 35% 6%)', border: active ? 'hsl(191 100% 44% / 0.6)' : 'hsl(214 28% 12%)', text: active ? 'hsl(191 100% 60%)' : 'hsl(214 14% 55%)' },
  }
  const c = colors[color]
  return (
    <button
      onClick={onClick} disabled={disabled}
      style={{ padding: '5px 10px', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: "'Share Tech Mono', monospace", background: c.bg, border: `1px solid ${c.border}`, color: c.text, cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.5 : 1, transition: 'all 0.12s' }}
    >
      {label}
    </button>
  )
}

function SectionLabel({ children }) {
  return <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(36 100% 46% / 0.65)', marginBottom: 8 }}>{children}</div>
}

function Panel({ title, children, style }) {
  return (
    <div className="tars-panel tars-panel-inner-br" style={style}>
      <div className="tars-panel-header">
        <span className="tars-panel-title">{title}</span>
      </div>
      <div className="tars-panel-body">{children}</div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────
function Control() {
  const [executing, setExecuting] = useState(null)
  const [cameraUrl, setCameraUrl] = useState(null)
  const [emotion, setEmotion] = useState('neutral')
  const [eyeState, setEyeState] = useState('idle')
  const [savedSequences, setSavedSequences] = useState({})
  const [expressionMap, setExpressionMap] = useState({})
  const [activeExpression, setActiveExpression] = useState(null)

  useEffect(() => {
    fetch('/api/control/saved-sequences').then(r => r.json()).then(setSavedSequences).catch(() => {})
    fetch('/api/expressions/map').then(r => r.json()).then(d => setExpressionMap(d.map || {})).catch(() => {})
  }, [])

  const getSeqType = (entry) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return 'gesture'
    const t = entry.type || 'gesture'
    // Normalize legacy type names
    if (t === 'expression') return 'gesture'
    if (t === 'movement') return 'locomotion'
    return t
  }

  const exec = async (movement) => {
    setExecuting(movement)
    try { await fetch('/api/control/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ movement }) }) }
    catch {}
    setExecuting(null)
  }

  const setEmotionApi = async (e) => {
    try { await fetch('/api/control/emotion', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ emotion: e }) }); setEmotion(e) }
    catch {}
  }

  const setEyeApi = async (s) => {
    try { await fetch('/api/control/eye-state', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ state: s }) }); setEyeState(s) }
    catch {}
  }

  const resetPosition = async () => {
    setExecuting('reset')
    try { await fetch('/api/control/reset', { method: 'POST' }) }
    catch {}
    setExecuting(null)
  }

  const triggerExpression = async (em, intensity) => {
    const key = `${em}:${intensity}`
    setActiveExpression(key)
    try { await fetch('/api/expressions/trigger', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ emotion: em, intensity }) }) }
    catch {}
  }

  // Show gesture-type sequences in custom panel; locomotion is handled by the grid
  const customSeqs = Object.entries(savedSequences).filter(([, e]) => getSeqType(e) === 'gesture')
  const expressionBtns = Object.entries(expressionMap).filter(([, e]) => e?.gesture)

  return (
    <div style={{ padding: '12px 12px 24px', fontFamily: "'Share Tech Mono', monospace" }}>

      {/* Header */}
      <div style={{ marginBottom: 14, paddingBottom: 12, borderBottom: '1px solid hsl(214 28% 11%)' }}>
        <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 18, letterSpacing: '0.15em', color: 'hsl(36 100% 55%)' }}>COMMAND INTERFACE</div>
        <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 38%)', marginTop: 1 }}>TARS DIRECT CONTROL</div>
      </div>

      {/* ── Row 1: Locomotion (left) + Face (right) ──────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12, marginBottom: 12 }}>

        {/* Locomotion D-pad */}
        <Panel title="Locomotion">
          {/* D-pad grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gridTemplateRows: 'auto auto auto auto', gap: 5, maxWidth: 280, margin: '0 auto 12px' }}>
            {/* Row 1: Walk Fwd */}
            <div />
            <CmdBtn label="Walk ↑" onClick={() => exec('walk_forward')} disabled={executing !== null} style={{ width: '100%' }} />
            <div />
            {/* Row 2: Turn L | Step Fwd | Turn R */}
            <CmdBtn label="← Turn" onClick={() => exec('turn_left')} disabled={executing !== null} style={{ width: '100%' }} />
            <CmdBtn label="Step ↑" onClick={() => exec('step_forward')} disabled={executing !== null} style={{ width: '100%' }} />
            <CmdBtn label="Turn →" onClick={() => exec('turn_right')} disabled={executing !== null} style={{ width: '100%' }} />
            {/* Row 3: Slow L | Step Back | Slow R */}
            <CmdBtn label="← Slow" onClick={() => exec('turn_left_slow')} disabled={executing !== null} style={{ width: '100%', fontSize: 9 }} />
            <CmdBtn label="Step ↓" onClick={() => exec('step_backward')} disabled={executing !== null} style={{ width: '100%' }} />
            <CmdBtn label="Slow →" onClick={() => exec('turn_right_slow')} disabled={executing !== null} style={{ width: '100%', fontSize: 9 }} />
            {/* Row 4: Walk Back */}
            <div />
            <CmdBtn label="Walk ↓" onClick={() => exec('walk_backward')} disabled={executing !== null} style={{ width: '100%' }} />
            <div />
          </div>

          {/* Balance + Reset row */}
          <div style={{ borderTop: '1px solid hsl(214 28% 11%)', paddingTop: 10 }}>
            <SectionLabel>Balance & Reset</SectionLabel>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {[['tilt_left','Tilt L'],['tilt_right','Tilt R'],['side_side','Side-Side'],['swing_legs','Swing']].map(([name, label]) => (
                <CmdBtn key={name} label={label} onClick={() => exec(name)} disabled={executing !== null} style={{ flex: 1, minWidth: 60 }} />
              ))}
              <CmdBtn label="Reset" icon={RotateCcw} onClick={resetPosition} disabled={executing !== null} variant="amber" style={{ flex: 1, minWidth: 60 }} />
            </div>
          </div>
        </Panel>

        {/* Face: Eye State + Emotion */}
        <Panel title="Face & Emotion">
          <SectionLabel>Eye State</SectionLabel>
          <div style={{ display: 'flex', gap: 5, marginBottom: 14, flexWrap: 'wrap' }}>
            {EYE_STATES.map(s => (
              <Chip key={s} label={s} active={eyeState === s} color="cyan" onClick={() => setEyeApi(s)} />
            ))}
          </div>

          <SectionLabel>Emotion</SectionLabel>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 14 }}>
            {EMOTIONS.map(e => (
              <Chip key={e} label={EMOTION_LABELS[e] || e} active={emotion === e} onClick={() => setEmotionApi(e)} />
            ))}
          </div>

          <SectionLabel>Gestures</SectionLabel>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {[['wave_right','Wave R'],['wave_left','Wave L'],['bow','Bow'],['pose','Pose'],['laugh','Laugh'],['neutral_legs','Neutral']].map(([name, label]) => (
              <CmdBtn key={name} label={label} onClick={() => exec(name)} disabled={executing !== null} />
            ))}
          </div>
        </Panel>
      </div>

      {/* ── Row 2: Camera + Custom Expressions + Sequences ───────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>

        {/* Camera */}
        <Panel title="Camera">
          <div style={{ marginBottom: 8 }}>
            <button
              onClick={() => setCameraUrl(`/api/status/camera?t=${Date.now()}`)}
              className="tars-btn tars-btn-ghost"
              style={{ width: '100%', marginBottom: 8 }}
            >
              <Camera size={12} /> Capture Frame
            </button>
          </div>
          {cameraUrl ? (
            <img src={cameraUrl} alt="Camera" style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', background: 'hsl(214 35% 6%)', display: 'block' }} onError={() => setCameraUrl(null)} />
          ) : (
            <div style={{ width: '100%', aspectRatio: '1', background: 'hsl(214 35% 5%)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid hsl(214 28% 11%)', fontSize: 10, letterSpacing: '0.1em', color: 'hsl(214 14% 30%)' }}>
              NO SIGNAL
            </div>
          )}
        </Panel>

        {/* Expression triggers (from expression map) */}
        {expressionBtns.length > 0 && (
          <Panel title="Expression Triggers">
            <div style={{ marginBottom: 6, fontSize: 9, letterSpacing: '0.1em', color: 'hsl(214 14% 38%)' }}>
              <Link to="/expressions" style={{ color: 'hsl(191 100% 44% / 0.7)', textDecoration: 'none' }}>All Expressions →</Link>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {expressionBtns.map(([key]) => {
                const [em, intensity] = key.split(':')
                const label = `${em.replace('_',' ')} (${intensity})`
                return (
                  <Chip key={key} label={label} active={activeExpression === key} color="cyan" onClick={() => triggerExpression(em, intensity)} />
                )
              })}
            </div>
          </Panel>
        )}

        {/* Custom gesture sequences */}
        {customSeqs.length > 0 && (
          <Panel title="Custom Gestures">
            {customSeqs.some(([, e]) => e?.quick) && (
              <>
                <SectionLabel>Quick</SectionLabel>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 10 }}>
                  {customSeqs.filter(([, e]) => e?.quick).map(([name]) => (
                    <Chip key={name} label={name} color="cyan" onClick={() => exec(name)} disabled={executing !== null} />
                  ))}
                </div>
              </>
            )}
            {customSeqs.some(([, e]) => !e?.quick) && (
              <>
                <SectionLabel>Standard</SectionLabel>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {customSeqs.filter(([, e]) => !e?.quick).map(([name]) => (
                    <Chip key={name} label={name} onClick={() => exec(name)} disabled={executing !== null} />
                  ))}
                </div>
              </>
            )}
          </Panel>
        )}
      </div>
    </div>
  )
}

export default Control
