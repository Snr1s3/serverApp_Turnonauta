import asyncio
import argparse

HOST = '127.0.0.1'
PORT = 8445    

async def client(client_id):
    reader, writer = await asyncio.open_connection(HOST, PORT)
    tournament_id = "4"
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
            print(f"Received: {response.decode()}\n")
            print("Sending keep-alive message...")
            # Send a keep-alive message every 10 seconds
            await asyncio.sleep(10)
            #writer.write(b"KEEP_ALIVE\n")
            await writer.drain()
    except asyncio.CancelledError:
        print("Connection closed by the client.")
    finally:
        print("Closing the connection")
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client for connecting to the server.")
    parser.add_argument("client_id", type=str, help="The ID of the client.")
    args = parser.parse_args()

    asyncio.run(client(args.client_id))