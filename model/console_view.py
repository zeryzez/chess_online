import chess

class GameModel:
    """
    Modèle du jeu d'échecs.
    Gère l'état du plateau, l'historique des coups, et la logique de légalité.
    """
    def __init__(self):
        self.board = chess.Board()

    def reset(self):
        """Réinitialise le plateau à la position de départ."""
        self.board.reset()

    def apply_moves(self, moves_uci):
        """Applique une liste de coups en UCI (['e2e4', ...])."""
        self.reset()
        for uci in moves_uci:
            self.board.push_uci(uci)

    def get_moves(self):
        """Retourne la liste des coups joués en UCI."""
        return [move.uci() for move in self.board.move_stack]

    def get_fen(self):
        """Retourne la position actuelle en notation FEN."""
        return self.board.fen()

    def is_game_over(self):
        """Indique si la partie est terminée."""
        return self.board.is_game_over()

    def parse_san(self, san):
        """Convertit une notation SAN en objet Move."""
        return self.board.parse_san(san)

    def is_legal(self, move):
        """Vérifie si un objet Move est légal dans la position actuelle."""
        return move in self.board.legal_moves

    def push(self, move):
        """Applique un objet Move au plateau."""
        self.board.push(move)

    def result(self):
        """Retourne le résultat si la partie est finie (ex: '1-0')."""
        return self.board.result()
