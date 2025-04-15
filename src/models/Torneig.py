class Torneig:

    def __init__(self, id_torneig, max_players):
        self.id_torneig = id_torneig
        self.max_players = max_players
        self.players = []

    def add_player(self, player_id):
        if len(self.players) >= self.max_players:
            raise ValueError("E.Tournament is full.")
        if player_id in self.players:
            raise ValueError("E.Player is already registered in this tournament.")
        self.players.append(player_id)

    def __str__(self):
        return f"Torneig(id_torneig={self.id_torneig}, players={[str(player) for player in self.players]})"