# view/console_view.py
from .base_view import View

class ConsoleView(View):
    def render_board(self, board):
        """Affiche le plateau en ASCII avec bordures."""
        print(board.unicode(borders=True))

    def prompt_move(self) -> str:
        """Invite l'utilisateur à entrer un coup en SAN."""
        return input("🔸 Ton coup : ").strip()

    def show_message(self, message: str):
        """Affiche un message quelconque à l'utilisateur."""
        print(message)
