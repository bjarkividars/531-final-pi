# joystick.py
import asyncio
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

# Midpoint & deadzone threshold for a 16‑bit ADC
MID = 32767
THRESHOLD = 10000

def determine_direction(x_val: int, y_val: int,
                        mid: int = MID, threshold: int = THRESHOLD) -> str:
    """
    Map raw X/Y readings to one of:
      - "neutral" (centered)
      - "up" / "down"   (dominant X axis)
      - "forward" / "backward" (dominant Y axis)
    """
    dx = x_val - mid
    dy = y_val - mid
    if abs(dx) < threshold and abs(dy) < threshold:
        return "neutral"
    # pick the axis with the larger deflection
    if abs(dx) > abs(dy):
        return "up" if dx > 0 else "down"
    else:
        return "forward" if dy > 0 else "backward"

async def poll_joystick(ws,
                        x_channel: int = 0,
                        y_channel: int = 1,
                        poll_interval: float = 0.05):
    """
    Read the joystick axes and send a string on any change.
    """
    # init I2C & ADC
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS1115(i2c)
    ch_x = AnalogIn(ads, getattr(ads, f"channel_{x_channel}"))
    ch_y = AnalogIn(ads, getattr(ads, f"channel_{y_channel}"))

    prev_dir = None
    while True:
        direction = determine_direction(ch_x.value, ch_y.value)
        if direction != prev_dir:
            await ws.send(direction)
            prev_dir = direction
        await asyncio.sleep(poll_interval)
