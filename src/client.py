import asyncio

HOST = '127.0.0.1'
PORT = 8444    

async def client():
    reader, writer = await asyncio.open_connection(HOST, PORT)
    tournament_id = "4"
    player_id = "11122"
    message = f"{tournament_id}.{player_id}"
    print(f"Sending: {message}")
    writer.write(message.encode())
    await writer.drain()

    response = await reader.read(100)
    print(f"Received: {response.decode()}")

    print("Closing the connection")
    writer.close()
    await writer.wait_closed()

asyncio.run(client())