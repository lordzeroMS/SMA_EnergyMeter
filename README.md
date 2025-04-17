# SMA Energy Meter Integration for Home Assistant

This integration allows you to monitor SMA Energy Meters directly in Home Assistant. It listens for multicast messages from SMA Energy Meters on your network and creates sensors for real-time power consumption, voltage, current, and other metrics.

## Features

- Real-time monitoring of SMA Energy Meters via multicast
- Automatic detection of SMA Energy Meters on your network
- Support for both SMA Energy Meters and SMA Home Managers
- Includes detailed metrics for total and per-phase measurements
- Easy setup through Home Assistant UI

## Installation

### HACS Installation (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Click on HACS in the sidebar
3. Go to "Integrations"
4. Click the three dots in the top-right corner and select "Custom repositories"
5. Add `https://github.com/lordzeroms/sma_energy_meter` as a custom repository with category "Integration"
6. Click "Add"
7. Search for "SMA Energy Meter" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/lordzeroms/sma_energy_meter)
2. Create a `custom_components` directory in your Home Assistant configuration directory if it doesn't already exist
3. Extract the `sma_energy_meter` directory into the `custom_components` directory
4. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services in Home Assistant
2. Click the "+ Add Integration" button
3. Search for "SMA Energy Meter" and select it
4. Enter the local IP address to bind to (default: 0.0.0.0)
5. Click "Submit"

The integration will automatically discover SMA Energy Meters on your network.

## Available Sensors

The integration creates the following sensors for each detected meter:

### Total Values
- Power consumption (W)
- Power supply/production (W)
- Reactive power consumption (VAr)
- Reactive power supply (VAr)
- Apparent power consumption (VA)
- Apparent power supply (VA)
- Power factor (cos φ)
- Frequency (Hz)

### Per Phase Values (for each phase)
- Power consumption (W)
- Power supply (W)
- Reactive power consumption (VAr)
- Reactive power supply (VAr)
- Apparent power consumption (VA)
- Apparent power supply (VA)
- Current (A)
- Voltage (V)
- Power factor (cos φ)

### Counter Values
Energy counters are available for all power measurements (kWh, kVArh, kVAh).

## Troubleshooting

### No devices detected
- Ensure your SMA Energy Meter is properly connected to your network
- Check that multicast traffic is allowed on your network
- Try setting a specific IP address instead of 0.0.0.0
- Check your network configuration for IGMP snooping settings

### Log files
Enable debug logging for more detailed information:

```yaml
logger:
  default: info
  logs:
    custom_components.sma_energy_meter: debug
```

## Credits

This integration is based on the SMA Energy Meter protocol documentation and inspired by other SMA integration projects. Special thanks to:

- david-m-m and datenschuft for the Speedwire decoder
- Wenger Florian for the SMA-EM packet capture script

## License

This project is licensed under the GNU General Public License v2.0.