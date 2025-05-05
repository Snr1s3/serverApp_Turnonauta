import asyncio
import aiohttp
import random
from models.Jugador import Jugador
from models.Torneig import Torneig
from api_connections import (
    post_add_puntuacio,
    delete_puntuacions_tournament,
    post_add_ronda,
    getRondesAcabades,
    delete_puntuacions_user,
)

# Server configuration
HOST = '0.0.0.0'
PORT = 8444
BASE_URL = "https://turnonauta.asegura.dev:8443/"

# Global variables
shared_session = None
dict_tournaments = {}  # Stores all tournaments
players = []  # Stores all players


# -------------------- Utility Functions --------------------

def is_player_registered(player_id):
    """
    Check if a player is already registered in any tournament.
    """
    return any(player_id in tournament.players for tournament in dict_tournaments.values())


def create_tournament(tournament_id, max_players, format):
    """
    Create a new tournament and add it to the global dictionary.
    """
    if tournament_id not in dict_tournaments:
        dict_tournaments[tournament_id] = Torneig(tournament_id, max_players, format)
        print(f"Saved tournament: id={tournament_id}, max players={max_players}, format={format}")
        return True
    return False


def print_tournaments():
    """
    Print all tournaments and their players.
    """
    print("\nCurrent Tournaments:")
    for tournament in dict_tournaments.values(): 
        print(f"Tournament: {tournament.id_torneig}")
        for player in tournament.players:
            print(f"  Player ID: {player.id_jugador}")


async def send_error_message(writer, message):
    """
    Send an error message to the client and close the connection.
    """
    writer.write(message.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


# -------------------- Client Handling --------------------

async def handle_client(reader, writer):
    """
    Handle incoming client connections.
    """
    global shared_session
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    try:
        # Read and parse the client message
        data = await reader.read(100)
        message = data.decode().strip()
        print(f"Received: {message} from {addr}")

        codi, tournament_id, player_id, player_name = parse_client_message(message)

        # Register the player
        await register_player(tournament_id, player_id, player_name, writer)

    except ValueError as e:
        await send_error_message(writer, f"{str(e)}\n")


def parse_client_message(message):
    """
    Parse the client message and extract relevant information.
    """
    try:
        codi, tournament_id, player_id, player_name = message.split(".")
        if codi == "0":
            return codi, tournament_id, player_id, player_name
    except ValueError:
        raise ValueError("Invalid data format. Use 'codi.tournament_id.player_id.player_name'.")


async def register_player(tournament_id, player_id, player_name, writer):
    """
    Register a player in a tournament.
    """
    global shared_session

    # Check if the tournament exists
    if tournament_id not in dict_tournaments:
        await send_error_message(writer, "Invalid Tournament.\n")
        return

    # Check if the player is already registered
    if is_player_registered(player_id):
        await send_error_message(writer, "Player ID already registered in another tournament.\n")
        return

    # Get the tournament and add the player
    tournament = dict_tournaments[tournament_id]
    player = Jugador(player_id, tournament_id, player_name, writer)
    players.append(player)
    tournament.add_player(player)

    # Notify all players in the tournament
    await notify_tournament_players(tournament)

    # Add the player's puntuacions
    await post_add_puntuacio(player.id_jugador, player.id_torneig, shared_session)
    print_tournaments()

async def start_tournament():
    """
    Start the tournament if the number of players is sufficient.
    """
    print("Checking tournaments...")
    for id, tournament in dict_tournaments.items():
        print("Checking tournament:", id)
        if tournament.check_number_of_players() and  tournament.status == "waiting":
            print(f"Tournament {tournament.id_torneig} is ready to start.")
            tournament.status = "started"
            await make_parings(tournament)
        elif tournament.round > 0:
            await make_parings(tournament)
        print(f"Tournament {tournament.id_torneig} status: {tournament.status}")
    
async def make_parings(tournament):
    """
    Create pairings for the tournament.
    """
    global players
    global shared_session
    tournaments_players = []
    paired_players = []
    print(f"Creating pairings for tournament {tournament.id_torneig}")
    if tournament.round == 0:
        print("First round")
        await get_puntuacions(tournament.id_torneig, shared_session)
        for player in players:
            print("Player ", player)
            if player.id_torneig == tournament.id_torneig:
                tournaments_players.append(player)
        print("Number of players:", len(tournaments_players))
        t_length = int((len(tournaments_players))/2)
        print("Number of pairings:", t_length)
        for i in range(0, t_length):     
            if len(tournaments_players) >= 2:
                index1 = random.randint(0, len(tournaments_players) - 1)
                index2 = random.randint(0, len(tournaments_players) - 1)
                while index1 == index2: 
                    index2 = random.randint(0, len(tournaments_players) - 1)

                player1 = tournaments_players[index1]
                player2 = tournaments_players[index2]
                tournaments_players.remove(player1)
                tournaments_players.remove(player2)
                paired_players.append((player1, player2))
                await post_add_ronda(player1.id_jugador, player2.id_jugador, tournament.id_torneig, shared_session)
                print(f"Paired players: {player1.id_jugador} and {player2.id_jugador}") 
        tournament.round += 1
    if tournament.round > 0:
        if await getRondesAcabades(tournament.id_torneig, shared_session):
            if tournament.round < tournament.max_rounds:
                await notify_tournament_players(tournament, 2)
                tournament.round += 1
            else:
                await notify_tournament_players(tournament, 3)
            

                
async def notify_tournament_players(tournament,code):
    """
    Notify all players in a tournament about the current player list.
    """
    player_names = [p.nom for p in tournament.players]
    if code == 1:
        notification = f"{code}.{'.'.join(player_names)}\n"
    elif code == 2:
        notification = f"{code}.{tournament.id_torneig}.pairing\n"
    elif code == 3:
        notification = f"{code}.{tournament.id_torneig}.end\n"

    for player in tournament.players:
        try:

            num = await player.send_message(notification)
            if num == 1:
                print(f"Failed to send message to player {player.id_jugador}. Removing from tournament.")
                await remove_disconnected_player(player, tournament)
        except (ConnectionResetError, BrokenPipeError):
            print(f"Failed to notify player {player.id_jugador}. Removing from tournament.")
            await remove_disconnected_player(player, tournament)


async def remove_disconnected_player(player, tournament):
    """
    Remove a disconnected player from the tournament and global players list.
    """
    tournament.players.remove(player)
    players.remove(player)
    await delete_puntuacions_user(player.id_jugador, tournament.id_torneig, shared_session)


# -------------------- Periodic Tasks --------------------

async def periodic_get_request(shared_session):
    """
    Periodically fetch active tournaments and save them to dict_tournaments.
    """
    url = BASE_URL + "tournaments/active"
    while True:
        try:
            async with shared_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        tournament_id = str(item.get('id_torneig'))
                        max_players = item.get('num_jugadors')
                        format = item.get('format')
                        create_tournament(tournament_id, max_players, format)
                else:
                    print(f"Failed to fetch data. Status: {response.status}")
        except Exception as e:
            print(f"Error during GET request: {e}")
        await asyncio.sleep(10)  # Fetch every 10 seconds

async def get_puntuacions(tournament_id,shared_session):
    global players
    url = BASE_URL + "puntuacions/get_by_tournament/" + str(tournament_id)
    try:
        async with shared_session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for puntuacio in data:
                    player_id = puntuacio["id_usuari"]
                    if player_id in players:
                        player = players[player_id]
                        player.sos = puntuacio["sos"]
                        player.victories = puntuacio["victories"]
                        player.empat = puntuacio["empat"]
                        player.derrotes = puntuacio["derrotes"]
                        player.punts = puntuacio["punts"]
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during GET request: {e}")

async def check_connections_and_notify():
    """
    Periodically check player connections and notify players in tournaments.
    """
    while True:
        await start_tournament()
        print("Checking connections...")
        for tournament_id, tournament in dict_tournaments.items():
            await notify_tournament_players(tournament, 1)
        await asyncio.sleep(2)  # Check every 2 seconds


# -------------------- Main Entry Point --------------------

async def main():
    """
    Main entry point for the server.
    Starts the server, periodic GET request, and connection checking tasks.
    """
    global shared_session
    shared_session = aiohttp.ClientSession()

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