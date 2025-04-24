import asyncio
import aiohttp
from models.Torneig import Torneig
from models.Jugador import Jugador
# Server configuration
HOST = '0.0.0.0'
PORT = 8445
dict_tournaments = {}
players = []


def create_tournament(tournament_id, max_players):
    """
    Creates a new tournament and adds it to the global dictionary.
    """
    if tournament_id in dict_tournaments:
        print(f"Tournament {tournament_id} already exists.")
        return False  # Tournament already exists

    # Add the new tournament to the dictionary
    dict_tournaments[tournament_id] = Torneig(tournament_id, max_players)

    
    #print(f"Tournament {tournament_id} created with max players: {max_players}")
    return True

async def handle_client(reader, writer):
    """
    Handles incoming client connections.
    """
    await periodic_get_request()
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    try:
        while True:
            data = await reader.read(100)
            if not data:
                print(f"Client {addr} disconnected.")
                break

            message = data.decode().strip()
            print(f"Received: {message} from {addr}")
            try:
                if(message.split(".")[0] == "0"): 
                    codi, id_torneig, id_jugador, nom = message.split(".")
                    player = Jugador(id_jugador, id_torneig, nom, writer)
                    dict_tournaments[id_torneig].add_player(player)
                    players.append(player)
                    for tournament in dict_tournaments.values():
                        print(f"Tournament ID: {tournament.id_torneig}, Max Players: {tournament.max_players}")
                        for p in tournament.players:
                            print(f"Player ID: {p.id_jugador}, Name: {p.nom}")
            except ValueError:
                writer.write(b"Invalid message format. Use 'id_jugador.id_torneig.nom'\n")
                await writer.drain()
                continue
            writer.write(f"Echo: {message}\n".encode())
            await writer.drain()
    except asyncio.CancelledError:
        print(f"Connection with {addr} was cancelled.")
    finally:
        print(f"Closing connection with {addr}")
        writer.close()
        await writer.wait_closed()


async def notify_players():
    """
    Periodically sends a message to all players with the list of players in their tournament.
    """
    while True:
        for tournament_id, tournament in dict_tournaments.items():
            # Get the list of player names in the tournament
            #print(f"Notifying players in tournament {tournament_id}")
            player_names = [p.nom for p in tournament.players]
            print (player_names)
            notification = f"1.{'.'.join(player_names)}\n"
            print(f"Notification: {notification}")
            disconnected_players = []
            for player in tournament.players:
                try:
                    # Send the updated player list to the player
                    player.writer.write(notification.encode())
                    await player.writer.drain()
                except (BrokenPipeError, ConnectionResetError):
                    # Handle disconnected players
                    print(f"Connection lost with player {player.id_jugador}. Removing from tournament.")
                    disconnected_players.append(player)

            # Remove disconnected players from the tournament
            for player in disconnected_players:
                tournament.players.remove(player)
                players.remove(player)  # Remove from the global players list

        # Wait for 2 seconds before the next check
        await asyncio.sleep(2)

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
                        create_tournament(tournament_id, num_players)
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
    asyncio.create_task(notify_players())
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())