# audio_recorder.py
import asyncio
import websockets # Keep for type hinting ws
import pyaudio    # Use PyAudio

# --- User Configuration ---
# Find this using a script like 'list_audio_devices.py'
# Example: Find your USB mic's index and set it here.
INPUT_DEVICE_INDEX = 1 # *** Replace with your USB Mic's correct index ***
# ****************************

# --- Audio Configuration ---
# !! IMPORTANT: Match server's expected sample rate (e.g., 16000 for many ASR models) !!
RATE = 44100             # Sample rate (Hz)
CHUNK = 4096             # Samples per frame (affects latency)
FORMAT = pyaudio.paInt16 # Audio format (16-bit signed integers)
CHANNELS = 1             # Number of channels (Mono)


async def stream_audio(ws):
    """
    Continuously capture audio from INPUT_DEVICE_INDEX, send binary chunks over ws.
    Handles cancellation gracefully by cleaning up PyAudio resources.
    """
    if not isinstance(INPUT_DEVICE_INDEX, int) or INPUT_DEVICE_INDEX < 0:
        print(f"ERROR: INPUT_DEVICE_INDEX ({INPUT_DEVICE_INDEX}) is not set correctly. Please configure it.")
        print("Run a script to list devices and find the correct index.")
        return

    audio = None
    stream = None
    try:
        # --- Initialize PyAudio ---
        audio = pyaudio.PyAudio()

        # --- Verify Selected Device ---
        try:
            device_info = audio.get_device_info_by_index(INPUT_DEVICE_INDEX)
            print(f"[Audio] Selected device: {INPUT_DEVICE_INDEX} - {device_info.get('name')}")
            if device_info.get('maxInputChannels', 0) < CHANNELS:
                print(f"[Audio] ERROR: Device {INPUT_DEVICE_INDEX} supports only {device_info.get('maxInputChannels')} input channels, need {CHANNELS}.")
                return # Cleanup handled in finally
        except IOError:
            print(f"[Audio] ERROR: Could not find audio device with index {INPUT_DEVICE_INDEX}.")
            return # Cleanup handled in finally
        except Exception as e:
             print(f"[Audio] ERROR getting device info for index {INPUT_DEVICE_INDEX}: {e}")
             return # Cleanup handled in finally

        # --- Open audio stream ---
        print(f"[Audio] Opening stream: Rate={RATE}, Channels={CHANNELS}, Chunk={CHUNK}, Device={INPUT_DEVICE_INDEX}")
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=INPUT_DEVICE_INDEX
        )
        print("[Audio] Stream opened. Starting recording...")
        stream.start_stream() # Explicitly start the stream

        # --- Main Streaming Loop ---
        # The 'ws' object is already connected when passed to this function
        print(f"[Audio] Streaming to WebSocket: {ws.remote_address}...")
        while True:
             try:
                 # Check if stream is active before reading
                 if not stream.is_active():
                      print("[Audio] WARN: Stream became inactive.")
                      await asyncio.sleep(0.1) # Avoid busy-loop if stream stops
                      continue # Or break, depending on desired behavior

                 # Read audio chunk from microphone
                 audio_data = stream.read(CHUNK, exception_on_overflow=False)

                 # Send audio chunk (binary data) to WebSocket
                 await ws.send(audio_data)
                 await asyncio.sleep(0)

                 # Optional: short sleep to yield control, can help prevent 100% CPU
                 # await asyncio.sleep(0.001)

             except IOError as e:
                 # This might happen if the device is disconnected
                 print(f"[Audio] IOError during stream read: {e}")
                 await asyncio.sleep(0.5) # Pause before potentially retrying/exiting
                 break # Exit loop on read error
             except websockets.exceptions.ConnectionClosed:
                  print("[Audio] WebSocket connection closed by peer.")
                  break # Exit loop if connection is closed
             except Exception as e:
                 print(f"[Audio] Error during streaming loop: {e!r}")
                 await asyncio.sleep(0.1)
                 # Consider whether to break or continue here

    except asyncio.CancelledError:
        print("[Audio] Streaming task cancelled.")
        # This is expected when the button is released. Cleanup is in finally.
        # Re-raise so the calling task in main.py knows it was cancelled cleanly.
        raise

    except Exception as e:
        # Catch unexpected errors during setup
        print(f"[Audio] An unexpected error occurred in stream_audio setup: {e!r}")

    finally:
        # --- CRITICAL: Cleanup Resources ---
        print("[Audio] Cleaning up audio resources...")
        if stream is not None:
            try:
                if stream.is_active():
                     stream.stop_stream()
                     print("[Audio] Stream stopped.")
                stream.close()
                print("[Audio] Stream closed.")
            except Exception as e:
                print(f"[Audio] Error stopping/closing stream: {e}")
        if audio is not None:
            try:
                audio.terminate()
                print("[Audio] PyAudio terminated.")
            except Exception as e:
                print(f"[Audio] Error terminating PyAudio: {e}")
        print("[Audio] Cleanup finished.")