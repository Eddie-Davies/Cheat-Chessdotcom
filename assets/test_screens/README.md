# Screenshot Testing Policy

The near-term real-screen testing target is the green Chess.com board theme
used during play.

Use these fixture folders for new screenshot regression tests:

- `chesscom_standard_start/`
- `chesscom_green_active_game/`

New green-board screenshots should be placed in their own descriptive folder
with the raw source and all annotations beside it:

```text
source.png
board_detection.png
square_labels_white_bottom.png
occupancy.png
piece_recognition.png
```

Wood and brown fixtures remain useful failure cases, but they are not part of
the active acceptance target yet. Their piece templates and board geometry
need improvement before they should be used as success criteria.

Synthetic light/dark images may continue to be used for isolated algorithm
unit tests; real screenshot regression tests must use green-board fixtures.

Fast active-board regression command:

```text
venv\Scripts\python.exe -m pytest -m standard_screen
```

This targets the standard green starting-board screenshot and avoids the
broader full-suite run when only the active board needs checking.