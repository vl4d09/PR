import asyncio
import websockets
from aiohttp import web
import threading

connected_clients = {}

async def chat_handler(websocket, path):
    
    username = await websocket.recv()  
    connected_clients[websocket] = username  
    print(f"{username} joined the chat. Total clients: {len(connected_clients)}")
    
    try:
        async for message in websocket:
            
            for client, client_username in connected_clients.items():
                if client != websocket:
                    await client.send(f"{username}: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"{username} disconnected")
    finally:
        del connected_clients[websocket]  
        print(f"{username} left. Total clients: {len(connected_clients)}")


async def http_handler(request):
    return web.Response(text="HTTP Server is up and running")


async def init_http_server():
    app = web.Application()
    app.add_routes([web.get('/', http_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print("HTTP server running on http://localhost:8080")
    

def run_http_server():
    asyncio.run(init_http_server())


async def run_websocket_server():
    server = await websockets.serve(chat_handler, 'localhost', 8765)
    print("WebSocket server running on ws://localhost:8765")
    await server.wait_closed()


def main():
    
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()
    
    
    asyncio.run(run_websocket_server())

if __name__ == "__main__":
    main()
