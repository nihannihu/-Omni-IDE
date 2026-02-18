import asyncio
import websockets
import json
import base64
import time
import random

SERVER_URL = "ws://localhost:8000/ws/omni"
DURATION_SECONDS = 30

async def listen_for_messages(websocket):
    """Receive and log messages from the server."""
    try:
        while True:
            start_time = time.time()
            message = await websocket.recv()
            latency = (time.time() - start_time) * 1000  # ms (rough estimate of network + processing if ping-pong)
            
            # Basic parsing
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                content = data.get("text", "")[:50] # Truncate for log
                print(f"[{time.strftime('%H:%M:%S')}] 📥 RECV: {msg_type} | Content: {content}... | Latency: ~{latency:.1f}ms")
            except:
                print(f"[{time.strftime('%H:%M:%S')}] 📥 RECV: Raw message (len={len(message)})")
                
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed by server.")

async def send_valid_audio(websocket):
    """Task A: Send valid 100kb audio chunks."""
    print("Started Task A: Valid Audio Stream (100kb/0.5s)")
    chunk_size = 100 * 1024 # 100kb
    dummy_audio = bytes([random.getrandbits(8) for _ in range(chunk_size)])
    
    while True:
        await websocket.send(dummy_audio)
        print(f"[{time.strftime('%H:%M:%S')}] 📤 SENT: Valid Audio Chunk (100kb)")
        await asyncio.sleep(0.5)

async def send_video_heartbeat(websocket):
    """Task B: Send dummy video frames."""
    print("Started Task B: Video Stream (Frame/1.0s)")
    # Tiny 1x1 base64 png
    dummy_frame = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    
    while True:
        payload = json.dumps({
            "type": "screen_frame",
            "image": dummy_frame
        })
        await websocket.send(payload)
        print(f"[{time.strftime('%H:%M:%S')}] 📤 SENT: Video Frame")
        await asyncio.sleep(1.0)
        
async def send_massive_payload(websocket):
    """Task C: Send invalid 5MB audio chunk to trigger rejection."""
    print("Started Task C: Massive Payload Attack (5MB/10s)")
    chunk_size = 5 * 1024 * 1024 # 5MB
    # Create just once to save CPU
    dummy_audio = bytes([0] * chunk_size) 
    
    while True:
        await asyncio.sleep(5) # Wait a bit before attacking
        print(f"[{time.strftime('%H:%M:%S')}] 💣 ATTACK: Sending 5MB Payload...")
        await websocket.send(dummy_audio)
        print(f"[{time.strftime('%H:%M:%S')}] 📤 SENT: 5MB Payload")
        await asyncio.sleep(10)

async def main():
    print(f"Connecting to {SERVER_URL}...")
    async with websockets.connect(SERVER_URL) as websocket:
        print("Connected! Starting Chaos...")
        
        # Run sender tasks in background
        sender_tasks = [
            asyncio.create_task(send_valid_audio(websocket)),
            asyncio.create_task(send_video_heartbeat(websocket)),
            asyncio.create_task(send_massive_payload(websocket)),
            asyncio.create_task(listen_for_messages(websocket))
        ]
        
        # Run for duration
        await asyncio.sleep(DURATION_SECONDS)
        
        print("\nTest Duration Complete. Stopping tasks...")
        for task in sender_tasks:
            task.cancel()
        
        print("Closing connection...")
        await websocket.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user.")
