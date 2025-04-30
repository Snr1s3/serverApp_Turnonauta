import asyncio
import aiohttp 
from models.Jugador import Jugador
from models.Torneig import Torneig
from api_connections import (
    post_add_puntuacio,
    delete_puntuacions_tournament,
    delete_puntuacions_user,
)
# Server configuration
HOST = '0.0.0.0'
PORT = 8444
shared_session = None

BASE_URL = "https://turnonauta.asegura.dev:8443/"

# Dictionary to store tournaments
dict_tournaments = {}

# List to store all players
players = []


async def handle_client(reader, writer):
    """
    Connexio client.
    """
    global shared_session
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    try:
        # Llegir el missatge del client
        data = await reader.read(100)
        message = data.decode().strip()
        print(f"Received: {message} from {addr}")

        # Parsejar el missatge
        codi, tournament_id, player_id, player_name = parse_client_message(message)
        # Registrar el jugador
        await register_player(tournament_id, player_id,player_name, writer)

    except ValueError as e:
        
        writer.write(f"{str(e)}\n".encode())
        await writer.drain()

async def periodic_get_request(shared_session):
    """
    Periodically fetch active tournaments and save them to dict_tournaments.
    """
    url = BASE_URL + "tournaments/active"
    try:
        async with shared_session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for item in data:
                    tournament_id = str(item.get('id_torneig'))
                    num_players = item.get('num_jugadors')

                    create_tournament(tournament_id, num_players)

                    print(f"Saved tournament: id={tournament_id}, max players={num_players}")
            else:
                print(f"Failed to fetch data. Status: {response.status}")
    except Exception as e:
        print(f"Error during GET request: {e}")

def parse_client_message(message):
    """
    Parsejar el missatge del client.
    """
    try:
        codi = message.split(".")[0]
        if codi == "0":
            codi, tournament_id, player_id, player_name = message.split(".")
            return codi, tournament_id, player_id, player_name
    except ValueError:
        raise ValueError("Invalid data format. Use 'codi.tournament_id.player_id.player_name'.")


async def register_player(tournament_id, player_id, player_name, writer):
    global shared_session
    # Verify if the tournament is valid
    print("Current Tournaments:", dict_tournaments)
    if tournament_id not in dict_tournaments:
        writer.write(b"Invalid Tournament.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Verify if the player is already registered
    if is_player_registered(player_id):
        writer.write(b"Player ID already registered in another tournament.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Get the tournament
    tournament = dict_tournaments[tournament_id]

    try:
        # Add the player to the global players list
        # Create a new player if not found
        print(f"Creating player {player_id} for tournament {tournament_id}")
        player = Jugador(player_id, tournament_id, player_name, writer)
        players.append(player)

        # Add the player to the tournament
        tournament.add_player(player)
        
        await delete_puntuacions_tournament(tournament_id, shared_session)
        # Call post_add_puntuacio with shared_session

        # Notify all players in the tournament
        player_names = [p.nom for p in tournament.players]
        notification = f"1.{'.'.join(player_names)}\n"
        
        for p in tournament.players:
                
                await post_add_puntuacio(p.id_jugador, p.id_torneig, shared_session)
                await p.send_message(notification)
            

    except ValueError as e:
        writer.write(f"{str(e)}\n".encode())
        await writer.drain()


def is_player_registered(player_id):
    """
    Verificar si el jugador ja està registrat.
    """
    for tournament in dict_tournaments.values():
        if player_id in tournament.players:
            return True
    return False


def create_tournament(tournament_id, num_players):
    """
    Crear un torneig.
    """
    if tournament_id in dict_tournaments:
        return False
    dict_tournaments[tournament_id] = Torneig(tournament_id, num_players)
    return True

def print_tournaments():
    """
    Prints tornejos
    """
    print("\nCurrent Tournaments:")
    for tournament in dict_tournaments.values():
        print(f"Tournament: {tournament.id_torneig}")
        for player_id in tournament.players:
            print(f"  Player ID: {player_id}")
async def check_connections_and_notify():
    """
    Periodically checks the connection with all players and sends an updated list
    of players in each tournament to all connected players.
    """
    global shared_session
    print("Checking connections and notifying players...")
    while True:
        for tournament_id, tournament in dict_tournaments.items():
            # Get the list of player names in the tournament
            player_names = [p.nom for p in tournament.players]
            notification = f"1.{'.'.join(player_names)}\n"
            print(f"Sending notification to tournament {tournament_id}: {notification}")
            disconnected_players = []
            for p in tournament.players:
                if p:
                    try:
                        # Send the updated player list to the player
                        print(f"Sending notification to player {p.id_jugador}")
                        if (await p.send_message(notification) == 1):
                            # If sending fails, mark the player as disconnected
                            print(f"Failed to send message to player {p.id_jugador}. Marking as disconnected.")
                            await delete_puntuacions_user(p.id_jugador, tournament_id, shared_session)
                            disconnected_players.append(p.id_jugador)
                    except (ConnectionResetError, BrokenPipeError):
                        # Handle disconnected players
                        print(f"Connection lost with player {p.id_jugador}. Removing from tournament.")
                        disconnected_players.append(p)
            print(f"Disconnected players: {disconnected_players}")
            # Remove disconnected players from the tournament
            for p_id in disconnected_players:
                print(f"Removing player {p_id} from tournament {tournament_id}")
                if p_id in tournament.players:
                    tournament.players.remove(p_id)
                if p_id in players:
                    players.remove(p_id)

        # Wait for 2 seconds before the next check
        await asyncio.sleep(2)

async def main():
    """
    Main entry point for the server.
    Starts the server, periodic GET request, and connection checking tasks.
    """
    global shared_session
    shared_session = aiohttp.ClientSession()  # Initialize the shared session

    try:
        server = await asyncio.start_server(handle_client, HOST, PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server running on {addr}")
        # Start periodic tasks
        asyncio.create_task(periodic_get_request(shared_session))
        asyncio.create_task(check_connections_and_notify())
        async with server:
            await server.serve_forever()
    finally:
        await shared_session.close()

if __name__ == "__main__":
    asyncio.run(main())