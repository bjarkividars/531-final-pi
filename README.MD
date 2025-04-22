# PodiumPro Client for Raspberry Pi

A client application that runs on Raspberry Pi to control presentations via the PodiumPro server. This client uses a joystick for navigation and an audio recording capability for recording questions from the audience.

## Features

- **Joystick Control**: Navigate through presentations using a joystick (up, down, left, right)
- **Voice Control**: Hold a button to record and transmit audio to the server for question processing
- **WebSocket Communication**: Real-time communication with the PodiumPro server

## Hardware Requirements

- Raspberry Pi (tested on Raspberry Pi 4B)
- ADS1115 Analog-to-Digital Converter
- Analog joystick with push button functionality
- USB microphone
- Power supply

## Wiring Setup

- Joystick X-axis: Connected to ADS1115 A0
- Joystick Y-axis: Connected to ADS1115 A1
- Joystick SW: Connected to GPIO 17 (active-low with pull-up)
- ADS1115: Connected to Raspberry Pi via I2C (SDA/SCL)
- USB Microphone: Connected to any USB port

## Software Prerequisites

```
pip install websockets pyaudio Adafruit_ADS1x15
```

## Configuration

Before running the client, configure the following settings in `main.py`:

```python
# ==== CONFIGURE THESE ====
WS_URL     = "ws://your.server.ip:8000/ws/unified"  # Change to your server address
BUTTON_PIN = board.D17                              # GPIO pin wired to joystick button
POLL_RATE  = 0.05                                   # joystick poll interval (secs)
# ==========================
```

Additionally, in `audio_recorder.py`, set the correct audio device index:

```python
INPUT_DEVICE_INDEX = 1  # Replace with your USB Mic's correct index
```

## Running the Client

```
python main.py
```

When started, the client will:

1. Calibrate the joystick center position (keep the joystick centered during startup)
2. Connect to the PodiumPro server via WebSocket
3. Begin monitoring joystick movements and button presses

## How to Use

- **Navigation**: Move the joystick in any direction to navigate through slides/UI
- **Voice Commands**: Press and hold the button to record questions, release when done
- **Reconnection**: The client will automatically attempt to reconnect if the connection is lost

## Troubleshooting

- If joystick sensitivity seems off, adjust the `THRESHOLD_DELTA` value in `joystick.py`
- For microphone issues, verify the correct `INPUT_DEVICE_INDEX` in `audio_recorder.py`
- Check terminal output for connection errors and other diagnostic messages

## Development

The codebase consists of three main Python files:

- `main.py`: Entry point and connection management
- `joystick.py`: Joystick polling and directional detection
- `audio_recorder.py`: Audio capture and streaming
