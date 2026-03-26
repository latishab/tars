import { useRef, useEffect, useState, useCallback } from 'react'
import * as THREE from 'three'
import { Play, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'

// ── Geometry constants ──────────────────────────────────────────────────────
const SEG_WIDTH  = 1.4
const SEG_HEIGHT = 7.0
const SEG_DEPTH  = 2.1
const GAP        = 0.15
const SMOOTH     = 0.12

// ── Locomotion map (same as Dev branch) ───────────────────────────────────
// Locomotion direction hint — backward movements reverse the body drift
const BACKWARD_MAP = { walk_backward: true, step_backward: true }

// ── Texture helpers ────────────────────────────────────────────────────────
function makeOuterTexture() {
  const c = document.createElement('canvas')
  c.width = 512; c.height = 1024
  const ctx = c.getContext('2d')
  ctx.fillStyle = '#1a1a1a'; ctx.fillRect(0, 0, 512, 1024)
  const step = 64
  ctx.fillStyle = '#222222'; ctx.strokeStyle = '#111111'; ctx.lineWidth = 4
  for (let y = 0; y < 350; y += step)
    for (let x = 0; x < 512; x += step) {
      ctx.fillRect(x + 2, y + 2, step - 4, step - 4)
      ctx.strokeRect(x, y, step, step)
    }
  ctx.fillStyle = 'rgba(255,255,255,0.02)'
  for (let i = 0; i < 1000; i++) ctx.fillRect(Math.random() * 512, Math.random() * 1024, 2, 2)
  return new THREE.CanvasTexture(c)
}

function makeCenterTexture() {
  const c = document.createElement('canvas')
  c.width = 1024; c.height = 1024
  const ctx = c.getContext('2d')
  ctx.fillStyle = '#bbbbbb'; ctx.fillRect(0, 0, 1024, 1024)
  ctx.fillStyle = '#111111'
  ctx.fillRect(0, 750, 1024, 120)
  ctx.fillRect(0, 150, 150, 100)
  ctx.fillRect(874, 150, 150, 100)
  ctx.strokeStyle = '#888888'; ctx.lineWidth = 3
  ctx.beginPath(); ctx.moveTo(512, 0); ctx.lineTo(512, 1024); ctx.stroke()
  ;[300, 450, 600, 900].forEach(yy => {
    ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(1024, yy); ctx.stroke()
  })
  ctx.fillStyle = '#cca300'; ctx.font = 'bold 80px monospace'
  ctx.save(); ctx.translate(140, 500); ctx.rotate(-Math.PI / 2)
  ctx.fillText('TARS', 0, 0); ctx.restore()
  return new THREE.CanvasTexture(c)
}

function makeScreenTexture() {
  const c = document.createElement('canvas')
  c.width = 256; c.height = 512
  const ctx = c.getContext('2d')
  ctx.fillStyle = '#001133'; ctx.fillRect(0, 0, 256, 512)
  ctx.fillStyle = '#00aaff'; ctx.fillRect(10, 10, 236, 30)
  for (let i = 60; i < 450; i += 10) {
    ctx.fillStyle = `rgba(0,170,255,${Math.random()})`
    ctx.fillRect(10, i, Math.random() * 100 + 10, 4)
  }
  ctx.strokeStyle = '#00aaff'; ctx.lineWidth = 2
  ctx.strokeRect(40, 150, 176, 200)
  return new THREE.CanvasTexture(c)
}

// ── Step helpers ───────────────────────────────────────────────────────────
function flattenSteps(steps) {
  const out = []
  for (const s of steps) {
    if (s.repeat !== undefined && s.steps) {
      for (let r = 0; r < s.repeat; r++)
        flattenSteps(s.steps).forEach(inner => out.push(inner))
    } else {
      out.push(s)
    }
  }
  return out
}

function resolveSteps(steps) {
  let pLH = 50, pRH = 50, pLL = 50, pRL = 50
  return steps.map(s => {
    const lh = (s.left_height  && s.left_height  !== 0) ? s.left_height  : pLH
    const rh = (s.right_height && s.right_height !== 0) ? s.right_height : pRH
    const ll = (s.left_leg     && s.left_leg     !== 0) ? s.left_leg     : pLL
    const rl = (s.right_leg    && s.right_leg    !== 0) ? s.right_leg    : pRL
    pLH = lh; pRH = rh; pLL = ll; pRL = rl
    return { ...s, left_height: lh, right_height: rh, left_leg: ll, right_leg: rl }
  })
}

function mapStepToPose(step) {
  const lh = ((step.left_height  || 50) - 50) / 50
  const rh = ((step.right_height || 50) - 50) / 50
  const ll = ((step.left_leg     || 50) - 50) / 50
  const rl = ((step.right_leg    || 50) - 50) / 50
  return { leftHeight: lh * 0.5, rightHeight: rh * 0.5, leftSwing: -ll * 0.5, rightSwing: -rl * 0.5 }
}

// ── Stateless helpers that operate on the mutable state object ─────────────
function applyPose(state, pose) {
  const segs = state.segments
  if (!segs || segs.length < 3) return
  segs[0].pivot.position.y = SEG_HEIGHT - pose.leftHeight
  segs[1].pivot.position.y = SEG_HEIGHT
  segs[2].pivot.position.y = SEG_HEIGHT - pose.rightHeight
  segs[0].pivot.rotation.x = pose.leftSwing
  segs[2].pivot.rotation.x = pose.rightSwing
}

function resetPoseState(state) {
  state.sBodyY = 0; state.sBodyZ = 0; state.sTwist = 0; state.sYaw = 0
  state.prevLeftSwing = 0; state.prevRightSwing = 0
  applyPose(state, { leftHeight: 0, rightHeight: 0, leftSwing: 0, rightSwing: 0 })
  if (state.tarsGroup) {
    state.tarsGroup.position.set(0, 0, 0)
    state.tarsGroup.rotation.set(0, 0, 0)
  }
}

function doStop(state, setPlaying) {
  state.playing = false
  state.allowLoco = false
  if (state.timerId) { clearTimeout(state.timerId); state.timerId = null }
  resetPoseState(state)
  setPlaying(false)
}

function doAnimStep(state, setPlaying) {
  if (!state.playing || state.animIndex >= state.animSteps.length) {
    doStop(state, setPlaying)
    return
  }
  const step = state.animSteps[state.animIndex]
  const targetPose = mapStepToPose(step)
  const speed   = step.speed || 0.85
  const holdMs  = (step.hold_time || 0) * 1000
  const transMs = (1.1 - speed) * 800 + 100
  const startPose = state.animIndex > 0
    ? mapStepToPose(state.animSteps[state.animIndex - 1])
    : { leftHeight: 0, rightHeight: 0, leftSwing: 0, rightSwing: 0 }
  const startTime = performance.now()

  function tween() {
    if (!state.playing) return
    const t0 = Math.min((performance.now() - startTime) / transMs, 1)
    const t  = t0 < 0.5 ? 2 * t0 * t0 : 1 - Math.pow(-2 * t0 + 2, 2) / 2
    applyPose(state, {
      leftHeight:  startPose.leftHeight  + (targetPose.leftHeight  - startPose.leftHeight)  * t,
      rightHeight: startPose.rightHeight + (targetPose.rightHeight - startPose.rightHeight) * t,
      leftSwing:   startPose.leftSwing   + (targetPose.leftSwing   - startPose.leftSwing)   * t,
      rightSwing:  startPose.rightSwing  + (targetPose.rightSwing  - startPose.rightSwing)  * t,
    })
    if (t < 1) {
      requestAnimationFrame(tween)
    } else {
      state.timerId = setTimeout(() => {
        state.animIndex++
        doAnimStep(state, setPlaying)
      }, holdMs)
    }
  }
  requestAnimationFrame(tween)
}

// ── Component ──────────────────────────────────────────────────────────────
export default function TarsPreview({ steps, movementName = '', isLocomotion = false }) {
  const containerRef = useRef(null)
  const stRef = useRef(null)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const state = {
      scene: null, camera: null, renderer: null,
      tarsGroup: null, segments: null,
      rafId: null,
      sBodyY: 0, sBodyZ: 0, sTwist: 0, sYaw: 0,
      prevLeftSwing: 0, prevRightSwing: 0,
      animSteps: [], animIndex: 0, timerId: null,
      playing: false, allowLoco: false, locoDir: 1,
    }
    stRef.current = state

    // Scene
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a14)
    state.scene = scene

    const w = container.clientWidth || 400
    const h = container.clientHeight || 300
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 100)
    camera.position.set(6, 6, 10)
    camera.lookAt(0, 3, 0)
    state.camera = camera

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(w, h)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    container.appendChild(renderer.domElement)
    state.renderer = renderer

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.4))
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6)
    dirLight.position.set(5, 10, 5); dirLight.castShadow = true
    scene.add(dirLight)
    const pl = new THREE.PointLight(0x00aaff, 0.4, 20)
    pl.position.set(-4, 6, -3); scene.add(pl)

    // Ground + grid
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(20, 20),
      new THREE.MeshStandardMaterial({ color: 0x111118, roughness: 0.9, metalness: 0.1 })
    )
    ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true
    scene.add(ground)
    const grid = new THREE.GridHelper(20, 20, 0x222233, 0x151522)
    grid.position.y = 0.01; scene.add(grid)

    // TARS model
    const tarsGroup = new THREE.Group()
    const segments = []
    const outerMat  = new THREE.MeshStandardMaterial({ map: makeOuterTexture(),  roughness: 0.7, metalness: 0.3 })
    const centerMat = new THREE.MeshStandardMaterial({ map: makeCenterTexture(), roughness: 0.4, metalness: 0.6 })
    const screenMat = new THREE.MeshBasicMaterial({ map: makeScreenTexture() })
    const bodyW = SEG_WIDTH * 2 + GAP
    const configs = [
      { width: SEG_WIDTH, mat: outerMat,  x: -(bodyW / 2 + SEG_WIDTH / 2 + GAP) },
      { width: bodyW,     mat: centerMat, x: 0 },
      { width: SEG_WIDTH, mat: outerMat,  x:  (bodyW / 2 + SEG_WIDTH / 2 + GAP) },
    ]
    configs.forEach((cfg, i) => {
      const geo  = new THREE.BoxGeometry(cfg.width, SEG_HEIGHT, SEG_DEPTH)
      const mesh = new THREE.Mesh(geo, cfg.mat)
      mesh.castShadow = true
      const pivot = new THREE.Group()
      pivot.position.set(cfg.x, SEG_HEIGHT, 0)
      mesh.position.y = -SEG_HEIGHT / 2
      pivot.add(mesh)
      if (i === 1) {
        const sw = bodyW * 0.6, sh = SEG_HEIGHT * 0.4
        const scrMesh = new THREE.Mesh(new THREE.PlaneGeometry(sw, sh), screenMat)
        scrMesh.position.set(0, 0.3, SEG_DEPTH / 2 + 0.01)
        mesh.add(scrMesh)
        const sLight = new THREE.PointLight(0x00aaff, 0.3, 1.5)
        sLight.position.set(0, 0.3, SEG_DEPTH / 2 + 0.2)
        mesh.add(sLight)
      }
      tarsGroup.add(pivot)
      segments.push({ pivot, mesh })
    })
    scene.add(tarsGroup)
    state.tarsGroup = tarsGroup
    state.segments  = segments

    // Orbit controls
    let isDragging = false, isPanning = false
    let prevX = 0, prevY = 0, touchStartDist = 0
    const spherical = { theta: 0.6, phi: 1.0, radius: 13 }
    const target = new THREE.Vector3(0, 3, 0)

    function updateCam() {
      const { radius: r, phi, theta } = spherical
      camera.position.set(
        target.x + r * Math.sin(phi) * Math.sin(theta),
        target.y + r * Math.cos(phi),
        target.z + r * Math.sin(phi) * Math.cos(theta)
      )
      camera.lookAt(target)
    }
    updateCam()

    const onMouseDown = e => {
      if (e.button === 0) isDragging = true
      if (e.button === 2) isPanning = true
      prevX = e.clientX; prevY = e.clientY; e.preventDefault()
    }
    const onCtxMenu = e => e.preventDefault()
    const onMouseMove = e => {
      const dx = e.clientX - prevX, dy = e.clientY - prevY
      prevX = e.clientX; prevY = e.clientY
      if (isDragging) {
        spherical.theta -= dx * 0.005
        spherical.phi = Math.max(0.2, Math.min(Math.PI - 0.2, spherical.phi - dy * 0.005))
        updateCam()
      }
      if (isPanning) {
        const right = new THREE.Vector3()
        camera.getWorldDirection(right)
        right.cross(new THREE.Vector3(0, 1, 0)).normalize()
        target.addScaledVector(right, -dx * 0.02)
        target.y += dy * 0.02
        updateCam()
      }
    }
    const onMouseUp   = () => { isDragging = false; isPanning = false }
    const onWheel = e => {
      spherical.radius = Math.max(5, Math.min(30, spherical.radius + e.deltaY * 0.01))
      updateCam(); e.preventDefault()
    }
    const onTouchStart = e => {
      if (e.touches.length === 1) {
        isDragging = true; prevX = e.touches[0].clientX; prevY = e.touches[0].clientY
      } else if (e.touches.length === 2) {
        isDragging = false
        const ddx = e.touches[0].clientX - e.touches[1].clientX
        const ddy = e.touches[0].clientY - e.touches[1].clientY
        touchStartDist = Math.sqrt(ddx * ddx + ddy * ddy)
      }
    }
    const onTouchMove = e => {
      e.preventDefault()
      if (e.touches.length === 1 && isDragging) {
        const dx = e.touches[0].clientX - prevX, dy = e.touches[0].clientY - prevY
        prevX = e.touches[0].clientX; prevY = e.touches[0].clientY
        spherical.theta -= dx * 0.005
        spherical.phi = Math.max(0.2, Math.min(Math.PI - 0.2, spherical.phi - dy * 0.005))
        updateCam()
      } else if (e.touches.length === 2) {
        const ddx = e.touches[0].clientX - e.touches[1].clientX
        const ddy = e.touches[0].clientY - e.touches[1].clientY
        const dist = Math.sqrt(ddx * ddx + ddy * ddy)
        spherical.radius = Math.max(5, Math.min(30, spherical.radius + (touchStartDist - dist) * 0.03))
        touchStartDist = dist; updateCam()
      }
    }

    container.addEventListener('mousedown', onMouseDown)
    container.addEventListener('contextmenu', onCtxMenu)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    container.addEventListener('wheel', onWheel, { passive: false })
    container.addEventListener('touchstart', onTouchStart)
    container.addEventListener('touchmove', onTouchMove, { passive: false })
    container.addEventListener('touchend', () => { isDragging = false })

    // Render loop (constraint-based physics)
    function loop() {
      state.rafId = requestAnimationFrame(loop)
      const segs = state.segments
      if (!segs || segs.length < 3) { renderer.render(scene, camera); return }

      const leftSwing   = segs[0].pivot.rotation.x
      const rightSwing  = segs[2].pivot.rotation.x
      const leftPivotY  = segs[0].pivot.position.y
      const rightPivotY = segs[2].pivot.position.y
      const leftHeight  = SEG_HEIGHT - leftPivotY
      const rightHeight = SEG_HEIGHT - rightPivotY

      state.sBodyY += (Math.max(leftHeight, rightHeight, 0) - state.sBodyY) * SMOOTH
      tarsGroup.position.y = state.sBodyY

      segs[1].pivot.rotation.x = 0
      state.sTwist += ((leftSwing - rightSwing) * 0.4 - state.sTwist) * SMOOTH
      segs[1].pivot.rotation.y = state.sTwist
      segs[1].pivot.rotation.z = 0

      const leftDelta  = leftSwing  - state.prevLeftSwing
      const rightDelta = rightSwing - state.prevRightSwing
      if (state.allowLoco) {
        if (leftPivotY <= rightPivotY) {
          if (leftDelta < 0) state.sBodyZ -= leftDelta * 5.0 * state.locoDir
        } else {
          if (rightDelta < 0) state.sBodyZ -= rightDelta * 5.0 * state.locoDir
        }
        const diff = leftDelta - rightDelta
        if (Math.abs(diff) > 0.001) state.sYaw += diff * 2.0
      }
      state.prevLeftSwing  = leftSwing
      state.prevRightSwing = rightSwing
      tarsGroup.position.z = state.sBodyZ
      tarsGroup.rotation.set(0, state.sYaw, 0)

      renderer.render(scene, camera)
    }
    loop()

    // Resize observer
    const ro = new ResizeObserver(() => {
      const cw = container.clientWidth, ch = container.clientHeight
      if (cw > 0 && ch > 0) {
        camera.aspect = cw / ch
        camera.updateProjectionMatrix()
        renderer.setSize(cw, ch)
      }
    })
    ro.observe(container)

    return () => {
      ro.disconnect()
      container.removeEventListener('mousedown', onMouseDown)
      container.removeEventListener('contextmenu', onCtxMenu)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
      container.removeEventListener('wheel', onWheel)
      container.removeEventListener('touchstart', onTouchStart)
      container.removeEventListener('touchmove', onTouchMove)
      if (state.rafId) cancelAnimationFrame(state.rafId)
      if (state.timerId) clearTimeout(state.timerId)
      renderer.dispose()
      if (container.contains(renderer.domElement)) container.removeChild(renderer.domElement)
      stRef.current = null
    }
  }, [])

  const play = useCallback(() => {
    const state = stRef.current
    if (!state) return
    const animSteps = resolveSteps(flattenSteps(steps).filter(s => !s.movement))
    if (animSteps.length === 0) return
    state.animSteps = animSteps
    state.animIndex = 0
    state.playing   = true
    state.allowLoco = isLocomotion
    state.locoDir   = BACKWARD_MAP[movementName] ? -1 : 1
    setPlaying(true)
    doAnimStep(state, setPlaying)
  }, [steps, movementName, isLocomotion])

  const stop = useCallback(() => {
    const state = stRef.current
    if (!state) return
    doStop(state, setPlaying)
  }, [])

  return (
    <div className="flex flex-col gap-2">
      <div
        ref={containerRef}
        className="w-full rounded-lg overflow-hidden tars-no-invert"
        style={{ height: '320px', background: '#0a0a14' }}
      />
      <div className="flex gap-2">
        {!playing ? (
          <Button size="sm" onClick={play} className="flex-1">
            <Play className="w-4 h-4 mr-1" />
            Preview
          </Button>
        ) : (
          <Button size="sm" onClick={stop} className="flex-1">
            <Square className="w-4 h-4 mr-1" />
            Stop Preview
          </Button>
        )}
      </div>
    </div>
  )
}
