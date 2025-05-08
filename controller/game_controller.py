# controller/game_controller.py

import berserk
import threading
import time
from model.game_model import GameModel
from view.console_view import ConsoleView

class GameController:
    """
    Contrôleur principal : orchestre le modèle, la vue, et l'API Lichess.
    """
    def __init__(self, token):
        session = berserk.TokenSession(token)
        self.client = berserk.Client(session)
        self.model = GameModel()
        self.game_id = None
        self.game_url = None
        self.user_color = None
        self.last_move_count = 0
        self.lock = threading.Lock()

    def challenge(self, opponent="maia1", clock_limit=600, clock_increment=5):
        resp = self.client.challenges.create(
            opponent, rated=False,
            clock_limit=clock_limit, clock_increment=clock_increment,
            color='random'
        )
        url = resp.get("url")
        gid = url.rsplit('/', 1)[-1]
        self.game_id = gid
        self.game_url = url
        ConsoleView.show_message(f"📡 Défi lancé contre {opponent} → {url}")

    def wait_for_start(self):
        ConsoleView.show_message("⏳ En attente du début de la partie…")
        for ev in self.client.board.stream_incoming_events():
            if ev.get("type") == "gameStart":
                self.user_color = ev['game']['color']  # 'white' ou 'black'
                ConsoleView.show_message(f"✅ Partie démarrée ! ID={self.game_id}")
                ConsoleView.show_message(f"🔗 Suivi: {self.game_url}")
                ConsoleView.show_message(f"🟢 Tu joues {self.user_color.upper()}.")
                break

    def listen_moves(self):
        for ev in self.client.board.stream_game_state(self.game_id):
            if ev['type'] not in ("gameFull", "gameState"): continue
            # Récupérer la liste UCI des coups
            if ev['type'] == "gameFull":
                moves = ev['state'].get('moves', '').split()
            else:
                moves = ev.get('moves', '').split()

            # Ignorer si aucun nouveau coup
            if len(moves) == self.last_move_count:
                continue
            self.last_move_count = len(moves)

            # Mettre à jour le modèle avec les coups reçus
            with self.lock:
                self.model.apply_moves(moves)

            # Affichage du plateau mis à jour
            ConsoleView.show_message("\n🔄 Plateau mis à jour :")
            with self.lock:
                ConsoleView.render_board(self.model.board)

    def play(self):
        # Démarre le thread d'écoute pour synchroniser le plateau
        threading.Thread(target=self.listen_moves, daemon=True).start()

        ConsoleView.show_message("🎮 À toi de jouer ! (SAN ex: e4, Nf3) — 'resign' pour abandonner")
        while True:
            with self.lock:
                # Si la partie est terminée, on quitte
                if self.model.is_game_over():
                    ConsoleView.show_message(f"🏁 Partie terminée: {self.model.result()}")
                    break
                # Détermine si c'est ton tour
                my_turn = (self.model.board.turn == (self.user_color == 'white'))

            # Si ce n'est pas ton tour, on attend
            if not my_turn:
                time.sleep(0.5)
                continue

            # Lecture du coup de l'utilisateur
            move_san = ConsoleView.prompt_move()
            if move_san.lower() == 'resign':
                self.client.board.resign_game(self.game_id)
                ConsoleView.show_message("🏳️ Tu as abandonné.")
                break

            # Conversion SAN -> Move avec vérification de légalité
            try:
                with self.lock:
                    move = self.model.parse_san(move_san)
                    if not self.model.is_legal(move):
                        raise ValueError("Coup illégal")
            except ValueError as ve:
                ConsoleView.show_message(f"⚠️ {ve}")
                continue

            # Envoi du coup à Lichess avec gestion de déconnexion réseau
            try:
                self.client.board.make_move(self.game_id, move.uci())
                ConsoleView.show_message(f"✅ Coup joué: {move_san}")
            except Exception as e:
                err_str = str(e)
                if 'RemoteDisconnected' in err_str or 'Connection aborted' in err_str:
                    ConsoleView.show_message("⚠️ Problème de connexion, tentative de renvoi du coup...")
                    try:
                        self.client.board.make_move(self.game_id, move.uci())
                        ConsoleView.show_message(f"✅ Coup renvoyé: {move_san}")
                    except Exception as retry_e:
                        ConsoleView.show_message(f"⚠️ Échec renvoi du coup: {retry_e}")
                else:
                    ConsoleView.show_message(f"⚠️ Erreur lors de l'envoi du coup: {e}")

    # Pas de code direct sous play, main s'en charge
