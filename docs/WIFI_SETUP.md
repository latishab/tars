# WiFi Setup Guide

Complete guide for configuring TARS WiFi connectivity.

## Overview

TARS supports multiple WiFi access methods:
- **Local Network (mDNS)**: `http://tars.local:8080` - Works on home networks
- **Tailscale VPN**: `http://100.x.x.x:8080` - Works everywhere (dorms, corporate networks, mobile data)

## Initial Setup

### 1. First Boot

On first boot or when no WiFi is configured, TARS automatically starts a setup hotspot:

```
SSID: TARS-Setup
Password: tars1234
IP: 10.42.0.1:8080
```

### 2. Connect to Hotspot

From your phone or laptop:
1. Connect to **TARS-Setup** WiFi network
2. Enter password: `tars1234`
3. Open browser to `http://10.42.0.1:8080/setup`

### 3. Setup Wizard

The setup wizard guides you through 3 steps:

**Step 1: Select WiFi Network**
- Scans for available networks
- Shows signal strength and security type
- Select your home/work WiFi

**Step 2: Connection Mode**
- **Local Network**: For home WiFi (uses mDNS)
- **Tailscale**: For dorm/corporate networks (requires auth key)

**Step 3: API Keys**
- Anthropic API key (required)
- Deepgram API key (optional)

### 4. Connection Confirmation

Before connecting, you'll see a confirmation modal showing:

```
📋 Save these URLs before connecting:

Tailscale (works everywhere):
http://100.84.133.74:8080

Local network (home WiFi only):
http://tars.local:8080

⚠️ After clicking "Connect Now":
1. TARS will connect to your WiFi
2. This setup page will disconnect (hotspot shuts down)
3. Reconnect your device to your WiFi
4. Open the Tailscale URL above to access TARS
```

**Important**: The modal stays open until you click **"Connect Now"**. This gives you time to:
- Copy/save the URLs
- Screenshot the information
- Write down the Tailscale IP

### 5. Reconnect

After clicking "Connect Now":
1. The hotspot shuts down (setup page disconnects)
2. TARS connects to your WiFi
3. Reconnect your device to the same WiFi network
4. Access dashboard at saved URL

## Access Methods

### Local Network (tars.local)

**Works on:**
- Home WiFi networks
- Personal hotspots
- Networks without client isolation

**Access URL:**
```
http://tars.local:8080
```

**How it works:**
- Uses mDNS (Multicast DNS) for hostname resolution
- Requires devices on same network segment
- No additional setup needed

**Limitations:**
- Does NOT work on dorm/university WiFi (client isolation)
- Does NOT work on corporate networks (mDNS blocked)
- Only works when on same WiFi as TARS

### Tailscale VPN

**Works on:**
- Any network (dorm, corporate, home)
- Mobile data (4G/5G)
- Different WiFi networks
- Anywhere with internet

**Access URL:**
```
http://100.x.x.x:8080
```
(Your specific IP shown in setup modal)

**How it works:**
- Creates encrypted VPN mesh network
- Assigns consistent IP address (100.x.x.x range)
- Works across different networks

**Requirements:**
1. Tailscale account (free): https://tailscale.com
2. Auth key from: https://login.tailscale.com/admin/settings/keys
3. Devices must be on same Tailscale network

**Setup:**
1. Create Tailscale account
2. Generate auth key (reusable recommended)
3. Enter auth key in setup wizard
4. Install Tailscale on your devices
5. Access TARS from anywhere

## Settings Page

After initial setup, manage WiFi from Settings page:

### Network Information

Shows current connection:
- **Status**: Connected / Hotspot Active / Disconnected
- **Network**: SSID name
- **IP Address**: Local IP
- **Dashboard Access**: Both tars.local and Tailscale URLs

### Change Network

Click "Change Network" to:
1. Scan for available networks
2. Select new network
3. Enter credentials
4. Confirm connection (see URLs before connecting)

### Network Types Supported

**Personal WiFi**
- Standard WPA/WPA2 networks
- Open networks
- Password-protected

**Enterprise WiFi (WPA2-Enterprise)**
- PEAP authentication
- MSCHAPv2 phase2
- Requires username + password
- Common on university/corporate networks

**Manual Entry**
- Enter hidden network SSID manually
- Toggle between Personal/Enterprise
- Useful for networks not appearing in scan

### Hotspot Controls

**Start Hotspot**
- Manually start TARS-Setup hotspot
- Useful for troubleshooting or reconfiguration

**Stop Hotspot**
- Deactivate setup hotspot
- Only available when hotspot is running

## Boot Behavior

TARS WiFi follows this priority on boot:

1. **Try Known Networks**: Automatically connect to previously saved WiFi
2. **No Connection Found**: Start TARS-Setup hotspot
3. **Tailscale**: Connects independently when internet available

This means:
- Robot auto-connects to your WiFi on boot
- Only shows hotspot if WiFi unavailable
- No manual intervention needed for normal operation

### How It Works (NetworkManager Autoconnect)

**WiFi Networks - Autoconnect Enabled**

All WiFi networks you connect to have `autoconnect=yes` by default:
- HomeWiFi → autoconnect=yes
- PhoneHotspot → autoconnect=yes
- OfficeWiFi → autoconnect=yes

NetworkManager handles priority automatically - it scans for known networks and connects to the first one found. Multiple networks with autoconnect enabled won't conflict - NetworkManager just tries them in order.

**Hotspot - Autoconnect Disabled**

The TARS-Setup hotspot has `autoconnect=no`:
- Won't start randomly on boot
- Only starts when manually triggered
- Dashboard service starts it if no WiFi connection found

**Boot Sequence**

```
TARS boots
  ↓
NetworkManager starts
  ↓
Scans for known WiFi networks
  ├─ Found HomeWiFi → Connect → Tailscale → Done ✅
  ├─ Found PhoneHotspot → Connect → Tailscale → Done ✅
  └─ Found nothing
       ↓
     Dashboard service starts (server.py)
       ↓
     Checks WiFi status
       ↓
     No connection found
       ↓
     Start TARS-Setup hotspot
       ↓
     User connects to setup page
       ↓
     User configures WiFi
       ↓
     nmcli connects (autoconnect=yes)
       ↓
     Hotspot auto-deactivates → Tailscale → Done ✅
```

**Implementation**

The boot logic is handled in the dashboard service (`server.py`):
```python
# On dashboard startup
if not wifi_manager.is_connected():
    wifi_manager.start_hotspot()
```

No separate systemd service needed - the dashboard handles it.

## Troubleshooting

### Cannot Access tars.local

**Symptom**: `tars.local` not loading

**Causes**:
- On dorm/corporate WiFi (client isolation)
- mDNS blocked by network
- Not on same WiFi as TARS

**Solution**:
- Use Tailscale URL instead
- Check WiFi connection
- Verify both devices on same network

### Forgot Tailscale IP

**Solution 1**: Via mDNS (if on home WiFi)
```
http://tars.local:8080
```
Then go to Settings → Network section to see Tailscale IP

**Solution 2**: Via Tailscale Admin
1. Open https://login.tailscale.com/admin/machines
2. Find "tars" device
3. Note the 100.x.x.x IP address

**Solution 3**: Via SSH (if configured)
```bash
ssh tars-pi
tailscale ip -4
```

**Solution 4**: Start Hotspot
1. Power cycle TARS
2. Disable home WiFi on Pi (or move robot out of range)
3. Wait 30 seconds for TARS-Setup hotspot
4. Connect to hotspot
5. Setup again and save URLs

### WiFi Connection Fails

**Check:**
- Correct password entered
- Network within range
- 2.4GHz or 5GHz band supported by Pi WiFi
- Enterprise credentials correct (username/password)

**Enterprise WiFi**:
- Verify authentication method is PEAP/MSCHAPv2
- Some networks require device registration
- Contact IT if connection repeatedly fails

### Hotspot Not Starting

**Check**:
1. Pi is powered on and booted (wait 60 seconds)
2. NetworkManager service running: `systemctl status NetworkManager`
3. Check logs: `journalctl -u tars-dashboard -n 50`

**Manual start**:
```bash
ssh tars-pi
cd ~/tars-daemon
source venv/bin/activate
python -c "from dashboard.backend.wifi_manager import WiFiManager; WiFiManager().start_hotspot()"
```

### Dashboard Not Loading

**After WiFi change:**
- Wait 10-15 seconds for connection
- Reconnect your device to same WiFi
- Try Tailscale URL if tars.local doesn't work
- Check TARS has internet (Tailscale requires internet)

**Check service**:
```bash
ssh tars-pi
sudo systemctl status tars-dashboard
```

## Advanced Configuration

### Static IP Assignment

To assign static IP to TARS:

```bash
ssh tars-pi
sudo nmcli connection modify "YourWiFi" \
  ipv4.addresses 192.168.1.100/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns 8.8.8.8 \
  ipv4.method manual
sudo nmcli connection up "YourWiFi"
```

### Change Hotspot Settings

Edit hotspot configuration:

```bash
ssh tars-pi
sudo nmcli connection modify TARS-Setup \
  wifi.ssid "NewName" \
  wifi-sec.psk "newpassword123"
```

### Multiple WiFi Networks

TARS remembers all WiFi networks you've connected to. It will auto-connect to whichever is available on boot.

To manage saved networks:
```bash
# List all saved connections
nmcli connection show

# Delete old network
nmcli connection delete "OldNetwork"
```

### Autoconnect Management

**Check autoconnect status:**
```bash
# Show all connections with autoconnect status
nmcli -f NAME,AUTOCONNECT connection show
```

**Enable autoconnect for a network:**
```bash
sudo nmcli connection modify "NetworkName" connection.autoconnect yes
```

**Disable autoconnect for a network:**
```bash
sudo nmcli connection modify "NetworkName" connection.autoconnect no
```

**Best Practices:**
- WiFi networks: Keep `autoconnect=yes` (default) ✅
- TARS-Setup hotspot: Keep `autoconnect=no` (default) ✅
- Networks with autoconnect enabled won't conflict - NetworkManager tries them in priority order
- Only disable autoconnect for networks you want to connect to manually

**Verify hotspot configuration:**
```bash
# Should show: AUTOCONNECT: no
nmcli connection show TARS-Setup | grep autoconnect
```

## Security Notes

- WiFi passwords stored in NetworkManager (system keyring)
- API keys stored in `/etc/tars/config.json` (root-owned)
- Tailscale provides encrypted tunnel (end-to-end)
- Dashboard accessible only on local network or Tailscale VPN
- Setup hotspot password should be changed after initial setup

## See Also

- [Dashboard Guide](./DASHBOARD.md) - Full dashboard documentation
- [Installation Guide](./INSTALLATION.md) - Initial setup instructions
- [Tailscale Docs](https://tailscale.com/kb/1017/install/) - Tailscale installation guide
