class Torneig:

    def __init__(self, id_torneig, max_players):
        self.id_torneig = id_torneig
        self.max_players = max_players
        self.players = []

    def add_player(self, player):
        if len(self.players) >= self.max_players:
            raise ValueError("E.Tournament is full.")
        if player in self.players:
            raise ValueError("E.Player is already registered in this tournament.")
        self.players.append(player)

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
        else:
            raise ValueError("E.Player not found in this tournament.")

    def __str__(self):
        return f"Torneig(id_torneig={self.id_torneig}, max_players={self.max_players}, players={[str(player) for player in self.players]})"