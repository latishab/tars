# TARS Dashboard

Web interface for monitoring and controlling TARS robot.

## Access

TARS supports multiple access methods:

### Local Network (mDNS)
```bash
http://tars.local:8000
```
- Works on home WiFi networks
- Does NOT work on dorm/corporate networks (client isolation)

### Tailscale VPN
```bash
http://100.x.x.x:8000
```
- Works from anywhere (dorm, corporate, mobile data)
- Requires Tailscale setup
- Your specific IP shown in setup wizard

### Direct IP (Local Network)
```bash
http://<raspberry-pi-ip>:8000
```
- Fallback method if mDNS not working
- Only works on same local network

📖 **[WiFi Setup Guide](./WIFI_SETUP.md)** - Complete WiFi configuration and troubleshooting guide

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
System configuration and network management.

#### Network Configuration

**Current Status**
- Connection state (Connected / Hotspot / Disconnected)
- Network name (SSID)
- Local IP address
- Dashboard access URLs (tars.local and Tailscale)

**WiFi Management**
- Scan for available networks
- Signal strength indicators
- Security type display (WPA2, Enterprise, Open)
- Network selection with password entry

**Connection Confirmation**
Before connecting to new WiFi, a modal shows:
- Tailscale URL (works everywhere)
- tars.local URL (home networks only)
- Clear warning about hotspot shutdown
- "Connect Now" button to proceed

This prevents being locked out when switching networks.

**Supported Network Types**

*Personal WiFi*
- WPA/WPA2 password-protected networks
- Open networks (no password)
- Standard home/cafe WiFi

*Enterprise WiFi (WPA2-Enterprise)*
- PEAP authentication
- MSCHAPv2 phase2
- Username + password required
- Common on university/corporate networks

*Manual Entry*
- Enter hidden network SSID
- Toggle between Personal/Enterprise modes
- Useful for networks not appearing in scan

**Hotspot Controls**
- Start TARS-Setup hotspot manually
- Stop active hotspot
- Useful for troubleshooting or reconfiguration

#### System Updates

**Version Information**
- Current software version
- Git commit hash

**Update Management**
- Check for updates button
- Install updates with one click
- Automatic update notifications
- Restart service control

## Initial Setup

On first boot, TARS starts a WiFi hotspot:

```
SSID: TARS-Setup
Password: tars1234
Access: http://10.42.0.1:8000/setup
```

The setup wizard guides through:
1. WiFi network selection
2. Connection mode (Local vs Tailscale)
3. API key configuration

See [WiFi Setup Guide](./WIFI_SETUP.md) for detailed instructions.

## Boot Behavior

TARS follows this WiFi priority on boot:

1. **Try known WiFi networks** - Auto-connect to saved networks
2. **No connection found** - Start TARS-Setup hotspot automatically
3. **Tailscale** - Connects independently when internet available

No manual intervention needed for normal operation.

## Starting the Dashboard

The dashboard starts automatically with the daemon:

```bash
# Via daemon
python tars_daemon.py

# Or standalone
python start_dashboard.py
```

Default port: 8000

## Architecture

```
Dashboard
├── Backend (FastAPI)
│   ├── /api/status - System metrics
│   ├── /api/movements - Movement controls
│   ├── /api/apps - App management
│   ├── /api/wifi - WiFi management
│   ├── /api/setup - Initial setup wizard
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
uvicorn server:app --reload --port 8000
```

## App Store API

### Install App

```bash
curl -X POST http://localhost:8000/api/apps/install \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "tars-conversation",
    "repository": "https://github.com/latishab/tars-conversation-app.git"
  }'
```

### List Apps

```bash
curl http://localhost:8000/api/apps
```

### Run App

```bash
curl -X POST http://localhost:8000/api/apps/run \
  -H "Content-Type: application/json" \
  -d '{"app_id": "tars-conversation-app"}'
```

### Stop App

```bash
curl -X POST http://localhost:8000/api/apps/stop \
  -H "Content-Type: application/json" \
  -d '{"app_id": "tars-conversation-app"}'
```

## WiFi API

### Get Status

```bash
curl http://localhost:8000/api/wifi/status
```

Returns:
```json
{
  "mode": "client",
  "ssid": "MyHomeWiFi",
  "ip": "192.168.1.100",
  "tailscale_ip": "100.84.133.74"
}
```

### Scan Networks

```bash
curl http://localhost:8000/api/wifi/networks
```

### Connect to Network

```bash
curl -X POST http://localhost:8000/api/wifi/connect \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "NetworkName",
    "password": "password123",
    "is_enterprise": false
  }'
```

### Connect to Enterprise WiFi

```bash
curl -X POST http://localhost:8000/api/wifi/connect \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "UniversityWiFi",
    "username": "student123",
    "password": "password",
    "is_enterprise": true,
    "eap_method": "peap",
    "phase2_auth": "mschapv2"
  }'
```

### Start/Stop Hotspot

```bash
# Start hotspot
curl -X POST http://localhost:8000/api/wifi/hotspot/start

# Stop hotspot
curl -X POST http://localhost:8000/api/wifi/hotspot/stop
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

2. Check port 8000 is not in use:
   ```bash
   lsof -i:8000
   ```

3. Restart dashboard:
   ```bash
   sudo systemctl restart tars-dashboard
   ```

### Cannot access tars.local

If `tars.local` doesn't work:
- You're likely on dorm/corporate WiFi (client isolation)
- Use Tailscale URL instead: `http://100.x.x.x:8000`
- See Settings → Network for your Tailscale IP
- Refer to [WiFi Setup Guide](./WIFI_SETUP.md) for details

### Apps not showing

1. Check ~/tars-apps/ directory exists
2. Verify app.json in each app directory
3. Check API endpoint: `curl http://localhost:8000/api/apps`

### WebSocket disconnecting

- Check firewall settings
- Verify network stability
- Check browser console for errors

### WiFi connection issues

See [WiFi Setup Guide](./WIFI_SETUP.md) for comprehensive troubleshooting.
