import asyncio
import aiohttp
from Jugador import Jugador
from Torneig import Torneig

HOST = '0.0.0.0'
PORT = 8444

dict_torurnaments = {}  # Dictionary to store Torneig objects

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")
    data = await reader.read(100)
    print(f"Received: {data.decode()} from {addr}")
    data = data.decode().strip()
    print(f"Data: {data}")
    try:
        tournament_id, player_id = data.split(".")
    except ValueError:
        writer.write(b"Invalid data format. Use 'tournament_id.player_id'.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Start periodic GET requests in the background for this client
    asyncio.create_task(periodic_get_request())

    # Ensure the tournament exists in the dictionary
    if tournament_id not in dict_torurnaments:
        writer.write(b"Invalid Tournament.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Add the player to the tournament
    torneig = dict_torurnaments[tournament_id]
    jugador = Jugador(player_id, tournament_id, writer)
    try:
        torneig.add_player(jugador)
        print(f"Updated tournament: {torneig}")
        writer.write(b"Registered for the tournament!\n")
    except ValueError as e:
        writer.write(str(e).encode() + b"\n")
    await writer.drain()

def create_tournament(tournament_id):
    """Create a new tournament and add it to the dictionary."""
    if tournament_id in dict_torurnaments:
        print(f"Tournament with ID {tournament_id} already exists.")
        return False  # Tournament already exists
    dict_torurnaments[tournament_id] = Torneig(tournament_id)
    print(f"Tournament with ID {tournament_id} created.")
    return True  # Tournament successfully created

async def periodic_get_request():
    url = "https://turnonauta.asegura.dev:8443/tournaments/active"  
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                print(f"GET {url} - Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        id_tournament = str(item.get('id_torneig'))  # Ensure ID is a string
                        jugadors = item.get('jugadors')
                        create_tournament(id_tournament)  # Create tournament if it doesn't exist
                        print(f"id: {id_tournament}, jugadors: {jugadors}")
                else:
                    print(f"Failed to fetch data. Status: {response.status}")
        except Exception as e:
            print(f"Error during GET request: {e}")

async def send_message_to_tournament(tournament_id, message):
    if tournament_id in dict_torurnaments:
        for jugador in dict_torurnaments[tournament_id].players:
            await jugador.send_message(message)
                
async def main():

      # Start periodic GET requests
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())