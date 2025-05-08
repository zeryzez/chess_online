#view/console_view.py

class ConsoleView:
    """
    Vue console pour l'affichage ASCII du plateau et la saisie des coups.
    """
    @staticmethod
    def render_board(board):
        """Affiche le plateau en ASCII avec bordures."""
        print(board.unicode(borders=True))

    @staticmethod
    def prompt_move():
        """Invite l'utilisateur à entrer un coup en SAN."""
        return input("🔸 Ton coup : ").strip()

    @staticmethod
    def show_message(message):
        """Affiche un message quelconque à l'utilisateur."""
        print(message)
