# Piece Templates

Templates are organized by color and piece type:

```text
piece_templates/
├── white/
│   ├── pawn.png
│   ├── knight.png
│   ├── bishop.png
│   ├── rook.png
│   ├── queen.png
│   └── king.png
└── black/
    ├── pawn.png
    ├── knight.png
    ├── bishop.png
    ├── rook.png
    ├── queen.png
    └── king.png
```

The current PNGs are representative templates extracted from
`assets/test_screens/chess_com_board_01.png` using the same board geometry
used by the Phase 5 and Phase 8 tests. They target the observed Chess.com
piece set and are not universal templates for every site or theme.

`TemplatePieceDetector` normalizes square size and estimates/removes the
local square background before comparing silhouettes. Add multiple PNGs per
piece set in a future revision when broader theme coverage is required.
