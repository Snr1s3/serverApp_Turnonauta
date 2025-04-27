import aiohttp

BASE_URL = "https://turnonauta.asegura.dev:8443/"




async def periodic_get_request(shared_session):
    """
    Gets de tornejos actius.
    """
    url = BASE_URL + "tournaments/active"
    try:
        async with shared_session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for item in data:
                    tournament_id = str(item.get('id_torneig'))
                    num_players = item.get('num_jugadors')
                    print(f"id: {tournament_id}, max players: {num_players}")
            else:
                print(f"Failed to fetch data. Status: {response.status}")
    except Exception as e:
        print(f"Error during GET request: {e}")

async def post_add_puntuacio(user_id, tournament_id,shared_session):
    """
    Perform a POST request to the server to add a new puntuacio.
    """
    url = BASE_URL + "puntuacions/add"
    payload = {
        "id_torneig": tournament_id,
        "id_usuari": user_id,
        "victories": 50,
        "derrotes": 0,
        "punts": 0
    }

    try:
        async with shared_session.post(url, json=payload) as response:
            if response.status in (200, 201):
                data = await response.json()
                print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during POST request: {e}")

async def delete_puntuacions_tournament(tournament_id,shared_session):
    """
    Perform a DELETE request to the server to remove all puntuacions for a tournament.
    """
    url = f"{BASE_URL}puntuacions/delete_puntuacions_tournament/{tournament_id}"

    try:
        async with shared_session.delete(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during DELETE request: {e}")

async def delete_puntuacions_user(user_id, tournament_id):
    """
    Perform a DELETE request to the server to remove all puntuacions for a user in a tournament.
    """
    global shared_session
    url = f"{BASE_URL}puntuacions/delete_by_user/{user_id}/{tournament_id}"

    try:
        async with shared_session.delete(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Success: {data}")
            else:
                error = await response.json()
                print(f"Failed: {response.status}, {error}")
    except Exception as e:
        print(f"Error during DELETE request: {e}")