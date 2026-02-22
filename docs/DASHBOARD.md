# Dashboard

Web interface for monitoring and controlling TARS. Access at `http://tars.local:8000` or via Tailscale.

See [WiFi Setup](./WIFI_SETUP.md) for network configuration and access details.

---

## Tabs

### Status
Real-time monitoring: battery level/voltage/current, CPU, memory, connection status (WiFi, WebRTC, gRPC), current emotion and eye state.

### Control
Movement controls: directional pad, gesture buttons, emotion picker. Shows execution feedback.

### Apps
Browse, install, and manage TARS apps.

Apps install to `~/tars-apps/`. Each app requires an `app.json` manifest:

```json
{
  name: my-app,
  version: 1.0.0,
  description: Description,
  repository: https://github.com/user/my-app.git,
  main: main.py,
  install_script: install.sh
}
```

### Settings
- **Network**: WiFi selection, hotspot controls
- **Updates**: Check and install software updates (restarts service automatically)

---

## Development

### Frontend

```bash
cd dashboard/frontend
npm install
npm run dev     # Dev server
npm run build   # Production build
```

### Backend

```bash
cd dashboard/backend
uvicorn server:app --reload --port 8000
```

---

## Troubleshooting

**Dashboard not loading:**
```bash
ssh tars-pi sudo systemctl status tars
ssh tars-pi sudo systemctl restart tars
```

**Apps not showing:** Verify `~/tars-apps/` exists and each app has `app.json`.

**WiFi or access issues:** See [WiFi Setup](./WIFI_SETUP.md).
