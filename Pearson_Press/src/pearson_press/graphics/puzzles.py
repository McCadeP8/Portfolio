"""A daily sudoku, generated from the edition date, with its answer printed upside down."""

from __future__ import annotations

import random
from datetime import date

from pearson_press.edition.blocks import Block
from pearson_press.graphics.charts import INK
from pearson_press.publication.fonts import face

Grid = list[list[int]]


def _candidates(grid: Grid, row: int, col: int) -> set[int]:
    box_r, box_c = row // 3 * 3, col // 3 * 3
    used = set(grid[row]) | {grid[r][col] for r in range(9)}
    used |= {grid[r][c] for r in range(box_r, box_r + 3) for c in range(box_c, box_c + 3)}
    return set(range(1, 10)) - used


def _solve(grid: Grid, rng: random.Random | None = None, limit: int = 1) -> int:
    """Count solutions up to ``limit``; with ``rng`` the first one found is left filled in."""

    best = None
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                options = _candidates(grid, r, c)
                if best is None or len(options) < len(best[2]):
                    best = (r, c, options)
    if best is None:
        return 1
    r, c, options = best
    order = list(options)
    if rng:
        rng.shuffle(order)
    found = 0
    for value in order:
        grid[r][c] = value
        found += _solve(grid, rng, limit - found)
        if found >= limit:
            if rng:
                return found
            break
    grid[r][c] = 0
    return found


def make_puzzle(seed: date, clues: int = 30) -> tuple[Grid, Grid]:
    rng = random.Random(seed.toordinal())
    solution: Grid = [[0] * 9 for _ in range(9)]
    _solve(solution, rng)
    puzzle = [row[:] for row in solution]
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)
    filled = 81
    for r, c in cells:
        if filled <= clues:
            break
        keep = puzzle[r][c]
        puzzle[r][c] = 0
        if _solve([row[:] for row in puzzle], limit=2) != 1:
            puzzle[r][c] = keep
        else:
            filled -= 1
    return puzzle, solution


def _grid(pdf, grid: Grid, x: float, top: float, size: float, font_size: float) -> None:
    cell = size / 9
    pdf.setStrokeGray(INK)
    for i in range(10):
        pdf.setLineWidth(1.0 if i % 3 == 0 else 0.3)
        pdf.line(x, top - i * cell, x + size, top - i * cell)
        pdf.line(x + i * cell, top, x + i * cell, top - size)
    pdf.setFillGray(INK)
    pdf.setFont("Times-Bold", font_size)
    for r in range(9):
        for c in range(9):
            if grid[r][c]:
                pdf.drawCentredString(x + (c + 0.5) * cell, top - (r + 0.5) * cell - font_size * 0.35,
                                      str(grid[r][c]))


def sudoku_block(edition_date: date) -> Block:
    puzzle, solution = make_puzzle(edition_date)

    def draw(pdf, x, top, width, s):
        left = x + 2.0
        usable = width - 4.0
        pdf.setFillGray(INK)
        pdf.setFont(face("PP-Narrow-Bold"), 6.2)
        pdf.drawString(left, top - 6.2, "SUDOKU")
        pdf.setFont(face("PP-Narrow"), 4.8)
        pdf.drawString(left, top - 12.5, "Fill the grid so every row, column and 3x3 box holds 1 through 9.")
        size = usable * (0.86 + 0.14 * s)
        grid_top = top - 17.0
        _grid(pdf, puzzle, left + (usable - size) / 2, grid_top, size, size / 9 * 0.62)
        # The answer, small and upside down, as newspapers print it.
        small = 46.0
        answer_top = grid_top - size - 6.0
        pdf.saveState()
        pdf.translate(left + usable, answer_top - small - 7.0)
        pdf.rotate(180)
        _grid(pdf, solution, 0, 0, small, 3.6)
        pdf.setFont(face("PP-Narrow"), 4.2)
        pdf.drawString(0, 3.0, "Today's answer")
        pdf.restoreState()
        return answer_top - small - 16.0

    return Block("sudoku", "graphic", 1, draw, 0.0, 0.0, 1.0, priority=20)
