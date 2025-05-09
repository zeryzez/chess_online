# tests/test_game_controller.py

import pytest
from controller.game_controller import GameController
from model.game_model import GameModel

# Vue factice pour capter les messages et le rendu du plateau
class DummyView:
    def __init__(self):
        self.messages = []
        self.board_rendered = False
        self._prompts = []

    def show_message(self, msg):
        self.messages.append(msg)

    def render_board(self, board):
        self.board_rendered = True

    def prompt_move(self):
        # Retourne le prochain élément de _prompts si défini, sinon 'e4'
        return self._prompts.pop(0) if self._prompts else 'e4'

# 1. Test de challenge_bot
class DummyServiceChallengeBot:
    def __init__(self):
        self.called = False

    def challenge_bot(self, opponent, clock_limit, clock_increment):
        self.called = True
        return {'url': 'https://lichess.org/abcd1234'}

    # stubs pour les autres méthodes utilisées
    def extract_game_info(self, resp):
        return resp['url'].rsplit('/',1)[-1], resp['url']

@pytest.fixture
def controller_bot():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    dummy = DummyServiceChallengeBot()
    # Remplace le service par notre Dummy
    ctrl.service = dummy
    # Lien extracteur sur le service
    ctrl.service.extract_game_info = dummy.extract_game_info
    return ctrl, view

def test_challenge_bot(controller_bot):
    ctrl, view = controller_bot
    ctrl.challenge_bot(opponent="maia1")
    assert ctrl.game_id == 'abcd1234'
    assert any("Défi bot lancé" in m for m in view.messages)

# 2. Test de wait_for_start
class DummyServiceStart:
    def __init__(self):
        pass
    def stream_incoming_events(self):
        yield {"type": "gameStart", "game": {"color": "white"}}

@pytest.fixture
def controller_start():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    dummy = DummyServiceStart()
    ctrl.service = dummy
    ctrl.game_id = 'abcd1234'
    ctrl.game_url = 'https://lichess.org/abcd1234'
    return ctrl, view

def test_wait_for_start(controller_start):
    ctrl, view = controller_start
    result = ctrl.wait_for_start()
    assert ctrl.user_color == 'white'
    assert any("Partie démarrée" in msg for msg in view.messages)
    # La méthode retourne True implicitement
    assert result is None or result is True

# 3. Test is_user_turn
def test_is_user_turn_white():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    ctrl.model.board.turn = True  # blanc au trait
    ctrl.user_color = 'white'
    assert ctrl.is_user_turn() is True

def test_is_user_turn_black():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    ctrl.model.board.turn = False  # noir au trait
    ctrl.user_color = 'black'
    assert ctrl.is_user_turn() is True

# 4. Test validate_move
def test_validate_move_legal():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    # Position après e4 pour que 'e4' soit légal
    ctrl.model.board.push_san('e4')
    move = ctrl.validate_move('e4')
    assert move is not None

def test_validate_move_illegal():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    move = ctrl.validate_move('e9')  # notation invalide
    assert move is None
    assert any("⚠️" in m for m in view.messages)

# 5. Test prompt_user_move resign
class DummyServiceResign:
    def __init__(self): self.resigned = False
    def resign(self, game_id): self.resigned = True

@pytest.fixture
def controller_resign():
    view = DummyView()
    view._prompts = ['resign']
    ctrl = GameController(token="dummy", view=view)
    dummy = DummyServiceResign()
    ctrl.service = dummy
    ctrl.game_id = 'gid'
    return ctrl, view, dummy

def test_prompt_user_move_resign(controller_resign):
    ctrl, view, svc = controller_resign
    result = ctrl.prompt_user_move()
    assert result is None
    assert svc.resigned is True
    assert any("abandon" in m for m in view.messages)

# 6. Test challenge_user
class DummyServiceChallengeUser:
    def __init__(self): self.called = False
    def challenge_user(self, username, clock_limit, clock_increment, rated):
        self.called = True
        return {'url': 'https://lichess.org/user123'}
    def extract_game_info(self, resp):
        return resp['url'].rsplit('/',1)[-1], resp['url']

@pytest.fixture
def controller_user():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    dummy = DummyServiceChallengeUser()
    ctrl.service = dummy
    ctrl.service.extract_game_info = dummy.extract_game_info
    return ctrl, view

def test_challenge_user(controller_user):
    ctrl, view = controller_user
    ctrl.challenge_user(username="testuser")
    assert ctrl.game_id == 'user123'
    assert any("Défi utilisateur" in m for m in view.messages)
    assert ctrl.service.called is True

# 7. Test open_seek
class DummyServiceSeek:
    def __init__(self): self.called = False
    def create_seek(self, clock_limit, clock_increment, rated, variant):
        self.called = True
        return {'url': 'https://lichess.org/seek456'}
    def extract_game_info(self, resp):
        return resp['url'].rsplit('/',1)[-1], resp['url']

@pytest.fixture
def controller_seek():
    view = DummyView()
    ctrl = GameController(token="dummy", view=view)
    dummy = DummyServiceSeek()
    ctrl.service = dummy
    ctrl.service.extract_game_info = dummy.extract_game_info
    return ctrl, view

def test_open_seek(controller_seek):
    ctrl, view = controller_seek
    ctrl.open_seek(clock_limit=300, clock_increment=2, rated=False)
    assert ctrl.game_id == 'seek456'
    assert any("Seek ouvert" in m for m in view.messages)
    assert ctrl.service.called is True
