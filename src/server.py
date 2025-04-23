import asyncio
import aiohttp
# Server configuration
HOST = '0.0.0.0'
PORT = 8444

async def handle_client(reader, writer):
    """
    Handles incoming client connections.
    """
    await periodic_get_request()
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    try:
        while True:
            # Read the client's message
            data = await reader.read(100)
            if not data:
                print(f"Client {addr} disconnected.")
                break

            message = data.decode().strip()
            print(f"Received: {message} from {addr}")

            # Echo the message back to the client
            writer.write(f"Echo: {message}\n".encode())
            await writer.drain()
    except asyncio.CancelledError:
        print(f"Connection with {addr} was cancelled.")
    finally:
        print(f"Closing connection with {addr}")
        writer.close()
        await writer.wait_closed()


async def periodic_get_request():
    """
    Periodically fetches active tournaments from the server.
    """
    url = "https://turnonauta.asegura.dev:8443/tournaments/active"
    async with aiohttp.ClientSession() as session:
        print("Fetching active tournaments...")
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        tournament_id = str(item.get('id_torneig'))
                        num_players = item.get('num_jugadors')
                        #create_tournament(tournament_id, num_players)
                        print(f"id: {tournament_id}, max players: {num_players}")
                else:
                    print(f"Failed to fetch data. Status: {response.status}")
        except Exception as e:
            print(f"Error during GET request: {e}")
async def main():
    """
    Main entry point for the server.
    """
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")
    
    await periodic_get_request()
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())