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
    Connexio client.
    """
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


def parse_client_message(message):
    """
    Parsejar el missatge del client.
    """
    try:
        codi, tournament_id, player_id, player_name = message.split(".")
        return codi, tournament_id, player_id, player_name
    except ValueError:
        raise ValueError("Invalid data format. Use 'codi.tournament_id.player_id.player_name'.")


async def register_player(tournament_id, player_id, player_name, writer):
    # Verify if the tournament is valid
    if tournament_id not in dict_tournaments:
        await Jugador(player_id, tournament_id, player_name, writer).send_message("Invalid Tournament.\n")
        return

    # Verify if the player is already registered
    if is_player_registered(player_id):
        await Jugador(player_id, tournament_id, player_name, writer).send_message("Player ID already registered in another tournament.\n")
        return

    # Get the tournament
    tournament = dict_tournaments[tournament_id]

    try:
        # Add the player to the global players list
        if not any(p.id_jugador == player_id for p in players):
            player = Jugador(player_id, tournament_id, player_name, writer)
            players.append(player)

        # Add the player to the tournament
        tournament.add_player(player)

        # Notify all players in the tournament
        player_names = [p.nom for p in tournament.players]
        notification = f"1.{'.'.join(player_names)}\n"
        for p in tournament.players:
            await p.send_message(notification)

    except ValueError as e:
        await Jugador(player_id, tournament_id, player_name, writer).send_message(f"{str(e)}\n")


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


async def periodic_get_request():
    """
    Gets de tornejos actius.
    """
    url = "https://turnonauta.asegura.dev:8443/tournaments/active"
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
    while True:
        for tournament_id, tournament in dict_tournaments.items():
            # Get the list of player names in the tournament
            player_names = [p.nom for p in tournament.players]
            notification = f"1.{'.'.join(player_names)}\n"

            disconnected_players = []
            for player in tournament.players:
                try:
                    # Use the send_message method to send the notification
                    await player.send_message(notification)
                except Exception as e:
                    # Handle disconnected players
                    print(f"Connection lost with player {player.id_jugador}. Removing from tournament. Error: {e}")
                    disconnected_players.append(player)

            # Remove disconnected players from the tournament
            for player in disconnected_players:
                tournament.players.remove(player)
                players.remove(player)  # Remove from the global players list

        # Wait for 5 seconds before sending the next update
        await asyncio.sleep(5)

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