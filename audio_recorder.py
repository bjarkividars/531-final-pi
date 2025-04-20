# audio_recorder.py
import asyncio
import sounddevice as sd

async def stream_audio(ws,
                       sample_rate: int = 16000,
                       block_size: int = 1024):
    """
    Continuously capture 16‑bit mono audio and send each block over ws.
    """
    with sd.InputStream(samplerate=sample_rate,
                        channels=1,
                        dtype='int16',
                        blocksize=block_size) as stream:
        while True:
            data, overflowed = stream.read(block_size)
            if overflowed:
                print("Warning: audio buffer overflow")
            # send raw PCM bytes
            await ws.send(data.tobytes())
