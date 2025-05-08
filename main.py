# main.py
import os
from controller.game_controller import GameController
from config import LICHESS_TOKEN

def main():
    controller = GameController(LICHESS_TOKEN)
    
    try:
        # Défi contre un bot avec paramètres par défaut
        controller.challenge(
            opponent="maia1",  # Nom du bot
            clock_limit=600,    # 10 minutes
            clock_increment=5   # 5 secondes par coup
        )
        
        # Attente du début de partie
        controller.wait_for_start()
        
        # Lancement de la boucle de jeu principale
        controller.play()
    
    except Exception as e:
        print(f"⛔ ERREUR CRITIQUE : {str(e)}")
        print("🔌 Causes possibles :")
        print("- Problème de connexion Internet")
        print("- Token Lichess invalide/expiré")
        print("- Bug dans le code du bot")

if __name__ == "__main__":
    main()