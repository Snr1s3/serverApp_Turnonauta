import asyncio
import aiohttp

HOST = '0.0.0.0'
PORT = 8444

dict_torurnaments = {}
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")
    data = await reader.read(100)
    print(f"Received: {data.decode()} from {addr}")
    # Decode and clean the data
    data = data.decode().strip()    
    print(f"Data: {data}")
    try:
        tournament_id, player_id = data.split(":")  # Split the data into tournament ID and player ID
    except ValueError:
        writer.write(b"Invalid data format. Use 'tournament_id:player_id'.\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return
    
    # Store the player in the dictionary under the tournament ID
    if tournament_id not in dict_torurnaments:
        dict_torurnaments[tournament_id] = []  # Create a list for players if not exists
    
    # Add the player to the tournament
    dict_torurnaments[tournament_id].append({"player_id": player_id, "writer": writer})
    print(f"Updated tournaments: {dict_torurnaments}")
    
    # Respond to the client
    writer.write(b"Registered for the tournament!\n")
    await writer.drain()
async def periodic_get_request():
    url = "https://turnonauta.asegura.dev:8443/tournaments/active"  
    i = 0
    while i < 4:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    print(f"GET {url} - Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        for item in data:
                            id_tournament = item.get('id_torneig')  
                            nom = item.get('nom')
                            if id_tournament not in dict_torurnaments:
                                id_tournament = str(id_tournament)
                                dict_torurnaments[id_tournament] = {}
                            print(f"id: {id_tournament}, nom: {nom}")
                    else:
                        print(f"Failed to fetch data. Status: {response.status}")
            except Exception as e:
                print(f"Error during GET request: {e}")
        await asyncio.sleep(2)
        i += 1 
    print("Finished periodic GET requests.")
    for id_tournament, data in dict_torurnaments.items():
        print(f"ID: {id_tournament}, Data: {data}")

async def main():
    asyncio.create_task(periodic_get_request())
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())