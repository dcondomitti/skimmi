# Maytronics Skimmi

[![hacs][hacsbadge]][hacs]

Home Assistant integration for the Maytronics Skimmi and SkimLux robot pool cleaners via Bluetooth Low Energy (BLE).

## Features

- Automatic Bluetooth discovery of Skimmi and SkimLux devices
- Battery level sensor
- Water temperature sensor
- Power consumption sensor
- Device state (idle, cleaning, paused, error)
- Motor hours (diagnostic)
- Cycle time (diagnostic)

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top right corner and select "Custom repositories"
3. Add this repository URL and select "Integration" as the category
4. Click "Download"
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/skimmi` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

The integration is configured via the Home Assistant UI. Your Skimmi device should be automatically discovered via Bluetooth. If not, you can manually add it through the integrations page.

If your device has a password set, you will be prompted to enter it during setup.

## Requirements

- Home Assistant 2025.1.0 or newer
- Bluetooth adapter accessible to Home Assistant
- Maytronics Skimmi or SkimLux device within Bluetooth range

[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg
