# Elica Getup - Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/YOUR_USERNAME/elica_getup.svg)](https://github.com/YOUR_USERNAME/elica_getup/releases)
[![License](https://img.shields.io/github/license/YOUR_USERNAME/elica_getup.svg)](LICENSE)

**DISCLAIMER**: This is an **unofficial** integration for Elica Getup hoods. It is not affiliated with, endorsed by, or supported by Elica. Use at your own risk. By using this integration, you acknowledge and accept all risks associated with it, including potential issues with your device or Elica account. The author assumes no responsibility for any damages or issues that may arise from using this integration.

## Overview

Custom Home Assistant integration for controlling Elica Getup kitchen hoods via the Elica cloud API. This integration creates a single device with multiple entities for complete hood control.

## Features

This integration creates a single device **"[Your Name] Elica Getup"** with the following entities:

### Main Entities
- **Fan** (`fan`): Hood fan control with 5 preset modes
  - Speed 1, 2, 3
  - Boost 1, Boost 2
- **Light** (`light`): Light control with brightness adjustment
- **Cover** (`cover`): Hood open/close control

### Sensors
- **Grease Filter** (`sensor`): Grease filter efficiency percentage
- **Charcoal Filter** (`sensor`): Charcoal filter efficiency percentage

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add repository URL: `https://github.com/YOUR_USERNAME/elica_getup`
5. Select category "Integration"
6. Search for "Elica Getup" and click "Download"
7. Restart Home Assistant

### Manual Installation

1. Copy the `elica_getup` folder to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Elica Getup"
4. Enter your credentials:
   - **Username**: Your Elica Connect app email address
   - **Password**: Your Elica Connect app password
   - **App Identifier**: A unique identifier for your device (e.g., `af3c7b5d2f17b6da`). You can customize this as you like - it's just an identifier used when communicating with Elica servers.
   - **Device Name**: Custom name for your device (default: "Kappa")

### Getting Your Credentials

- **Username & Password**: Use the same credentials as your Elica Connect mobile app
- **App Identifier**: Any unique string you want (e.g., `af3c7b5d2f17b6da`, `my-elica-hood`, etc.). Customize it as you prefer.

## Usage

After configuration, you'll find a new device "[Your Name] Elica Getup" with all entities grouped together.

### Automation Examples

```yaml
# Turn on fan when cooking
automation:
  - alias: "Auto Hood Fan"
    trigger:
      - platform: state
        entity_id: binary_sensor.stove
        to: "on"
    action:
      - service: fan.turn_on
        target:
          entity_id: fan.ventola_kappa
        data:
          preset_mode: "2"

# Turn on light at sunset
automation:
  - alias: "Hood Light at Sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.luce_kappa
        data:
          brightness: 128
```

## Technical Notes

- The integration polls the Elica cloud API every 60 seconds
- Hood movement (open/close) takes approximately 28 seconds to complete
- Before turning on the fan or light, the hood automatically opens if closed
- All communication is done via Elica's cloud API

## Troubleshooting

### Authentication Failed
- Verify your Elica Connect app credentials are correct
- The App Identifier can be any string - try something simple like `af3c7b5d2f17b6da`

### Entities Not Updating
- Check your internet connection
- Verify the Elica cloud service is operational
- Check Home Assistant logs for errors

## Support

For issues, questions, or feature requests, please open an issue on [GitHub](https://github.com/YOUR_USERNAME/elica_getup/issues).

## Disclaimer

This integration is provided "as is" without warranty of any kind. The author is not responsible for any damage to your device, loss of data, or any other issues that may arise from using this integration. Use at your own risk.

This is an independent project and is not affiliated with, endorsed by, or supported by Elica S.p.A.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Developed for personal use and shared with the Home Assistant community.
