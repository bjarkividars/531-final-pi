# joystick.py
import asyncio
import Adafruit_ADS1x15
import time
import statistics # Using median for more robust calibration

# --- Configuration ---
GAIN = 1
X_CHANNEL = 0
Y_CHANNEL = 1

CENTER_SAMPLES = 30

# *** ADJUST THIS VALUE BASED ON TESTING ***
# Observed center: X=~20600, Y=~20880
# Start with ~2500, decrease if unresponsive, increase if too sensitive near center.
THRESHOLD_DELTA = 2500

# Axis physical characteristics (relative to center) - Confirmed from logs
# These settings help determine the initial boolean flags correctly.
Y_AXIS_UP_VALUE = "lower" # Lower Y value means physical UP detected
X_AXIS_LEFT_VALUE = "lower" # Lower X value means physical LEFT detected

# Set to False for normal operation, True for debug prints on startup
DEBUG_CALIBRATION = False

# --- End Configuration ---


async def poll_joystick(ws,
                        x_channel: int = X_CHANNEL,
                        y_channel: int = Y_CHANNEL,
                        poll_interval: float = 0.05):
    """
    Read joystick axes, calibrate center, determine direction based on thresholds,
    REMAP direction labels according to user spec, and send on change.
    """
    try:
        adc = Adafruit_ADS1x15.ADS1115(busnum=1)
        print("ADS1115 ADC Initialized.")
    except Exception as e:
        print(f"Error initializing ADS1115: {e}")
        return

    # --- Center Calibration ---
    print(f"Calibrating center ({CENTER_SAMPLES} samples)... KEEP JOYSTICK CENTERED!")
    # [Calibration code remains the same as previous version]
    # ... (omitted for brevity, assuming it worked) ...
    x_readings = []
    y_readings = []
    try:
        await asyncio.sleep(0.5) # Allow settling time
        for i in range(CENTER_SAMPLES):
            x_readings.append(adc.read_adc(x_channel, gain=GAIN))
            y_readings.append(adc.read_adc(y_channel, gain=GAIN))
            # if DEBUG_CALIBRATION: print(f"  Calib read {i+1}: X={x_readings[-1]}, Y={y_readings[-1]}")
            await asyncio.sleep(0.02)
        x_readings.sort(); y_readings.sort()
        x_center = statistics.median(x_readings)
        y_center = statistics.median(y_readings)
        print(f"Calibration complete.")
        if DEBUG_CALIBRATION:
            print(f"  Median Center X: {x_center:.2f} (Range: {min(x_readings)}-{max(x_readings)})")
            print(f"  Median Center Y: {y_center:.2f} (Range: {min(y_readings)}-{max(y_readings)})")
    except Exception as e:
        print(f"Error during calibration: {e!r}")
        return

    # --- Calculate Absolute Thresholds ---
    # [Threshold calculation remains the same as previous version]
    # ... (omitted for brevity) ...
    left_threshold = x_center - THRESHOLD_DELTA
    right_threshold = x_center + THRESHOLD_DELTA
    if Y_AXIS_UP_VALUE == "lower":
        up_threshold = y_center - THRESHOLD_DELTA
        down_threshold = y_center + THRESHOLD_DELTA
    else:
        up_threshold = y_center + THRESHOLD_DELTA
        down_threshold = y_center - THRESHOLD_DELTA

    if DEBUG_CALIBRATION:
        print(f"--- Thresholds (Delta={THRESHOLD_DELTA}) ---")
        print(f"  X Neutral Zone: ~{left_threshold:.0f} <-> {right_threshold:.0f}")
        print(f"  Y Neutral Zone: ~{min(up_threshold, down_threshold):.0f} <-> {max(up_threshold, down_threshold):.0f}")
        print(f"-------------------------")
        await asyncio.sleep(1.0)

    # --- Main Polling Loop ---
    prev_direction = None
    print("Starting joystick polling...")
    # print("WARNING: Potential hardware issue detected near X=minimum (value jumps).") # Kept commented unless needed
    while True:
        try:
            value_x = adc.read_adc(x_channel, gain=GAIN)
            value_y = adc.read_adc(y_channel, gain=GAIN)
            # print(f'value x: {value_x} and value y: {value_y}') # Keep commented unless debugging raw values

            # --- Determine original direction flags based on thresholds ---
            # These flags indicate the *physical* deviation based on config
            physical_left = (value_x < left_threshold) if X_AXIS_LEFT_VALUE == "lower" else (value_x > right_threshold)
            physical_right = (value_x > right_threshold) if X_AXIS_LEFT_VALUE == "lower" else (value_x < left_threshold)
            physical_up = (value_y < up_threshold) if Y_AXIS_UP_VALUE == "lower" else (value_y > up_threshold)
            physical_down = (value_y > down_threshold) if Y_AXIS_UP_VALUE == "lower" else (value_y < down_threshold)

            # --- *** REMAP FLAGS TO DESIRED OUTPUT LABELS *** ---
            direction = "neutral"
            dir_parts = []

            # Original Physical -> Desired Output Label
            if physical_up:     # Low Y occurred
                dir_parts.append("left")  # User wants this labelled "left"
            if physical_down:   # High Y occurred
                dir_parts.append("right") # User wants this labelled "right"
            if physical_left:   # Low X occurred
                dir_parts.append("down")    # User wants this labelled "up"
            if physical_right:  # High X occurred
                dir_parts.append("up")  # User wants this labelled "down"

            # --- Combine remapped parts ---
            if dir_parts:
                 direction = "-".join(sorted(dir_parts)) # Sort for consistent diagonal names
                 # Conflict check (less likely now, but good practice)
                 if "up" in dir_parts and "down" in dir_parts: direction = "INVALID_REMAPPED_X"
                 if "left" in dir_parts and "right" in dir_parts: direction = "INVALID_REMAPPED_Y"

            # Send direction only if it changed
            if direction != prev_direction:
                 # Print raw values along with the *remapped* direction change
                 if ws:
                    await ws.send(direction)
                 # else: print("(ws is None, not sending)") # Keep commented unless testing ws object
                 prev_direction = direction

            await asyncio.sleep(poll_interval)

        except OSError as e:
             print(f"OSError reading ADC (check connection?): {e}")
             await asyncio.sleep(1)
        except Exception as e:
             print(f"Error in joystick poll loop: {e!r}")
             await asyncio.sleep(1)