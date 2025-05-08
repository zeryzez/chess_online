# view/base_view.py
from abc import ABC, abstractmethod

class View(ABC):
    @abstractmethod
    def render_board(self, board):
        """Affiche le plateau (quel que soit le média)."""
        pass

    @abstractmethod
    def prompt_move(self) -> str:
        """Demande à l'utilisateur de saisir un coup et renvoie la SAN."""
        pass

    @abstractmethod
    def show_message(self, message: str):
        """Affiche un message à l'utilisateur."""
        pass
