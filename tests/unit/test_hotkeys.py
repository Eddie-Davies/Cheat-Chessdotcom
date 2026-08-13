"""Phase 18 global hotkey and visibility controller tests."""

from chess_analyser.overlay import (
	GlobalHotkeyService,
	HotkeyBackend,
	HotkeyError,
	OverlayVisibilityController,
)


class FakeBackend(HotkeyBackend):
	def __init__(self, error=None):
		self.error = error
		self.callback = None
		self.started = False
		self.stopped = False

	def start(self, key, callback):
		if self.error:
			raise self.error
		self.callback = callback
		self.started = True

	def stop(self):
		self.stopped = True


class FakeOverlay:
	def __init__(self):
		self.visible = False
		self.actions = []

	def show(self):
		self.visible = True
		self.actions.append("show")

	def hide(self):
		self.visible = False
		self.actions.append("hide")


def test_default_f8_registers_and_callback_toggles_visibility():
	backend = FakeBackend()
	service = GlobalHotkeyService(backend=backend)
	overlay = FakeOverlay()
	controller = OverlayVisibilityController(overlay)

	status = service.start(controller.toggle)
	backend.callback()
	backend.callback()
	service.stop()

	assert status.registered
	assert backend.started
	assert backend.stopped
	assert overlay.actions == ["show", "hide"]


def test_hotkey_registration_failure_is_reported_without_crashing():
	service = GlobalHotkeyService(backend=FakeBackend(HotkeyError("permission denied")))

	status = service.start(lambda: None)

	assert not status.registered
	assert "permission denied" in status.message


def test_visibility_controller_uses_dispatcher_for_thread_safe_ui_updates():
	overlay = FakeOverlay()
	pending = []
	controller = OverlayVisibilityController(overlay, dispatch=pending.append)

	controller.toggle()
	assert overlay.actions == []
	pending.pop(0)()
	assert overlay.actions == ["show"]
