import aiohttp

BASE_URL = "https://turnonauta.asegura.dev:8443/"

async def getPlayersBySos(tournament_id,shared_session):
    """
    Fetch jugadors per SOS
    """
    url = f"{BASE_URL}puntuacions/get_by_tournament_ordered/{tournament_id}"
    try:
        playersSos = []
        async with shared_session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for puntuacio in data:
                    player_id = puntuacio["id_usuari"]
                    print("Player ID:", player_id)
                    playersSos.append(player_id)
                return playersSos
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
            return [] 
    except Exception as e:
        print(f"Error during GET request: {e}")

async def getRondesAcabades(tournament_id,shared_session):
    """
    Fetch rondes acabades
    """
    url = f"{BASE_URL}rondes/ronda_acabada?torneig_id={tournament_id}"
    try:
        async with shared_session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data == 0:
                    return True
                else:
                    return False
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
                return None
    except Exception as e:
        print(f"Error during GET request: {e}")
        return None

async def post_add_puntuacio(user_id, tournament_id,shared_session):
    """
    Post de puntuacions
    """
    url = BASE_URL + "puntuacions/add"
    payload = {
        "id_torneig": tournament_id,
        "id_usuari": user_id,
        "sos": 0,
        "victories": 0,
        "empat": 0,
        "derrotes": 0,
        "punts": 0
    }

    try:
        async with shared_session.post(url, json=payload) as response:
            if response.status in (200, 201):
                data = await response.json()
                #print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during POST request: {e}")
        
async def post_add_ronda(id_jugador1, id_jugador2, tournament_id,shared_session):
    """
    Post de rondes
    """
    url = BASE_URL + "rondes/add"
    payload = {
        "id_torneig": tournament_id,
        "id_player1": id_jugador1,
        "id_player2":  id_jugador2
    }

    try:
        print(f"Adding ronda {id_jugador1} vs {id_jugador2} to tournament {tournament_id}")
        async with shared_session.post(url, json=payload) as response:
            if response.status in (200, 201):
                data = await response.json()
                #print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during POST request: {e}")

async def delete_puntuacions_tournament(tournament_id,shared_session):
    """
    Eliminar puntuacions d'un torneig
    """
    print(f"Deleting puntuacions for tournament {tournament_id}")
    url = f"{BASE_URL}puntuacions/delete_puntuacions_tournament/{tournament_id}"

    try:
        async with shared_session.delete(url) as response:
            if response.status == 200:
                data = await response.json()
                #print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during DELETE request: {e}")

async def delete_puntuacions_user(user_id, tournament_id,shared_session):
    """
    Eliminar puntuacions d'un jugador
    """
    
    url = f"{BASE_URL}puntuacions/delete_by_user/{user_id}/{tournament_id}"

    try:
        async with shared_session.delete(url) as response:
            if response.status == 200:
                data = await response.json()
               # print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during DELETE request: {e}")