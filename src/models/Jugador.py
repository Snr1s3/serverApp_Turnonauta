class Jugador:
    def __init__(self, id_jugador, id_torneig, player_name, writer):
        self.id_jugador = id_jugador
        self.id_torneig = id_torneig
        self.nom = player_name
        self.sos = 0
        self.victories = 0
        self.empat = 0
        self.derrotes = 0
        self.punts = 0
        self.writer = writer

    
    async def send_message(self, message):
        """
        Enviar missatge al jugador
        """
        try:
            self.writer.write(message.encode())
            await self.writer.drain()
            return 0
        except Exception as e:
            return 1
    

    def __str__(self):
        """
        TO STRING
        """
        return f"Jugador(id_jugador={self.id_jugador}, id_torneig={self.id_torneig}, nom={self.nom})"