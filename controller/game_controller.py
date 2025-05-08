# controller/game_controller.py

import threading
import time
from model.game_model import GameModel
from services.lichess_service import LichessService
from utils.exception_handler import handle_api_move_error
from view.base_view import View

class GameController:
    """
    Contrôleur principal : orchestre le modèle, la vue, et le service Lichess.
    """
    def __init__(self, token: str, view: View):
        self.service = LichessService(token)
        self.view = view                  # ← ta vue abstraite
        self.model = GameModel()
        self.game_id = None
        self.game_url = None
        self.user_color = None
        self.last_move_count = 0
        self.lock = threading.Lock()

    def challenge(self, opponent="maia1", clock_limit=600, clock_increment=5):
        resp = self.service.create_challenge(opponent, clock_limit, clock_increment)
        url = resp.get("url")
        self.game_id = url.rsplit('/', 1)[-1]
        self.game_url = url
        self.view.show_message(f"📡 Défi lancé contre {opponent}")

    def wait_for_start(self):
        self.view.show_message("⏳ En attente du début de la partie…")
        for ev in self.service.stream_incoming_events():
            if ev.get("type") == "gameStart":
                self.user_color = ev['game']['color']
                self.view.show_message(f"✅ Partie démarrée ! ID={self.game_id}")
                self.view.show_message(f"🔗 Suivi: {self.game_url}")
                self.view.show_message(f"🟢 Tu joues {self.user_color.upper()}.")
                break

    def listen_moves(self):
        for ev in self.service.stream_game_state(self.game_id):
            if ev['type'] not in ("gameFull", "gameState"):
                continue

            moves = (ev.get('state', {}).get('moves', '').split()
                     if ev['type'] == "gameFull"
                     else ev.get('moves', '').split())

            if len(moves) == self.last_move_count:
                continue
            self.last_move_count = len(moves)

            with self.lock:
                self.model.apply_moves(moves)

            self.view.show_message("\n🔄 Plateau mis à jour :")
            with self.lock:
                self.view.render_board(self.model.board)

    def play(self):
        threading.Thread(target=self.listen_moves, daemon=True).start()
        self.view.show_message(
            "🎮 À toi de jouer ! (SAN ex: e4, Nf3) — tape 'resign' pour abandonner"
        )

        while not self.model.is_game_over():
            if not self.is_user_turn():
                time.sleep(0.5)
                continue

            move_san = self.prompt_user_move()
            if move_san is None:
                break

            move = self.validate_move(move_san)
            if not move:
                continue

            self.send_move_to_lichess(move, move_san)

        self.view.show_message(f"🏁 Partie terminée: {self.model.result()}")

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

        def send_move_to_lichess(self, move, move_san):
        try:
            self.service.make_move(self.game_id, move.uci())
            self.view.show_message(f"✅ Coup joué: {move_san}")
        except Exception as e:
            self.view.show_message(f"❌ Impossible de jouer {move_san} après plusieurs essais : {e}")
