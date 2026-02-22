# WiFi Setup

## 🌐 Access Methods

| Method | URL | Works on |
|---|---|---|
| Local (mDNS) | `http://tars.local:8000` | Home networks, personal hotspot |
| Tailscale | `http://tars:8000` | Anywhere (dorms, corporate, mobile) |
| Direct IP | `http://<ip>:8000` | Same local network |

## 🚀 First Boot

TARS creates a setup hotspot when no WiFi is configured:

```
SSID: TARS-Setup
Password: tars1234
Setup URL: http://tars.local:8000/setup
```

1. Connect to **TARS-Setup** WiFi
2. Open `http://tars.local:8000/setup`
3. Select your WiFi and enter credentials
4. (Optional) Enter Tailscale auth key for remote access
5. **Save the dashboard URLs** shown before clicking Connect — the hotspot shuts down immediately

## 🔐 Tailscale (Remote Access)

For access from anywhere — dorms, corporate networks, or mobile:

1. Create account at [tailscale.com](https://tailscale.com)
2. Generate an auth key at Admin — Settings — Keys
3. Enter the auth key in the WiFi setup wizard (or via `ssh tars-pi "sudo tailscale up --authkey=<key>"`)
4. Install Tailscale on your devices
5. **Enable MagicDNS** in the Tailscale admin panel (DNS tab — Enable MagicDNS)

With MagicDNS enabled, TARS is reachable at `http://tars:8000` from any device on your Tailscale network.

Without MagicDNS, use the numeric IP shown in [login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines).

## 🔄 Changing Networks

Settings → Network → Change Network.

**Supported types:** Personal (WPA/WPA2), Enterprise (PEAP/MSCHAPv2), Open, Hidden SSID

## 🔍 Troubleshooting

**tars.local not working:** You're on a network with client isolation (dorms, corporate). Use Tailscale.

**Forgot Tailscale IP:**
- Home WiFi: `http://tars.local:8000` → Settings → Network shows Tailscale IP
- Tailscale admin: [login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines)
- SSH: `ssh tars-pi tailscale ip -4`

**WiFi won't connect:** Verify password. For enterprise WiFi, confirm PEAP/MSCHAPv2 credentials.

**Hotspot not starting:**
```bash
ssh tars-pi sudo systemctl status tars
ssh tars-pi journalctl -u tars -n 50
```
