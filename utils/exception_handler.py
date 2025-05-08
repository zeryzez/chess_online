# utils/exception_handler.py

from view.console_view import ConsoleView
import time

def handle_api_move_error(error, retry_function):
    """
    Gère les erreurs liées à l'envoi d'un coup à l'API Lichess,
    avec tentative de renvoi automatique si pertinent.
    """
    err_str = str(error)
    if 'RemoteDisconnected' in err_str or 'Connection aborted' in err_str:
        ConsoleView.show_message("⚠️ Problème de connexion, tentative de renvoi du coup...")
        time.sleep(1)
        try:
            retry_function()
            ConsoleView.show_message("✅ Coup renvoyé avec succès.")
        except Exception as retry_e:
            ConsoleView.show_message(f"⚠️ Échec renvoi du coup: {retry_e}")
    else:
        ConsoleView.show_message(f"⚠️ Erreur lors de l'envoi du coup: {error}")