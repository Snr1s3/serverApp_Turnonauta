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


async def register_player(tournament_id, player_id,player_name, writer):
    # Verificar si el torneig és vàlid
    if tournament_id not in dict_tournaments:
        writer.write(b"Invalid Tournament.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Verificar si el jugador ja està registrat
    if is_player_registered(player_id):
        writer.write(b"Player ID already registered in another tournament.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Agafar el torneig
    tournament = dict_tournaments[tournament_id]

    try:
        # Afegir jugador a la llista de jugadors
        if not any(p.id_jugador == player_id for p in players):
            players.append(Jugador(player_id, tournament_id, player_name, writer))

        # Afegir jugador al torneig
        tournament.add_player(player_id)
        writer.write(b"Registered for the tournament!\n")
        await writer.drain()

        # Notificar tots els jugadors del torneig
        player_names = [p.nom for p in players if p.id_jugador in tournament.players]
        notification = (
            f"{'.'.join(player_names)}\n"
        )
        disconnected_players = []
        for p_id in tournament.players:
            p = next((pl for pl in players if pl.id_jugador == p_id), None)
            try:
                p.writer.write(notification.encode())
                await p.writer.drain()
            except ConnectionResetError:
                print(f"Connection lost with player {p.id_jugador}. Removing from tournament.")
                disconnected_players.append(p_id)

        # Eliminar desconnectats
        for p_id in disconnected_players:
            tournament.players.remove(p_id)

        print_tournaments()
    except ValueError as e:
        writer.write(f"{str(e)}\n".encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()


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


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    # Gets
    asyncio.create_task(periodic_get_request())

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())