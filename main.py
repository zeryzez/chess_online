# main.py

import os
from controller.game_controller import GameController
from view.console_view import ConsoleView  # Import de la vue console
from config import LICHESS_TOKEN


def main():
    # Initialisation de la vue et du contrôleur
    view = ConsoleView()
    controller = GameController(LICHESS_TOKEN, view)

    try:
        """
        controller.challenge_bot(
            1,  # Niveau du bot (1-8)
            clock_limit=600,    # 10 minutes
            clock_increment=5   # 5 secondes par coup
        )
        """
        """
        controller.challenge_user(
            username="maia1",  # Nom de l'utilisateur
            clock_limit=600,    # 10 minutes
            clock_increment=5   # 5 secondes par coup
        )
        """
        """
        controller.open_seek(
            clock_limit=600,    # 10 minutes
            clock_increment=5,  # 5 secondes par coup
            rated=False,         # Partie non classée
            variant="standard"  # Variante standard
        )
        """
        # Attente du début de partie
        controller.wait_for_start()

        # Lancement de la boucle de jeu principale
        controller.play()

    except Exception as e:
        view.show_message(f"⛔ ERREUR CRITIQUE : {str(e)}")
        view.show_message("🔌 Causes possibles :")
        view.show_message("- Problème de connexion Internet")
        view.show_message("- Token Lichess invalide/expiré")
        view.show_message("- Bug dans le code du bot")


if __name__ == "__main__":
    main()
