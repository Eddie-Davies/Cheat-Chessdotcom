"""Cross-platform global hotkey service and overlay visibility controller."""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class HotkeyError(RuntimeError):
	"""Base error for global hotkey registration and lifecycle failures."""


class HotkeyUnavailableError(HotkeyError):
	"""Raised when the optional global-hotkey backend is unavailable."""


class HotkeyPermissionError(HotkeyError):
	"""Raised when the operating system denies global keyboard access."""


@dataclass(frozen=True)
class HotkeyStatus:
	"""Registration status suitable for displaying in a control UI."""

	registered: bool
	key: str
	message: str


class HotkeyBackend(ABC):
	"""Replaceable backend interface for platform-specific global hooks."""

	@abstractmethod
	def start(self, key: str, callback: Callable[[], None]) -> None:
		"""Register a global key and begin listening."""

	@abstractmethod
	def stop(self) -> None:
		"""Stop listening and unregister the key."""


class PynputHotkeyBackend(HotkeyBackend):
	"""Optional pynput implementation for Windows, macOS, and Linux."""

	def __init__(self) -> None:
		self._listener: Any | None = None

	def start(self, key: str, callback: Callable[[], None]) -> None:
		try:
			from pynput import keyboard
		except ImportError as exc:
			raise HotkeyUnavailableError(
				"Global hotkeys require the optional 'pynput' package"
			) from exc
		try:
			key_name = key.strip().lower()
			if not key_name.startswith("f") or not key_name[1:].isdigit():
				raise ValueError(f"Unsupported hotkey format: {key}")
			getattr(keyboard.Key, key_name)
			self._listener = keyboard.GlobalHotKeys({f"<{key_name}>": callback})
			self._listener.start()
		except PermissionError as exc:
			raise HotkeyPermissionError(
				"Operating system denied global keyboard access; grant accessibility/keyboard permission"
			) from exc
		except (OSError, RuntimeError, ValueError, AttributeError) as exc:
			raise HotkeyError(f"Unable to register global hotkey {key}: {exc}") from exc

	def stop(self) -> None:
		if self._listener is None:
			return
		self._listener.stop()
		self._listener = None


class GlobalHotkeyService:
	"""Manage one configurable global hotkey without knowing overlay details."""

	def __init__(
		self,
		*,
		key: str = "f8",
		backend: HotkeyBackend | None = None,
		logger: logging.Logger | None = None,
	) -> None:
		self.key = key.lower().strip()
		self.backend = backend or PynputHotkeyBackend()
		self.logger = logger or logging.getLogger(__name__)
		self._registered = False

	@property
	def registered(self) -> bool:
		return self._registered

	def start(self, callback: Callable[[], None]) -> HotkeyStatus:
		if self._registered:
			return HotkeyStatus(True, self.key, "Global hotkey already registered")
		try:
			self.backend.start(self.key, callback)
		except HotkeyError as exc:
			self.logger.warning("Global hotkey registration failed: %s", exc)
			return HotkeyStatus(False, self.key, str(exc))
		self._registered = True
		self.logger.info("Global hotkey registered: %s", self.key)
		return HotkeyStatus(True, self.key, "Global hotkey registered")

	def stop(self) -> None:
		if not self._registered:
			return
		self.backend.stop()
		self._registered = False


class OverlayVisibilityController:
	"""Toggle an overlay through a safe UI dispatcher from a hotkey callback."""

	def __init__(self, overlay: Any, *, dispatch: Callable[[Callable[[], None]], None] | None = None) -> None:
		self.overlay = overlay
		self.dispatch = dispatch or (lambda callback: callback())

	def toggle(self) -> None:
		self.dispatch(self._toggle_on_ui_thread)

	def _toggle_on_ui_thread(self) -> None:
		if getattr(self.overlay, "visible", False):
			self.overlay.hide()
		else:
			self.overlay.show()