class Torneig:
    def __init__(self, id_torneig, players=None):
        self.id_torneig = id_torneig
        self.players = players if players else []

    def add_player(self, jugador):
        if any(player.id_jugador == jugador.id_jugador for player in self.players):
            raise ValueError(f"Player with ID {jugador.id_jugador} is already in the tournament.")
        self.players.append(jugador)

    def __str__(self):
        return f"Torneig(id_torneig={self.id_torneig}, players={[str(player) for player in self.players]})"