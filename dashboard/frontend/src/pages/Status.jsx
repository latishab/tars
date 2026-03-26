import { useState, useEffect, useRef } from 'react'
import { Battery, Cpu, Thermometer, Wifi, Radio, Copy, Check, Wind, Info, Monitor, CloudSun } from 'lucide-react'

// ── Gauge bar ─────────────────────────────────────────────────────────────
function batteryColor(level) {
  if (level > 60) return 'hsl(141 70% 45%)'   // green
  if (level > 20) return 'hsl(35 95% 50%)'    // orange
  return 'hsl(0 80% 50%)'                      // red
}

function GaugeBar({ value, max = 100, warn = 80, danger = 95, low = 20, battery = false }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  const color = battery
    ? batteryColor(value)
    : value >= danger
      ? 'hsl(0 80% 50%)'
      : value >= warn
        ? 'hsl(35 95% 50%)'
        : 'hsl(191 100% 46%)'
  return (
    <div style={{ position: 'relative', height: 3, background: 'hsl(214 28% 11%)', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${pct}%`, background: color, transition: 'width 0.6s ease', boxShadow: `0 0 6px ${color}` }} />
    </div>
  )
}

// ── Metric tile ──────────────────────────────────────────────────────────
function MetricTile({ label, value, unit, sub, gauge, gaugeLow, gaugeWarn, gaugeMax = 100 }) {
  return (
    <div style={{ padding: '12px 14px', background: 'hsl(214 35% 5%)', border: '1px solid hsl(214 28% 11%)', borderLeft: '2px solid hsl(191 100% 46% / 0.25)' }}>
      <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 40%)', marginBottom: 6 }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 4 }}>
        <span style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 28, color: 'hsl(210 22% 88%)', lineHeight: 1 }}>{value ?? '—'}</span>
        {unit && <span style={{ fontSize: 10, letterSpacing: '0.08em', color: 'hsl(214 14% 45%)' }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'hsl(214 14% 40%)', marginBottom: 4 }}>{sub}</div>}
      {gauge != null && <GaugeBar value={gauge} max={gaugeMax} low={gaugeLow} warn={gaugeWarn} />}
    </div>
  )
}

// ── Connection row ────────────────────────────────────────────────────────
function ConnRow({ label, active }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid hsl(214 28% 9%)' }}>
      <div style={{ width: 6, height: 6, borderRadius: '50%', background: active ? 'hsl(141 70% 45%)' : 'hsl(214 14% 28%)', boxShadow: active ? '0 0 6px hsl(141 70% 45%)' : 'none', flexShrink: 0 }} />
      <span style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'hsl(214 14% 50%)', flex: 1 }}>{label}</span>
      <span style={{ fontSize: 9, letterSpacing: '0.1em', color: active ? 'hsl(141 70% 55%)' : 'hsl(214 14% 35%)' }}>{active ? 'ONLINE' : 'OFFLINE'}</span>
    </div>
  )
}

// ── Panel ─────────────────────────────────────────────────────────────────
function Panel({ title, icon: Icon, children, action }) {
  return (
    <div className="tars-panel tars-panel-inner-br">
      <div className="tars-panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {Icon && <Icon size={12} style={{ color: 'hsl(191 100% 46% / 0.7)' }} />}
          <span className="tars-panel-title">{title}</span>
        </div>
        {action}
      </div>
      <div className="tars-panel-body">{children}</div>
    </div>
  )
}

// ── Timestamp ────────────────────────────────────────────────────────────
function Timestamp() {
  const [time, setTime] = useState(new Date())
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t) }, [])
  const fmt = t => t.toISOString().replace('T', ' ').slice(0, 19) + ' UTC'
  return <span style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 10, letterSpacing: '0.1em', color: 'hsl(214 14% 35%)' }}>{fmt(time)}</span>
}

// ── Display Panel ─────────────────────────────────────────────────────────
const APPS = [
  { name: 'eyes',     label: 'Eyes' },
  { name: 'spectrum', label: 'Spectrum' },
  { name: 'clock',    label: 'Clock' },
  { name: 'weather',  label: 'Weather' },
]

const SCREENSAVERS = [
  { name: 'starfield',  label: 'Starfield' },
  { name: 'endurance',  label: 'Endurance' },
]

function DisplayPanel({ displayStatus, onSwitchApp, onActivateScreensaver, onDeactivateScreensaver, loading }) {
  const activeApp = displayStatus?.active_app
  const screensaverActive = displayStatus?.screensaver_active
  const activeScreensaver = displayStatus?.active_screensaver

  return (
    <Panel title="Display Mode" icon={Monitor}>
      {/* App section */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 40%)', marginBottom: 8 }}>
          APP
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {APPS.map(app => {
            const isActive = !screensaverActive && activeApp === app.name
            return (
              <button
                key={app.name}
                onClick={() => onSwitchApp(app.name)}
                disabled={loading}
                className={`tars-btn ${isActive ? 'tars-btn-cyan' : 'tars-btn-ghost'}`}
                style={{ fontSize: 10, letterSpacing: '0.12em', minWidth: 72 }}
              >
                {app.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: 'hsl(214 28% 11%)', marginBottom: 14 }} />

      {/* Screensaver section */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 40%)' }}>
            SCREENSAVER
          </div>
          {screensaverActive && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 5, height: 5, borderRadius: '50%',
                background: 'hsl(191 100% 44%)',
                boxShadow: '0 0 6px hsl(191 100% 44%)',
                animation: 'tars-pulse-cyan 1.2s ease-in-out infinite',
              }} />
              <span style={{ fontSize: 9, letterSpacing: '0.14em', color: 'hsl(191 100% 55%)' }}>
                {activeScreensaver ? activeScreensaver.toUpperCase() : 'ACTIVE'}
              </span>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          {SCREENSAVERS.map(ss => {
            const isActive = screensaverActive && activeScreensaver === ss.name
            return (
              <button
                key={ss.name}
                onClick={() => onActivateScreensaver(ss.name)}
                disabled={loading}
                className={`tars-btn ${isActive ? 'tars-btn-cyan' : 'tars-btn-ghost'}`}
                style={{ fontSize: 10, letterSpacing: '0.12em', minWidth: 78 }}
              >
                {ss.label}
              </button>
            )
          })}
          {screensaverActive && (
            <button
              onClick={onDeactivateScreensaver}
              disabled={loading}
              className="tars-btn tars-btn-ghost"
              style={{ fontSize: 10, letterSpacing: '0.12em', color: 'hsl(0 80% 60%)', borderColor: 'hsl(0 80% 30% / 0.4)' }}
            >
              Deactivate
            </button>
          )}
        </div>
      </div>
    </Panel>
  )
}

// ── Weather helpers ────────────────────────────────────────────────────────
const WMO_LABEL = {
  0:'CLEAR SKY',1:'MAINLY CLEAR',2:'PARTLY CLOUDY',3:'OVERCAST',
  45:'FOG',48:'ICING FOG',
  51:'LIGHT DRIZZLE',53:'DRIZZLE',55:'HEAVY DRIZZLE',
  61:'LIGHT RAIN',63:'RAIN',65:'HEAVY RAIN',
  71:'LIGHT SNOW',73:'SNOW',75:'HEAVY SNOW',77:'SNOW GRAINS',
  80:'RAIN SHOWERS',81:'SHOWERS',82:'HEAVY SHOWERS',
  85:'SNOW SHOWERS',86:'HEAVY SNOW SHOWERS',
  95:'THUNDERSTORM',96:'T-STORM + HAIL',99:'T-STORM + HAIL',
}
const WMO_COLOR = {
  0:'hsl(42 100% 62%)',1:'hsl(42 100% 62%)',2:'hsl(200 60% 65%)',3:'hsl(214 14% 50%)',
  45:'hsl(180 20% 55%)',48:'hsl(180 20% 55%)',
  51:'hsl(191 80% 55%)',53:'hsl(191 80% 55%)',55:'hsl(191 80% 55%)',
  61:'hsl(210 80% 60%)',63:'hsl(210 80% 60%)',65:'hsl(210 80% 60%)',
  71:'hsl(220 40% 80%)',73:'hsl(220 40% 80%)',75:'hsl(220 40% 80%)',77:'hsl(220 40% 80%)',
  80:'hsl(210 70% 62%)',81:'hsl(210 70% 62%)',82:'hsl(210 70% 62%)',
  85:'hsl(220 40% 80%)',86:'hsl(220 40% 80%)',
  95:'hsl(280 70% 65%)',96:'hsl(280 70% 65%)',99:'hsl(280 70% 65%)',
}
const DAYS = ['SUN','MON','TUE','WED','THU','FRI','SAT']

async function fetchWeather() {
  const geo = await fetch('http://ip-api.com/json/?fields=city,country,lat,lon,status').then(r => r.json())
  if (geo.status !== 'success') throw new Error('geolocation failed')
  const { lat, lon, city, country } = geo
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}`
    + `&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m`
    + `&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=4`
  const w = await fetch(url).then(r => r.json())
  const cur = w.current
  const daily = w.daily
  return {
    city, country, lat, lon,
    temp: Math.round(cur.temperature_2m),
    feels: Math.round(cur.apparent_temperature),
    humidity: cur.relative_humidity_2m,
    wind: Math.round(cur.wind_speed_10m),
    code: cur.weather_code,
    forecast: [1,2,3].map(i => ({
      day: DAYS[new Date(daily.time[i]).getDay()],
      code: daily.weather_code[i],
      hi: Math.round(daily.temperature_2m_max[i]),
      lo: Math.round(daily.temperature_2m_min[i]),
    })),
    updatedAt: Date.now(),
  }
}

// ── Weather Panel ──────────────────────────────────────────────────────────
function WeatherPanel() {
  const [wx, setWx] = useState(null)
  const [wxErr, setWxErr] = useState(null)
  const [wxLoading, setWxLoading] = useState(true)
  const timerRef = useRef(null)

  const load = async () => {
    setWxLoading(true)
    try { setWx(await fetchWeather()); setWxErr(null) }
    catch (e) { setWxErr(e.message) }
    setWxLoading(false)
  }

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, 10 * 60 * 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  const labelStyle = { fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'hsl(214 14% 40%)' }
  const mutedStyle = { fontSize: 9, letterSpacing: '0.1em', color: 'hsl(214 14% 38%)' }

  return (
    <Panel title="Weather" icon={CloudSun} action={
      <button onClick={load} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 9, letterSpacing: '0.12em', color: 'hsl(214 14% 38%)', padding: '2px 0' }}>
        {wxLoading ? '…' : 'REFRESH'}
      </button>
    }>
      {wxLoading && !wx && (
        <div style={{ ...mutedStyle, padding: '12px 0', textAlign: 'center' }}>ACQUIRING…</div>
      )}
      {wxErr && !wx && (
        <div style={{ fontSize: 9, letterSpacing: '0.12em', color: 'hsl(0 80% 55%)', padding: '8px 0' }}>LINK LOST — {wxErr}</div>
      )}
      {wx && (() => {
        const condColor = WMO_COLOR[wx.code] ?? 'hsl(191 100% 46%)'
        const condLabel = WMO_LABEL[wx.code] ?? 'UNKNOWN'
        return (
          <>
            {/* Location + condition */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <div>
                <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 20, letterSpacing: '0.08em', color: 'hsl(210 22% 88%)' }}>
                  {wx.city}
                </div>
                <div style={mutedStyle}>{wx.country} · {wx.lat.toFixed(2)}N {Math.abs(wx.lon).toFixed(2)}{wx.lon < 0 ? 'W' : 'E'}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 36, color: condColor, lineHeight: 1 }}>
                  {wx.temp}°
                </div>
                <div style={{ fontSize: 9, letterSpacing: '0.1em', color: condColor, marginTop: 2 }}>{condLabel}</div>
              </div>
            </div>

            {/* Stats row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 6, marginBottom: 12 }}>
              {[
                ['FEELS', `${wx.feels}°`],
                ['HUMIDITY', `${wx.humidity}%`],
                ['WIND', `${wx.wind} km/h`],
              ].map(([k, v]) => (
                <div key={k} style={{ padding: '8px 10px', background: 'hsl(214 35% 5%)', border: '1px solid hsl(214 28% 11%)', borderLeft: '2px solid hsl(191 100% 46% / 0.2)' }}>
                  <div style={labelStyle}>{k}</div>
                  <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 18, color: 'hsl(191 100% 55%)', marginTop: 2 }}>{v}</div>
                </div>
              ))}
            </div>

            {/* Divider */}
            <div style={{ height: 1, background: 'hsl(214 28% 11%)', marginBottom: 10 }} />

            {/* 3-day forecast */}
            <div style={{ ...labelStyle, marginBottom: 8 }}>3-DAY FORECAST</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {wx.forecast.map(fc => {
                const fc_color = WMO_COLOR[fc.code] ?? 'hsl(191 100% 46%)'
                const fc_label = WMO_LABEL[fc.code] ?? '??'
                const spread = Math.max(1, fc.hi - fc.lo)
                const barPct = Math.min(100, (spread / 20) * 100)
                return (
                  <div key={fc.day} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 8px', background: 'hsl(214 35% 5%)' }}>
                    <span style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 13, color: 'hsl(210 22% 70%)', width: 28 }}>{fc.day}</span>
                    <div style={{ flex: 1, height: 2, background: 'hsl(214 28% 11%)', borderRadius: 1, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${barPct}%`, background: fc_color, boxShadow: `0 0 4px ${fc_color}` }} />
                    </div>
                    <span style={{ fontSize: 9, letterSpacing: '0.08em', color: fc_color, width: 90, textAlign: 'right' }}>{fc_label}</span>
                    <span style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 14, color: fc_color, width: 28, textAlign: 'right' }}>{fc.hi}°</span>
                    <span style={{ ...mutedStyle, width: 24, textAlign: 'right' }}>{fc.lo}°</span>
                  </div>
                )
              })}
            </div>

            {/* Updated */}
            <div style={{ ...mutedStyle, marginTop: 8, textAlign: 'right' }}>
              UPDATED {new Date(wx.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </>
        )
      })()}
    </Panel>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────
export default function Status() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)
  const [ventilating, setVentilating] = useState(false)
  const [ventLoading, setVentLoading] = useState(false)
  const [displayStatus, setDisplayStatus] = useState(null)
  const [displayLoading, setDisplayLoading] = useState(false)

  useEffect(() => {
    const fetch_ = async () => {
      try { const r = await fetch('/api/status/'); setStatus(await r.json()); setError(null) }
      catch { setError('TELEMETRY FEED LOST') }
    }
    const fetchVent = async () => {
      try { const r = await fetch('/api/control/ventilate'); const d = await r.json(); setVentilating(d.ventilating) }
      catch {}
    }
    const fetchDisplay = async () => {
      try { const r = await fetch('/api/display/status'); if (r.ok) setDisplayStatus(await r.json()) }
      catch {}
    }
    fetch_(); fetchVent(); fetchDisplay()
    const t1 = setInterval(fetch_, 2000)
    const t2 = setInterval(fetchVent, 5000)
    const t3 = setInterval(fetchDisplay, 2000)
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3) }
  }, [])

  const toggleVent = async () => {
    setVentLoading(true)
    try { const r = await fetch('/api/control/ventilate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ active: !ventilating }) }); setVentilating((await r.json()).ventilating) }
    catch {}
    setVentLoading(false)
  }

  const switchApp = async (name) => {
    setDisplayLoading(true)
    try {
      const r = await fetch('/api/display/apps/launch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
      if (r.ok) setDisplayStatus(prev => prev ? { ...prev, active_app: name, screensaver_active: false, active_screensaver: null } : prev)
    } catch {}
    setDisplayLoading(false)
  }

  const activateScreensaver = async (name) => {
    setDisplayLoading(true)
    try {
      const r = await fetch('/api/display/screensavers/activate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
      if (r.ok) { const d = await r.json(); setDisplayStatus(prev => prev ? { ...prev, screensaver_active: true, active_screensaver: d.active_screensaver ?? name } : prev) }
    } catch {}
    setDisplayLoading(false)
  }

  const deactivateScreensaver = async () => {
    setDisplayLoading(true)
    try {
      const r = await fetch('/api/display/screensavers/deactivate', { method: 'POST' })
      if (r.ok) setDisplayStatus(prev => prev ? { ...prev, screensaver_active: false, active_screensaver: null } : prev)
    } catch {}
    setDisplayLoading(false)
  }

  const copyToClipboard = (text) => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }

  const bat = status?.battery || {}
  const sys = status?.system || {}
  const net = status?.network || {}
  const conn = status?.connections || {}

  return (
    <div style={{ padding: '12px 12px 24px', fontFamily: "'Share Tech Mono', monospace" }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 14, paddingBottom: 12, borderBottom: '1px solid hsl(214 28% 11%)' }}>
        <div>
          <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 18, letterSpacing: '0.15em', color: 'hsl(191 100% 55%)' }}>SYSTEM TELEMETRY</div>
          <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 38%)', marginTop: 1 }}>TARS UNIT — LIVE READOUT</div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3 }}>
          <Timestamp />
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className={`tars-status-dot ${status ? '' : ''}`} style={{ background: status ? 'hsl(141 70% 45%)' : 'hsl(0 80% 50%)', boxShadow: status ? '0 0 6px hsl(141 70% 45%)' : 'none' }} />
            <span style={{ fontSize: 9, letterSpacing: '0.15em', color: status ? 'hsl(141 70% 55%)' : 'hsl(0 80% 60%)' }}>{status ? 'NOMINAL' : error ? 'FAULT' : 'CONNECTING'}</span>
          </div>
        </div>
      </div>

      {error && !status && (
        <div className="tars-feedback" style={{ marginBottom: 12, borderLeftColor: 'hsl(0 80% 50% / 0.5)', color: 'hsl(0 80% 65%)' }}>{error}</div>
      )}

      {/* Loading skeleton */}
      {!status && !error && (
        <div style={{ fontSize: 10, letterSpacing: '0.15em', color: 'hsl(214 14% 35%)', textAlign: 'center', padding: '40px 0' }}>ACQUIRING TELEMETRY…</div>
      )}

      {status && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* ── Power Cell ──────────────────────────────────────────── */}
          <Panel title="Power Cell" icon={Battery}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'center', marginBottom: 12 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 700, fontSize: 48, color: batteryColor(bat.level ?? 0), lineHeight: 1 }}>{bat.level ?? '—'}</span>
                  <span style={{ fontSize: 14, color: 'hsl(214 14% 45%)', letterSpacing: '0.05em' }}>%</span>
                </div>
                <div style={{ fontSize: 9, letterSpacing: '0.15em', color: 'hsl(214 14% 40%)', marginTop: 2 }}>
                  {bat.level > 60 ? 'CHARGE SUFFICIENT' : bat.level > 20 ? 'CHARGE LOW' : 'CRITICAL — RECHARGE REQUIRED'}
                </div>
              </div>
              <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ fontSize: 9, letterSpacing: '0.12em', color: 'hsl(214 14% 40%)' }}>VOLTAGE</div>
                <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 22, color: 'hsl(191 100% 55%)' }}>{bat.voltage != null ? `${bat.voltage.toFixed(2)}V` : '—'}</div>
                <div style={{ fontSize: 9, letterSpacing: '0.12em', color: 'hsl(214 14% 40%)' }}>CURRENT</div>
                <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 16, color: 'hsl(214 14% 55%)' }}>{bat.current != null ? `${Math.round(bat.current)}mA` : '—'}</div>
              </div>
            </div>
            <GaugeBar value={bat.level ?? 0} max={100} battery />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: 9, letterSpacing: '0.1em', color: 'hsl(214 14% 30%)' }}>
              <span>0%</span><span>50%</span><span>100%</span>
            </div>
          </Panel>

          {/* ── Core Systems ─────────────────────────────────────────── */}
          <Panel title="Core Systems" icon={Cpu}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              <MetricTile label="CPU Load" value={sys.cpu_percent?.toFixed(0)} unit="%" gauge={sys.cpu_percent} warn={70} danger={90} />
              <MetricTile label="Memory" value={sys.memory_percent?.toFixed(0)} unit="%" gauge={sys.memory_percent} warn={75} danger={90} />
              <MetricTile label="Core Temp" value={sys.cpu_temp?.toFixed(1)} unit="°C" gauge={sys.cpu_temp} gaugeMax={85} warn={65} danger={80} />
            </div>
          </Panel>

          {/* ── Display Mode ─────────────────────────────────────────── */}
          {displayStatus && (
            <DisplayPanel
              displayStatus={displayStatus}
              onSwitchApp={switchApp}
              onActivateScreensaver={activateScreensaver}
              onDeactivateScreensaver={deactivateScreensaver}
              loading={displayLoading}
            />
          )}

          {/* ── Weather ──────────────────────────────────────────────── */}
          <WeatherPanel />

          {/* ── Ventilation ──────────────────────────────────────────── */}
          <Panel title="Thermal Management" icon={Wind}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 40%)', marginBottom: 4 }}>VENTILATION STATUS</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: ventilating ? 'hsl(191 100% 44%)' : 'hsl(214 14% 28%)', boxShadow: ventilating ? '0 0 8px hsl(191 100% 44%)' : 'none', animation: ventilating ? 'tars-pulse-cyan 1.2s ease-in-out infinite' : 'none' }} />
                  <span style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 20, color: ventilating ? 'hsl(191 100% 55%)' : 'hsl(214 14% 45%)' }}>
                    {ventilating ? 'ACTIVE' : 'STANDBY'}
                  </span>
                </div>
              </div>
              <button
                onClick={toggleVent}
                disabled={ventLoading}
                className={`tars-btn ${ventilating ? 'tars-btn-cyan' : 'tars-btn-ghost'}`}
                style={{ minWidth: 100 }}
              >
                {ventLoading ? '…' : ventilating ? 'Disable' : 'Enable'}
              </button>
            </div>
          </Panel>

          {/* ── Network ──────────────────────────────────────────────── */}
          <Panel title="Network & Links" icon={Wifi}>
            {net.connection_mode && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <span style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 40%)' }}>CONNECTION MODE</span>
                  <div style={{ position: 'relative', display: 'inline-flex' }} className="tars-info-trigger">
                    <Info size={10} style={{ color: 'hsl(191 100% 44% / 0.6)', cursor: 'default' }} />
                    <div className="tars-info-tip">
                      <div style={{ marginBottom: 4, color: 'hsl(191 100% 55%)', letterSpacing: '0.12em' }}>LOCAL</div>
                      <div style={{ marginBottom: 8, color: 'hsl(214 14% 55%)' }}>Pi on the same LAN/WiFi — direct network access.</div>
                      <div style={{ marginBottom: 4, color: 'hsl(191 100% 55%)', letterSpacing: '0.12em' }}>TAILSCALE</div>
                      <div style={{ color: 'hsl(214 14% 55%)' }}>Routed via Tailscale VPN — works from anywhere.</div>
                    </div>
                  </div>
                </div>
                <div style={{ fontFamily: 'Rajdhani, sans-serif', fontWeight: 600, fontSize: 18, letterSpacing: '0.1em', color: 'hsl(191 100% 55%)', textTransform: 'uppercase', marginBottom: 6 }}>{net.connection_mode}</div>
                {net.connection_mode === 'tailscale' && net.tailscale_ip && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', background: 'hsl(214 35% 5%)', border: '1px solid hsl(214 28% 12%)' }}>
                    <span style={{ flex: 1, fontSize: 11, letterSpacing: '0.06em', color: 'hsl(191 100% 55%)' }}>{net.tailscale_ip}</span>
                    <button
                      onClick={() => copyToClipboard(net.tailscale_ip)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: copied ? 'hsl(141 70% 50%)' : 'hsl(214 14% 40%)', display: 'flex', padding: 4 }}
                    >
                      {copied ? <Check size={14} /> : <Copy size={14} />}
                    </button>
                  </div>
                )}
              </div>
            )}
            <div>
              <div style={{ fontSize: 9, letterSpacing: '0.2em', color: 'hsl(214 14% 40%)', marginBottom: 8 }}>SUBSYSTEM LINKS</div>
              <ConnRow label="WebRTC" active={conn.webrtc} />
              <ConnRow label="gRPC" active={conn.grpc} />
            </div>
          </Panel>

        </div>
      )}
    </div>
  )
}
