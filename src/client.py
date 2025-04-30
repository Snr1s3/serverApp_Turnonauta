import asyncio
import argparse

HOST = '52.20.160.197'
PORT = 8444    

async def client(client_id):
    reader, writer = await asyncio.open_connection(HOST, PORT)
    tournament_id = "7"
    player_id = client_id
    message = f"0.{tournament_id}.{player_id}.player{player_id}"
    print(f"Sending: {message}")
    writer.write(message.encode())
    await writer.drain()

    try:
        while True:
            response = await reader.read(100)
            if not response:
                print("Server closed the connection.")
                break
            print(f"Received: {response.decode()}")

            # Send a keep-alive message every 10 seconds
            await asyncio.sleep(10)
            writer.write(b"KEEP_ALIVE\n")
            await writer.drain()
    except asyncio.CancelledError:
        print("Connection closed by the client.")
    finally:
        print("Closing the connection")
        writer.close()
        await writer.wait_closed()

async def main():
    # Run 4 clients concurrently
    tasks = [client(i) for i in range(2, 6)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())