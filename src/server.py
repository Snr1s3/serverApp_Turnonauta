import asyncio
import aiohttp
from models.Jugador import Jugador
from models.Torneig import Torneig

# Server configuration
HOST = '0.0.0.0'
PORT = 8444

# Dictionary to store tournaments
dict_tournaments = {}

# List to store all players
players = []


async def handle_client(reader, writer):
    """
    Handles incoming client connections.
    """
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

            # Parse the message
            try:
                codi, tournament_id, player_id, player_name = parse_client_message(message)

                # Register the player
                await register_player(tournament_id, player_id, player_name, writer)
            except ValueError as e:
                writer.write(f"{str(e)}\n".encode())
                await writer.drain()
    except asyncio.CancelledError:
        print(f"Connection with {addr} was cancelled.")
    finally:
        print(f"Closing connection with {addr}")
        writer.close()
        await writer.wait_closed()


def parse_client_message(message):
    """
    Parses the client's message.
    """
    try:
        codi, tournament_id, player_id, player_name = message.split(".")
        return codi, tournament_id, player_id, player_name
    except ValueError:
        raise ValueError("Invalid data format. Use 'codi.tournament_id.player_id.player_name'.")


async def register_player(tournament_id, player_id, player_name, writer):
    """
    Registers a player to a tournament and notifies all players in the tournament.
    """
    if tournament_id not in dict_tournaments:
        writer.write(b"Invalid Tournament.\n")
        await writer.drain()
        return

    if is_player_registered(player_id):
        writer.write(b"Player ID already registered in another tournament.\n")
        await writer.drain()
        return

    tournament = dict_tournaments[tournament_id]
    player = Jugador(player_id, tournament_id, writer)
    try:
        tournament.add_player(player)
        writer.write(b"Registered for the tournament!\n")
        await writer.drain()

        # Notify all players in the tournament
        notification = f"Player {player_name} has joined the tournament {tournament_id}.\n"
        disconnected_players = []
        for p in tournament.players:
            if p.writer != writer:  # Avoid notifying the player who just joined
                try:
                    p.writer.write(notification.encode())
                    await p.writer.drain()
                except (BrokenPipeError, ConnectionResetError):
                    print(f"Connection lost with player {p.id_jugador}. Removing from tournament.")
                    disconnected_players.append(p)

        # Remove disconnected players
        for p in disconnected_players:
            tournament.players.remove(p)

        print_tournaments()
    except ValueError as e:
        writer.write(f"{str(e)}\n".encode())
        await writer.drain()



def is_player_registered(player_id):
    """
    Checks if the player is already registered in any tournament.
    """
    for tournament in dict_tournaments.values():
        for player in tournament.players:
            if player.id_jugador == player_id:
                return True
    return False


def create_tournament(tournament_id, num_players):
    """
    Creates a new tournament.
    """
    if tournament_id in dict_tournaments:
        return False
    dict_tournaments[tournament_id] = Torneig(tournament_id, num_players)
    return True


async def periodic_get_request():
    """
    Periodically fetches active tournaments from the server.
    """
    url = "https://turnonauta.asegura.dev:8443/tournaments/active"
    while True:
        async with aiohttp.ClientSession() as session:
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
        
        # Wait for 30 seconds before the next request
        await asyncio.sleep(30)


def print_tournaments():
    """
    Prints the current state of all tournaments.
    """
    print("\nCurrent Tournaments:")
    for tournament in dict_tournaments.values():
        print(f"Tournament: {tournament.id_torneig}")
        for player_id in tournament.players:
            print(f"  Player ID: {player_id}")

async def check_connections_and_notify():
    """
    Periodically checks the connection with all players and removes disconnected players.
    """
    while True:
        for tournament_id, tournament in dict_tournaments.items():
            # Get the list of player names in the tournament
            player_names = [p.nom for p in players if p.id_jugador in tournament.players]
            notification = (
                f"1.{'.'.join(player_names)}\n"
            )

            disconnected_players = []
            for p_id in tournament.players:
                p = next((pl for pl in players if pl.id_jugador == p_id), None)
                if p:
                    try:
                        # Send the updated player list to the player
                        p.writer.write(notification.encode())
                        await p.writer.drain()
                    except ConnectionResetError:
                        # Handle disconnected players
                        print(f"Connection lost with player {p.id_jugador}. Removing from tournament.")
                        disconnected_players.append(p_id)

            # Remove disconnected players from the tournament
            for p in disconnected_players:
                tournament.players.remove(p.id_jugador)
                players.remove(p)

        # Wait for 2 seconds before the next check
        await asyncio.sleep(2)

async def main():
    """
    Main entry point for the server.
    Starts the server, periodic GET request, and connection checking tasks.
    """
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    # Start periodic tasks
    asyncio.create_task(periodic_get_request())
    asyncio.create_task(check_connections_and_notify())

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())