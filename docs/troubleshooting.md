# Troubleshooting

[← Documentation](README.md) · [Deutsch](de/fehlerbehebung.md)

## Quick checks

1. **Is the Board Manager running?** Open `http://<board-ip>:3180` in a browser on a device in the same network. Board Manager 1 shows its app; Board Manager 2 answers on `http://<board-ip>:3180/api/state`.
2. **Is the entity *Board Manager connection* on?** If not, Home Assistant cannot reach the board. Check the address, the port and the network between them (VLANs, firewall, Docker networking).
3. **Is the entity *Realtime connection* on?** If not, updates still arrive every 2 seconds, but not instantly. See [realtime connection](#no-realtime-updates).

## Setup

| Message | Cause and solution |
| --- | --- |
| *Cannot reach the local Board Manager or its response is invalid* | Wrong address or port, the Board Manager is not running, or something else answers on that port. Enter the IP address only, without `http://` and without a port. |
| *No board ID is configured in Board Manager* | The board has not been set up with Autodarts yet. Finish the setup in the Board Manager, then try again. |
| *No new boards were found automatically* | The search only finds boards that registered from your internet connection and that are not set up yet. Enter the address instead. |
| *The board search is unavailable right now* | The Autodarts discovery service is unreachable. Enter the address instead. |
| *This Autodarts board is already configured* | The board is already set up. Use **Reconfigure** to change its address. |
| The board is not discovered automatically | Automatic discovery needs Board Manager 2 and mDNS in your network. Home Assistant in Docker needs `network_mode: host`, and mDNS does not cross VLANs without a repeater. Use the search or the address instead. |
| *This client ID is invalid or is not enabled for device login* | The cloud link needs a client ID issued by Autodarts for this integration. None is available yet; see [cloud link](installation.md#link-the-autodarts-cloud-optional). Local setup works without it. |

## Repairs

Home Assistant shows these notices under **Settings → Repairs**:

| Notice | Meaning and solution |
| --- | --- |
| **Autodarts board address points to a different board** | The configured address answers with a different board ID, for example because IP addresses were swapped. The entities stay unavailable so that they never show another board's data. Open the integration, choose **Reconfigure** and select the correct board. The notice disappears by itself. |
| **Update the board to the new Autodarts Board Manager** | The board still runs the classic Board Manager 1, which Autodarts will switch off. Install Board Manager 2 on the board PC. The integration switches over by itself and the notice disappears. |

## Operation

### Entities are unavailable

- **All local entities unavailable:** the Board Manager does not answer. The entities recover by themselves within seconds after the board is back. The training entities stay available.
- **Settings and camera entities unavailable, the rest works:** the board has not reported its configuration yet. This resolves with the next read, at the latest after 30 seconds.
- **Unavailable after a Board Manager update:** the integration reloads itself when the generation changes. Wait a few seconds.

### No realtime updates

*Realtime connection* is off, and changes appear with a delay of about 2 seconds:

- A proxy or firewall between Home Assistant and the board may block WebSocket connections to port 3180.
- After a restart of the Board Manager, the integration reconnects within 60 seconds at most.

### Darts are counted wrongly in the training session

- Darts on the board while Home Assistant starts are deliberately ignored.
- If a takeout is not detected and new darts follow, the previous visit is closed and the new darts are counted.
- The training session counts what the board detects. If the board detects a wrong segment and you correct it in Autodarts, the session follows the correction only if the board reports it.

To start over, press **Reset training statistics** or *New session* on the training card.

### A camera is reported as a problem

*Camera problem* turns on when a camera delivers no frames for 15 seconds during active detection. Check the camera's cable and USB port, and whether the camera appears in the Board Manager. Calibrating once more often helps as well.

### The card is missing or outdated

- **Custom element doesn't exist: autodarts-card:** restart Home Assistant after installing, then reload the browser page.
- **An old version of a card after an update:** reload the page. In the companion app, use *Settings → Companion app → Debugging → Reset frontend cache*.
- **The training history is empty:** the history is read from the recorder. It needs the `recorder` integration (enabled by default) and fills with completed visits.

## Diagnostics and logs

### Download diagnostics

**Settings → Devices & services → Autodarts →** the board's menu (⋮) → **Download diagnostics**. The file contains the board state, the settings summary, the Board Manager generation, connection states and the poll interval. The board ID, addresses and tokens are redacted.

### Enable debug logging

On the integration page, select **Enable debug logging**, reproduce the problem and then select **Disable debug logging**. Home Assistant downloads the log. Alternatively, in `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.autodarts: debug
```

### Report a bug

Open an [issue](https://github.com/Dennis-Otto/ha-autodarts/issues/new/choose) with the Home Assistant version, the Board Manager version, the diagnostics file and the relevant log lines. Report security problems privately as described in [SECURITY.md](../SECURITY.md).
