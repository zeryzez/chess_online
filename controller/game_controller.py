# controller/game_controller.py

import threading
import time
from model.game_model import GameModel
from services.lichess_service import LichessService
from view.base_view import View
from utils.exception_handler import handle_api_move_error

class GameController:
    """
    Contrôleur principal : orchestre le modèle, la vue, et le service Lichess.
    """
    def __init__(self, token: str, view: View):
        # Service API Lichess avec retry/back-off
        self.service = LichessService(token)
        self.view = view
        self.model = GameModel()

        self.game_id = None
        self.game_url = None
        self.user_color = None
        self.last_move_count = 0

        # Synchronisation threads
        self.lock = threading.Lock()
        self.opponent_moved = threading.Event()

    def challenge_bot(self, level=1, clock_limit=600, clock_increment=5):
        """
        Lance un défi rapide contre un bot.
        """
        try:
            resp = self.service.challenge_bot(
                level, clock_limit, clock_increment
            )
            
            self.game_id, self.game_url = self.service.extract_game_info(resp)
            self.view.show_message(f"🤖 Défi bot lancé → {self.game_url}")
        except Exception as e:
            self.view.show_message(f"❌ Erreur défi bot : {e}")

    def challenge_user(self, username: str, clock_limit=600, clock_increment=5, rated=True):
        """
        Lance un défi rapide contre un utilisateur.
        """
        try:
            resp = self.service.challenge_user(
                username, clock_limit, clock_increment, rated
            )
            id, self.game_url = self.service.extract_game_info(resp)
            self.view.show_message(f"👤 Défi utilisateur lancé → {self.game_url}")
        except Exception as e:
            self.view.show_message(f"❌ Erreur défi utilisateur : {e}")

    def open_seek(self, clock_limit=600, clock_increment=5, rated=True, variant="standard"):
        """
        Ouvre un seek public (matchmaking) en partie rapide.
        """

        try:
            resp = self.service.create_seek(
                clock_limit, clock_increment, rated, variant
            )
            self.game_id, self.game_url = self.service.extract_game_info(resp)
            self.view.show_message(f"🔍 Seek ouvert → {self.game_url}")
        except Exception as e:
            self.view.show_message(f"❌ Erreur open seek : {e}")

    def wait_for_start(self):
        """
        Attend gameStart ou échec du défi.
        """
        self.view.show_message("⏳ En attente du début de la partie…")
        for ev in self.service.stream_incoming_events():
            ev_type = ev.get("type")
            if ev_type == "challengeCreated":
                self.view.show_message("ℹ️ Défi enregistré, en attente...")
            elif ev_type == "gameStart":
                real_game_id = ev["game"]["id"]
                self.user_color = self.get_player_color_from_event(ev, "zeryzez")
                self.view.show_message(f"✅ Partie démarrée ! ID={self.game_id}")
                self.view.show_message(f"🟢 Tu joues {self.user_color.upper()}.")
                return True
            elif ev_type in ("challengeDeclined", "challengeCanceled", "challengeExpired"):
                self.view.show_message("❌ Le défi n'a pas été accepté.")
                return False
            elif ev_type.startswith("challenge"):
                self.view.show_message(f"🔔 Événement défi : {ev_type}")
        self.view.show_message("⚠️ Flux terminé sans démarrage.")
        return False

    def listen_moves(self):
        """
        Thread d'écoute pour synchroniser le modèle.
        """
        for ev in self.service.stream_game_state(self.game_id):
            if ev.get('type') not in ("gameFull", "gameState"):
                continue
            if ev['type'] == 'gameFull':
                moves = ev['state'].get('moves', '').split()
            else:
                moves = ev.get('moves', '').split()

            if len(moves) == self.last_move_count:
                continue
            self.last_move_count = len(moves)

            with self.lock:
                self.model.apply_moves(moves)

            self.view.show_message("\n🔄 Plateau mis à jour :")
            with self.lock:
                self.view.render_board(self.model.board)

            if self.is_user_turn():
                self.opponent_moved.set()

    def play(self):
        """
        Boucle de jeu principale.
        """
        threading.Thread(target=self.listen_moves, daemon=True).start()
        self.view.show_message(
            "🎮 À toi de jouer ! (SAN ex: e4, Nf3) — tape 'resign' pour abandonner"
        )

        while not self.model.is_game_over():
            if not self.is_user_turn():
                self.view.show_message("⏳ En attente du coup de l'adversaire…")
                self.opponent_moved.wait()
                self.opponent_moved.clear()
                continue

            move_san = self.prompt_user_move()
            if move_san is None:
                break

            move = self.validate_move(move_san)
            if not move:
                continue

            self.send_move_to_lichess(move, move_san)

        self.view.show_message(f"🏁 Partie terminée: {self.model.result()}")

    # ---- Helpers ----

    def is_user_turn(self) -> bool:
        with self.lock:
            return self.model.board.turn == (self.user_color == 'white')

    def prompt_user_move(self):
        move_san = self.view.prompt_move()
        if move_san.lower() == 'resign':
            self.service.resign(self.game_id)
            self.view.show_message("🏳️ Tu as abandonné.")
            return None
        return move_san

    def validate_move(self, move_san):
        try:
            with self.lock:
                move = self.model.parse_san(move_san)
                if not self.model.is_legal(move):
                    raise ValueError("Coup illégal")
                return move
        except ValueError as ve:
            self.view.show_message(f"⚠️ {ve}")
            return None

    def send_move_to_lichess(self, move, move_san: str):
        try:
            self.service.make_move(self.game_id, move.uci())
            self.view.show_message(f"✅ Coup joué: {move_san}")
        except Exception as e:
            handle_api_move_error(e, lambda: self.service.make_move(self.game_id, move.uci()))

    def get_player_color_from_event(self,ev: dict, username: str) -> str | None:
        username = username.lower()
        game_data = self.service.client.games.export(self.game_id)

        for color in ("white", "black"):
            player = game_data.get("players", {}).get(color, {})
            user = player.get("user")
            if user and user.get("id", "").lower() == username:
                return color
        return None

