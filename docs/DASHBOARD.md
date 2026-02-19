# TARS Dashboard

Web interface for monitoring and controlling TARS robot.

## Access

```bash
# Local network
http://tars-pi.local:8080

# Direct IP
http://<raspberry-pi-ip>:8080
```

## Features

### Status Tab
Real-time system monitoring:
- Battery level, voltage, current
- CPU usage and temperature
- Memory usage
- Network connection status (WiFi, WebRTC, gRPC)
- Display emotion and eye state

### Control Tab
Movement controls:
- Virtual joystick for directional movements
- Pre-programmed gestures (wave, nod, shake, etc.)
- Real-time feedback

### Apps Tab
App marketplace for TARS:
- Official and community apps in single unified list
- Featured apps marked with star icon
- Install/Uninstall apps with one click
- Run/Stop controls for installed apps
- Status indicators (installed, running)
- Direct links to app repositories

### Settings Tab
System configuration:
- WiFi network management
- Software updates
- System settings

## Starting the Dashboard

The dashboard starts automatically with the daemon:

```bash
# Via daemon
python tars_daemon.py

# Or standalone
python start_dashboard.py
```

Default port: 8080

## Architecture

```
Dashboard
├── Backend (FastAPI)
│   ├── /api/status - System metrics
│   ├── /api/movements - Movement controls
│   ├── /api/apps - App management
│   ├── /api/settings - Configuration
│   └── /ws - WebSocket updates
│
└── Frontend (React + Vite)
    ├── Tailwind CSS styling
    ├── shadcn/ui components
    └── Real-time updates via WebSocket
```

## Development

### Frontend Build

```bash
cd dashboard/frontend
npm install
npm run dev     # Development server
npm run build   # Production build
```

### Backend Development

```bash
cd dashboard/backend
uvicorn server:app --reload --port 8080
```

## App Store API

### Install App

```bash
curl -X POST http://localhost:8080/api/apps/install \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "tars-conversation",
    "repository": "https://github.com/latishab/tars-conversation-app.git"
  }'
```

### List Apps

```bash
curl http://localhost:8080/api/apps
```

### Run App

```bash
curl -X POST http://localhost:8080/api/apps/run \
  -H "Content-Type: application/json" \
  -d '{"app_id": "tars-conversation-app"}'
```

### Stop App

```bash
curl -X POST http://localhost:8080/api/apps/stop \
  -H "Content-Type: application/json" \
  -d '{"app_id": "tars-conversation-app"}'
```

## App Store Integration

Apps are installed in `~/tars-apps/` and must include an `app.json` manifest:

```json
{
  "name": "my-tars-app",
  "version": "1.0.0",
  "description": "My TARS application",
  "author": "username",
  "repository": "https://github.com/username/my-app.git",
  "main": "main.py",
  "install_script": "install.sh",
  "uninstall_script": "uninstall.sh"
}
```

## Troubleshooting

### Dashboard not accessible

1. Check dashboard is running:
   ```bash
   ps aux | grep start_dashboard
   ```

2. Check port 8080 is not in use:
   ```bash
   lsof -i:8080
   ```

3. Restart dashboard:
   ```bash
   pkill -f start_dashboard
   python start_dashboard.py
   ```

### Apps not showing

1. Check ~/tars-apps/ directory exists
2. Verify app.json in each app directory
3. Check API endpoint: `curl http://localhost:8080/api/apps`

### WebSocket disconnecting

- Check firewall settings
- Verify network stability
- Check browser console for errors
