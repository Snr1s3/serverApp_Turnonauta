import asyncio
import aiohttp
import random
from models.Jugador import Jugador
from models.Torneig import Torneig
from api_connections import (
    post_add_puntuacio,
    getPlayersBySos,
    delete_puntuacions_tournament,
    post_add_ronda,
    getRondesAcabades,
    delete_puntuacions_user,
)

# SERVIDOR
HOST = '0.0.0.0'
PORT = 8444
BASE_URL = "https://turnonauta.asegura.dev:8443/"

# VARIABLES GLOBALS
shared_session = None
dict_tournaments = {}  
players = []  


# -------------------- Utility --------------------

def is_player_registered(player_id):
    """
    Mirar si un jugador ja està registrat en un torneig.
    """
    return any(player_id in tournament.players for tournament in dict_tournaments.values())


def create_tournament(tournament_id, max_players, format):
    """
    Crear un torneig.
    """
    if tournament_id not in dict_tournaments:
        dict_tournaments[tournament_id] = Torneig(tournament_id, max_players, format)
        print(f"Saved tournament: id={tournament_id}, max players={max_players}, format={format}")
        return True
    return False


def print_tournaments():
    """
    Print dels tornejos actius.
    """
    print("\nCurrent Tournaments:")
    for tournament in dict_tournaments.values(): 
        print(f"Tournament: {tournament.id_torneig}")
        for player in tournament.players:
            print(f"  Player ID: {player.id_jugador}")


async def send_error_message(writer, message):
    """
   Enviar missatge d'error al client.
    """
    writer.write(message.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


# -------------------- Clients Handling --------------------

async def handle_client(reader, writer):
    """
    Handle connexions dels clients.
    """
    global shared_session
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    try:
        data = await reader.read(100)
        message = data.decode().strip()
        print(f"Received: {message} from {addr}")
        codi, tournament_id, player_id, player_name = parse_client_message(message)

        await register_player(tournament_id, player_id, player_name, writer)

    except ValueError as e:
        await send_error_message(writer, f"{str(e)}\n")


def parse_client_message(message):
    """
    Parsejar el missatge del client.
    """
    try:
        codi, tournament_id, player_id, player_name = message.split(".")
        if codi == "0":
            return codi, tournament_id, player_id, player_name
    except ValueError:
        raise ValueError("Invalid data format. Use 'codi.tournament_id.player_id.player_name'.")


async def register_player(tournament_id, player_id, player_name, writer):
    """
    Registrar un jugador en un torneig.
    """
    global shared_session

    if tournament_id not in dict_tournaments:
        await send_error_message(writer, "Invalid Tournament.\n")
        return

    if is_player_registered(player_id):
        await send_error_message(writer, "Player ID already registered in another tournament.\n")
        return

    tournament = dict_tournaments[tournament_id]
    player = Jugador(player_id, tournament_id, player_name, writer)
    players.append(player)
    tournament.add_player(player)

    await notify_tournament_players(tournament,1)

    await post_add_puntuacio(player.id_jugador, player.id_torneig, shared_session)
    print_tournaments()

async def start_tournament():
    """
    Començar el torneig.
    """
    for id, tournament in dict_tournaments.items():
        if tournament.check_number_of_players() and  tournament.status == "waiting":
            print(f"Tournament {tournament.id_torneig} is ready to start.")
            tournament.status = "started"
            await make_parings(tournament)
        elif tournament.round > 0:
            await make_parings(tournament)
    
async def make_parings(tournament):
    """
    Fer els emparellaments per al torneig.
    """
    global players
    global shared_session
    tournaments_players = []
    paired_players = []
    print(f"Creating pairings for tournament {tournament.id_torneig}")
    if tournament.round == 0:
        print("Seguent ronda")
        paired_players = []
        await notify_tournament_players(tournament, 2)
        tournaments_players = await getPlayersBySos(tournament.id_torneig, shared_session)
        print("Number of players:", len(tournaments_players))
        t_length = int((len(tournaments_players))/2)
        print("Number of pairings:", t_length)
        for i in range(0, t_length):     
            if len(tournaments_players) >= 2:
                player1 = tournaments_players[0]
                player2 = tournaments_players[1]
                tournaments_players.remove(player1)
                tournaments_players.remove(player2)
                paired_players.append((player1, player2))
                await post_add_ronda(player1, player2, tournament.id_torneig, shared_session)
                print(f"Paired players: {player1} and {player2}")
        tournament.round += 1
    if tournament.round > 0:
        acabades = await getRondesAcabades(tournament.id_torneig, shared_session)
        print ("Acabades: ", acabades)
        if acabades:
            if tournament.round < tournament.max_rounds:
                print("Seguent ronda")
                paired_players = []
                await notify_tournament_players(tournament, 2)
                tournaments_players = await getPlayersBySos(tournament.id_torneig, shared_session)
                print("Number of players:", len(tournaments_players))
                t_length = int((len(tournaments_players))/2)
                print("Number of pairings:", t_length)
                for i in range(0, t_length):     
                    if len(tournaments_players) >= 2:
                        player1 = tournaments_players[0]
                        player2 = tournaments_players[1]
                        tournaments_players.remove(player1)
                        tournaments_players.remove(player2)
                        paired_players.append((player1, player2))
                        await post_add_ronda(player1, player2, tournament.id_torneig, shared_session)
                        print(f"Paired players: {player1} and {player2}")
                tournament.round += 1
            else:
                if(tournament.status != "finished"):
                    await notify_tournament_players(tournament, 3)
                    tournament.status = "finished"

                    for player in players:  
                        if player.id_torneig == tournament.id_torneig:
                            try:
                                print(f"Notified player {player.id_jugador} about tournament end.")
                                player.writer.close()
                            except (ConnectionResetError, BrokenPipeError):
                                print(f"Failed to notify player {player.id_jugador}.")
                            tournament.players.remove(player)
                            players.remove(player)
                            print(f"Player {player.id_jugador} removed from tournament {tournament.id_torneig}.")

                print(f"All players disconnected from tournament {tournament.id_torneig}.")
            

                
async def notify_tournament_players(tournament,code):
    """
    Notifiacar jugaors en un torneig.
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
    Elimina jugador desconectat del torneig.
    """
    tournament.players.remove(player)
    players.remove(player)
    await delete_puntuacions_user(player.id_jugador, tournament.id_torneig, shared_session)


# -------------------- Tasques periodiques --------------------

async def periodic_get_request(shared_session):
    """
    Fetch tornejos actius
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
        await asyncio.sleep(10)



async def check_connections_and_notify():
    """
    Verifica la connexió dels jugadors i notifica els tornejos.
    """
    while True:
        await start_tournament()
        for tournament_id, tournament in dict_tournaments.items():
            await notify_tournament_players(tournament, 1)
        await asyncio.sleep(2)  


# -------------------- Main --------------------

async def main():
    """
    Funcion principal del servidor.
    """
    global shared_session
    shared_session = aiohttp.ClientSession()

    try:
        server = await asyncio.start_server(handle_client, HOST, PORT)
        addr = server.sockets[0].getsockname()
        print(f"Server running on {addr}")

        # Tasques periodiques
        asyncio.create_task(periodic_get_request(shared_session))
        asyncio.create_task(check_connections_and_notify())

        async with server:
            await server.serve_forever()
    finally:
        await shared_session.close()


if __name__ == "__main__":
    asyncio.run(main())