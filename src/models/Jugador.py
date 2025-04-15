class Jugador:
    def __init__(self, id_jugador, id_torneig, player_name, writer):
        self.id_jugador = id_jugador
        self.id_torneig = id_torneig
        self.nom = player_name
        self.writer = writer

    async def send_message(self, message):
        try:
            self.writer.write(message.encode())
            await self.writer.drain()
        except Exception as e:
            print(f"Error sending message to player {self.id_jugador}: {e}")
    

    def __str__(self):
        return f"Jugador(id_jugador={self.id_jugador}, id_torneig={self.id_torneig}, nom={self.nom})"