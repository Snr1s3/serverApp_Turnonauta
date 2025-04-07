import asyncio
import aiohttp

HOST = '0.0.0.0'
PORT = 8444

dict_torurnaments = {}
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Connection from {addr}")

    data = await reader.read(100)  # Read up to 100 bytes
    print(f"Received: {data.decode()} from {addr}")

    data = data.decode().strip()
    data = data.split(",")
    print(f"Data: {data}")
    
    # Respond to the client
    writer.write(b"Data received!\n")
    await writer.drain()
    
    writer.close()
    await writer.wait_closed()
async def periodic_get_request():
    url = "https://turnonauta.asegura.dev:8443/tournaments/active"  
    i = 0
    while i < 4:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    print(f"GET {url} - Status: {response.status}")
                    if response.status == 200:
                        # Parse the response as JSON
                        data = await response.json()
                        # Debugging: Print the raw data
                        #print(f"Raw response data: {data}")
                        # Extract and print `id` and `nom` fields
                        for item in data:
                            #print(f"Raw item data: {item}")  # Debugging
                            id_tournament = item.get('id_torneig')  # Ensure id_tournament is a string
                            nom = item.get('nom')
                            if id_tournament not in dict_torurnaments:
                                dict_torurnaments[id_tournament] = {}
                            print(f"id: {id_tournament}, nom: {nom}")
                    else:
                        print(f"Failed to fetch data. Status: {response.status}")
            except Exception as e:
                print(f"Error during GET request: {e}")
        await asyncio.sleep(2)
        i += 1  # Wait for 2 seconds before the next request
    print("Finished periodic GET requests.")
    for id_tournament, data in dict_torurnaments.items():
        print(f"ID: {id_tournament}, Data: {data}")

async def main():
    # Start the periodic GET request task
    asyncio.create_task(periodic_get_request())
    
    # Start the server
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())