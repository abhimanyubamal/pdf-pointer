from PyQt5.QtCore import Qt


class KeyboardController:
    def __init__(self, viewer):
        self.viewer = viewer
        self.chars = viewer.characters

        # Build ordered lines: [(page, line_y, [char_indices])]
        self.lines = self._build_lines(self.chars)

    def _build_lines(self, characters):
        line_map = {}

        for i, ch in enumerate(characters):
            key = (ch["page"], ch["line_y"])
            line_map.setdefault(key, []).append(i)

        # Sort by page, then vertical position
        sorted_lines = sorted(
            [(page, line_y, indices) for (page, line_y), indices in line_map.items()],
            key=lambda x: (x[0], x[1])
        )

        return sorted_lines

    def handle_key(self, event):
        idx = self.viewer.cursor_index
        current = self.chars[idx]

        # --------------------
        # Horizontal movement
        # --------------------
        if event.key() == Qt.Key_Right:
            self.viewer.cursor_index = min(idx + 1, len(self.chars) - 1)
            self.viewer.update_finger()
            return

        if event.key() == Qt.Key_Left:
            self.viewer.cursor_index = max(idx - 1, 0)
            self.viewer.update_finger()
            return

        # --------------------
        # Vertical movement
        # --------------------
        if event.key() not in (Qt.Key_Up, Qt.Key_Down):
            return

        direction = -1 if event.key() == Qt.Key_Up else 1

        # Find current line index
        current_line_idx = None
        for i, (page, line_y, indices) in enumerate(self.lines):
            if idx in indices:
                current_line_idx = i
                break

        if current_line_idx is None:
            return

        target_line_idx = current_line_idx + direction

        # -----------------------------------
        # Case 1: Normal line-to-line movement
        # -----------------------------------
        if 0 <= target_line_idx < len(self.lines):
            target_page, _, target_indices = self.lines[target_line_idx]

            # If same page OR crossing page boundary, both are valid
            self._move_to_line(target_indices, current)
            return

        # -----------------------------------
        # Case 2: Page boundary (scroll)
        # -----------------------------------
        current_page = current["page"]
        next_page = current_page + direction

        if next_page < 0 or next_page > self.chars[-1]["page"]:
            return  # no more pages

        # Get first or last line of the target page
        page_lines = [
            line for line in self.lines if line[0] == next_page
        ]

        if not page_lines:
            return

        target_line = page_lines[0] if direction == 1 else page_lines[-1]
        _, _, target_indices = target_line

        self._move_to_line(target_indices, current)

    def _move_to_line(self, target_indices, current_char):
        """
        Move cursor to the glyph in target line
        whose X-center is closest to the current glyph.
        """
        current_x = (current_char["rect"].x0 + current_char["rect"].x1) / 2

        best_idx = min(
            target_indices,
            key=lambda i: abs(
                ((self.chars[i]["rect"].x0 + self.chars[i]["rect"].x1) / 2)
                - current_x
            )
        )

        self.viewer.cursor_index = best_idx
        self.viewer.update_finger()
