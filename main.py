# main.py
import asyncio
import digitalio
import board
import websockets

from joystick import poll_joystick
from audio_recorder import stream_audio

# ==== CONFIGURE THESE ====
WS_URL   = "ws://172.28.187.194:8000/ws/unified"
BUTTON_PIN = board.D17          # GPIO pin wired to joystick button (active‑low)
POLL_RATE  = 0.05               # joystick poll interval (secs)
# ==========================

async def monitor_button(ws):
    """
    Watch the button pin: on press start audio streaming;
    on release, stop it.
    """
    button = digitalio.DigitalInOut(BUTTON_PIN)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP

    audio_task = None
    while True:
        if not button.value:  # button pressed
            if audio_task is None:
                audio_task = asyncio.create_task(stream_audio(ws))
        else:
            if audio_task:
                audio_task.cancel()
                print('sending end')
                await ws.send("END")
                print('SENT END')
                try:
                    await audio_task
                except asyncio.CancelledError:
                    pass
                audio_task = None
        await asyncio.sleep(POLL_RATE)

async def handle_connection():
    """
    Establish WS, then spawn joystick + button tasks.
    """
    async with websockets.connect(WS_URL) as ws:
        await asyncio.gather(
            poll_joystick(ws, poll_interval=POLL_RATE, x_channel=1,
                        y_channel = 2),
            monitor_button(ws),
        )

async def main():
    """
    Keep retrying the connection on failure.
    """
    while True:
        try:
            await handle_connection()
        except Exception as e:
            print(f"Connection error: {e!r}, retrying in 5s…")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())