# services/lichess_service.py

import berserk
import time
from requests.exceptions import Timeout, ConnectionError
from berserk.exceptions import ResponseError

class LichessService:
    def __init__(self, token: str):
        session = berserk.TokenSession(token)
        self.client = berserk.Client(session)

    # ——— Partie / streaming ———

    def stream_incoming_events(self):
        return self.client.board.stream_incoming_events()

    def stream_game_state(self, game_id: str):
        return self.client.board.stream_game_state(game_id)

    # ——— Coup ———

    def make_move(self, game_id: str, move_uci: str):
        # (ici timeout/retry si tu veux)
        return self.client.board.make_move(game_id, move_uci)

    def resign(self, game_id: str):
        return self.client.board.resign_game(game_id)

    # ——— Challenges & seeks ———

    def challenge_bot(self, level=1, clock_limit=600, clock_increment=5):
        """
        Défie un bot public sur Lichess (non classé).
        Retourne la réponse brute pour extraction.
        """
        return self._retry(
            self.client.challenges.create_ai,
            level=level,
            clock_limit=clock_limit,
            clock_increment=clock_increment,
            color='random',
        )

    def challenge_user(self, username: str, clock_limit=600, clock_increment=5, rated=True):
        """
        Défie un utilisateur Lichess selon les paramètres temporels.
        """
        return self._retry(
            self.client.challenges.create,
            username,
            rated=rated,
            clock_limit=clock_limit,
            clock_increment=clock_increment,
            color='random'
        )

    def create_seek(self, clock_limit=600, clock_increment=5, rated=False, variant="standard"):
        """
        Ouvre un seek public (matchmaking aléatoire) selon la cadence donnée.
        """
        return self._retry(
            self.client.challenges.create_open,
            clock_limit=clock_limit,
            clock_increment=clock_increment,
            rated=rated,
            variant=variant
        )

    # ——— Helpers pour extraire game_id/url ———

    def _retry(self, fn, *args, max_retries=3, initial_backoff=1, **kwargs):
        """
        Helper générique pour relancer fn(*args, **kwargs) en cas d'erreur réseau.
        """
        backoff = initial_backoff
        for attempt in range(1, max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except (Timeout, ConnectionError, ResponseError) as e:
                if attempt == max_retries:
                    # Au dernier essai, on remonte l'erreur
                    raise
                time.sleep(backoff)
                backoff *= 2

    @staticmethod
    def extract_game_info(response: dict):
        """
        Extrait (game_id, game_url) depuis la réponse Lichess.
        """
        try:
            # Récupération de l'ID à partir de la réponse
            game_id = response.get('id', None)
            
            if not game_id:
                raise ValueError("ID de partie manquant dans la réponse.")
                
            # L'URL du jeu (généralement sous la forme lichess.org/{id})
            game_url = f"https://lichess.org/{game_id}"

            return game_id, game_url
        except Exception as e:
            raise ValueError(f"Erreur lors de l'extraction de l'ID du jeu : {e}")

    
