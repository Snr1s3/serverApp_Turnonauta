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
    data = data.decode().strip()
    data = data.split(",")
    data = data.replace("'", "") 
    data = data.replace("[", "") 
    data = data.replace("]", "") 
    print(f"Data: {data}")
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
                        data = await response.json()
                        for item in data:
                            id_tournament = item.get('id_torneig')  
                            nom = item.get('nom')
                            if id_tournament not in dict_torurnaments:
                                dict_torurnaments[''+id_tournament] = {}
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