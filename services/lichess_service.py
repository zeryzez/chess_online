# services/lichess_service.py

import berserk
import time
from requests.exceptions import Timeout

class LichessService:
    def __init__(self, token):
        session = berserk.TokenSession(token)
        self.client = berserk.Client(session)

    def create_challenge(self, opponent, clock_limit, clock_increment):
        return self.client.challenges.create(
            opponent,
            rated=False,
            clock_limit=clock_limit,
            clock_increment=clock_increment,
            color='random'
        )

    def resign(self, game_id):
        self.client.board.resign_game(game_id)

    def make_move(self, game_id, move_uci):
        """
        Envoi robuste d'un coup : timeout + retry exponentiel.
        """
        max_retries = 4
        backoff = 1
        for attempt in range(1, max_retries + 1):
            try:
                # Si berserk exposait timeout, on pourrait le passer ici.
                return self.client.board.make_move(game_id, move_uci)
            except Exception as e:
                is_timeout = isinstance(e, Timeout) or 'timeout' in str(e).lower()
                if attempt == max_retries:
                    # Dernière tentative, on remonte l'erreur
                    raise
                # Log ou affichage : on recule la prochaine tentative
                print(f"⚠️ Erreur réseau ({'timeout' if is_timeout else 'autre'}), "
                      f"tentative {attempt}/{max_retries} dans {backoff}s…")
                time.sleep(backoff)
                backoff *= 2

    def stream_incoming_events(self):
        return self.client.board.stream_incoming_events()

    def stream_game_state(self, game_id):
        return self.client.board.stream_game_state(game_id)
