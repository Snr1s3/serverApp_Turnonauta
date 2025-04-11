import asyncio
import aiohttp 
from models.Jugador import Jugador
from models.Torneig import Torneig

HOST = '0.0.0.0'
PORT = 8444

# Dictionary to store Torneig objects
dict_tournaments = {}


async def handle_client(reader, writer):
    """Handles incoming client connections."""
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    try:
        data = await reader.read(100)
        message = data.decode().strip()
        print(f"Received: {message} from {addr}")

        tournament_id, player_id = parse_client_message(message)
        await register_player(tournament_id, player_id, writer)

    except ValueError as e:
        writer.write(f"{str(e)}\n".encode())
        await writer.drain()


def parse_client_message(message):
    try:
        tournament_id, player_id = message.split(".")
        return tournament_id, player_id
    except ValueError:
        raise ValueError("Invalid data format. Use 'tournament_id.player_id'.")


async def register_player(tournament_id, player_id, writer):
    """Registers a player to a tournament and notifies all players in the tournament."""
    if tournament_id not in dict_tournaments:
        raise ValueError("Invalid Tournament.")

    if is_player_registered(player_id):
        raise ValueError("Player ID already registered in another tournament.")

    tournament = dict_tournaments[tournament_id]
    player = Jugador(player_id, tournament_id, writer)
    try:
        tournament.add_player(player)
        writer.write(b"Registered for the tournament!\n")
        await writer.drain()

        # Notify all players in the tournament
        notification = f"Player {player_id} has joined the tournament {tournament_id}.\n"
        disconnected_players = []
        for p in tournament.players:
            if p.writer != writer:  # Avoid notifying the player who just joined
                try:
                    p.writer.write(notification.encode())
                    await p.writer.drain()
                except ConnectionResetError:
                    print(f"Connection lost with player {p.id_jugador}. Removing from tournament.")
                    disconnected_players.append(p)

        # Remove disconnected players
        for p in disconnected_players:
            tournament.players.remove(p)

        print_tournaments()
    except ValueError as e:
        raise ValueError(str(e))


def is_player_registered(player_id):
    for tournament in dict_tournaments.values():
        for player in tournament.players:
            if player.id_jugador == player_id:
                return True
    return False


def create_tournament(tournament_id, num_players):
    if tournament_id in dict_tournaments:
        return False 
    dict_tournaments[tournament_id] = Torneig(tournament_id, num_players)
    return True  


async def periodic_get_request():
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
    print("\nCurrent Tournaments:")
    for tournament in dict_tournaments.values():
        print(f"Tournament: {tournament.id_torneig}")
        for player in tournament.players:
            print(f"  Player: {player.id_jugador}")


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    asyncio.create_task(periodic_get_request())

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())