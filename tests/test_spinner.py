"""Tests for the Spinner component."""

from snaptui.components.spinner import Spinner, SpinnerTickMsg, SPINNER_DOTS, SPINNER_LINE


class TestSpinner:
    def test_initial_view(self):
        s = Spinner()
        assert s.view() == SPINNER_DOTS[0]

    def test_tick_advances_frame(self):
        s = Spinner()
        s, cmd = s.update(SpinnerTickMsg())
        assert s.frame == 1
        assert s.view() == SPINNER_DOTS[1]

    def test_wraps_around(self):
        s = Spinner(frame=len(SPINNER_DOTS) - 1)
        s, cmd = s.update(SpinnerTickMsg())
        assert s.frame == 0

    def test_tick_returns_cmd(self):
        s = Spinner()
        s, cmd = s.update(SpinnerTickMsg())
        assert cmd is not None

    def test_custom_frames(self):
        s = Spinner(frames=list(SPINNER_LINE))
        assert s.view() == "|"
        s, _ = s.update(SpinnerTickMsg())
        assert s.view() == "/"

    def test_ignores_wrong_tag(self):
        s = Spinner(tag=1)
        s, cmd = s.update(SpinnerTickMsg(tag=2))
        assert s.frame == 0
        assert cmd is None

    def test_matches_tag(self):
        s = Spinner(tag=42)
        s, cmd = s.update(SpinnerTickMsg(tag=42))
        assert s.frame == 1

    def test_empty_frames(self):
        s = Spinner(frames=[])
        assert s.view() == ""
