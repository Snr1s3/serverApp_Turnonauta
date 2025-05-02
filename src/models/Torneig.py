import math

class Torneig:

    def __init__(self, id_torneig, max_players, format):
        self.id_torneig = id_torneig
        self.max_players = max_players
        self.players = []
        self.format = format
        self.status = "waiting"
        self.round = 0
        self.max_rounds = math.ceil(math.log2(max_players))
        print("Number of rounds: ", self.max_rounds)

    def add_player(self, player_id):
        if len(self.players) >= self.max_players:
            raise ValueError("E.Tournament is full.")
        if player_id in self.players:
            raise ValueError("E.Player is already registered in this tournament.")
        self.players.append(player_id)

    def check_number_of_players(self):
        if len(self.players) == self.max_players:
            self.status = "ready"
            return True
        else:
            self.status = "waiting"
            return False
    
    def __str__(self):
        return f"Torneig(id_torneig={self.id_torneig}, players={[str(player) for player in self.players]})"