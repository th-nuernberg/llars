"""
Unit tests for the "scenario access granted" live push.

Code under test:
    app/socketio_handlers/events_scenarios.py -> emit_scenario_access_granted

When someone grants a user access to a scenario, the backend pushes the card to
that user's personal invite room so the Evaluation hub can surface it live. A
rater sitting on the hub previously had no idea a study had been shared with
them until they reloaded.

Two properties matter and are locked in here:

1. The push goes to a room derived from the recipient's *username*. The room
   name is never taken from client input (the socket handler derives it from the
   authenticated identity), so one user can never receive another's invitations.
2. It is best-effort. The invite has already been committed by the time this
   runs — a socket failure must not propagate and fail the HTTP request.

Test IDs: [SCNOTIFY-001] through [SCNOTIFY-006]
"""

import pytest


class _RecordingSocketIO:
    """Captures emit() calls; optionally blows up to test error isolation."""

    def __init__(self, explode=False):
        self.calls = []
        self.explode = explode

    def emit(self, event, payload, room=None):
        if self.explode:
            raise RuntimeError('socket layer down')
        self.calls.append({'event': event, 'payload': payload, 'room': room})


def _emit():
    from socketio_handlers.events_scenarios import emit_scenario_access_granted
    return emit_scenario_access_granted


SCENARIO = {'id': 869, 'scenario_name': 'Survey Screening — Konsens'}


class TestScenarioAccessNotification:

    def test_SCNOTIFY_001_emits_to_the_recipient_room(self):
        """[SCNOTIFY-001] One recipient -> one event in that user's room."""
        sio = _RecordingSocketIO()

        _emit()(sio, ['ieb-albrecht'], SCENARIO)

        assert len(sio.calls) == 1
        call = sio.calls[0]
        assert call['event'] == 'scenario:access_granted'
        assert call['payload'] == {'scenario': SCENARIO}
        assert 'ieb-albrecht' in call['room']

    def test_SCNOTIFY_002_room_is_per_user(self):
        """[SCNOTIFY-002] Each recipient gets their own room, never a shared one."""
        sio = _RecordingSocketIO()

        _emit()(sio, ['ieb-albrecht', 'ieb-steigerwald'], SCENARIO)

        rooms = [c['room'] for c in sio.calls]
        assert len(rooms) == 2
        assert len(set(rooms)) == 2
        assert all('scenario_invites_' in r for r in rooms)

    def test_SCNOTIFY_003_matches_the_subscribe_room_naming(self):
        """[SCNOTIFY-003] Emit room == the room the socket handler joins.

        If these two drift apart the push silently goes nowhere, which is
        exactly the kind of bug that only shows up in production.
        """
        from socketio_handlers.events_scenarios import _invite_room

        sio = _RecordingSocketIO()
        _emit()(sio, ['someone'], SCENARIO)

        assert sio.calls[0]['room'] == _invite_room('someone')

    def test_SCNOTIFY_004_no_recipients_is_a_noop(self):
        """[SCNOTIFY-004] Empty/None recipient list emits nothing."""
        sio = _RecordingSocketIO()

        _emit()(sio, [], SCENARIO)
        _emit()(sio, None, SCENARIO)
        _emit()(sio, ['x'], None)

        assert sio.calls == []

    def test_SCNOTIFY_005_skips_blank_usernames(self):
        """[SCNOTIFY-005] Falsy usernames are skipped, valid ones still sent."""
        sio = _RecordingSocketIO()

        _emit()(sio, ['', None, 'real-user'], SCENARIO)

        assert len(sio.calls) == 1
        assert 'real-user' in sio.calls[0]['room']

    def test_SCNOTIFY_006_socket_failure_is_swallowed(self):
        """[SCNOTIFY-006] A broken socket must not raise.

        The membership is already committed; failing here would turn a
        successful invite into an HTTP 500 for the person doing the inviting.
        """
        sio = _RecordingSocketIO(explode=True)

        # Must not raise.
        _emit()(sio, ['ieb-albrecht'], SCENARIO)
