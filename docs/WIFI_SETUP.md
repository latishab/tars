# WiFi Setup

## Access Methods

| Method | URL | Works on |
|---|---|---|
| Local (mDNS) | `http://tars.local:8000` | Home networks, personal hotspot |
| Tailscale | `http://tars:8000` | Anywhere (dorms, corporate, mobile) |
| Direct IP | `http://<ip>:8000` | Same local network |

## First Boot

TARS creates a setup hotspot when no WiFi is configured:

```
SSID: TARS-Setup
Password: tars1234
Setup URL: http://10.42.0.1:8000/setup
```

1. Connect to **TARS-Setup** WiFi
2. Open `http://10.42.0.1:8000/setup`
3. Select your WiFi and enter credentials
4. (Optional) Enter Tailscale auth key for remote access
5. **Save the dashboard URLs** shown before clicking Connect — the hotspot shuts down immediately

## Changing Networks

Settings → Network → Change Network.

**Supported types:** Personal (WPA/WPA2), Enterprise (PEAP/MSCHAPv2), Open, Hidden SSID

## Tailscale

For access from dorms, corporate networks, or anywhere with internet:

1. Create account at [tailscale.com](https://tailscale.com)
2. Generate auth key at [login.tailscale.com/admin/settings/keys](https://login.tailscale.com/admin/settings/keys)
3. Enter auth key during WiFi setup
4. Install Tailscale on your devices → access at `http://tars:8000`

## Troubleshooting

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
