from copy import deepcopy
from time import perf_counter


class SudokuSolver:
    """Baseline row-major backtracking Sudoku solver."""

    name = "Backtracking"

    def __init__(self, board):
        self.board = board
        self.nodes_visited = 0

    def is_valid(self, row, col, num):
        for j in range(9):
            if self.board[row][j] == num:
                return False

        for i in range(9):
            if self.board[i][col] == num:
                return False

        start_row = (row // 3) * 3
        start_col = (col // 3) * 3

        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if self.board[i][j] == num:
                    return False

        return True

    def find_empty(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return i, j
        return None

    def solve(self):
        empty = self.find_empty()

        if not empty:
            return True

        row, col = empty
        self.nodes_visited += 1

        for num in range(1, 10):
            if self.is_valid(row, col, num):
                self.board[row][col] = num

                if self.solve():
                    return True

                self.board[row][col] = 0

        return False

    def validate_board(self):
        for row in range(9):
            nums = [x for x in self.board[row] if x != 0]
            if len(nums) != len(set(nums)):
                return False

        for col in range(9):
            nums = []
            for row in range(9):
                if self.board[row][col] != 0:
                    nums.append(self.board[row][col])

            if len(nums) != len(set(nums)):
                return False

        for box_row in range(0, 9, 3):
            for box_col in range(0, 9, 3):
                nums = []

                for i in range(box_row, box_row + 3):
                    for j in range(box_col, box_col + 3):
                        if self.board[i][j] != 0:
                            nums.append(self.board[i][j])

                if len(nums) != len(set(nums)):
                    return False

        return True

    def print_board(self):
        for row in self.board:
            print(row)


class MRVSudokuSolver(SudokuSolver):
    """Backtracking solver using the minimum remaining value heuristic."""

    name = "Minimum Remaining Value"

    def get_candidates(self, row, col):
        candidates = []

        for num in range(1, 10):
            if self.is_valid(row, col, num):
                candidates.append(num)

        return candidates

    def find_mrv_empty(self):
        best_cell = None
        best_candidates = None

        for row in range(9):
            for col in range(9):
                if self.board[row][col] == 0:
                    candidates = self.get_candidates(row, col)

                    if not candidates:
                        return (row, col), []

                    if best_candidates is None or len(candidates) < len(best_candidates):
                        best_cell = (row, col)
                        best_candidates = candidates

        return best_cell, best_candidates

    def solve(self):
        empty, candidates = self.find_mrv_empty()

        if empty is None:
            return True

        row, col = empty
        self.nodes_visited += 1

        for num in candidates:
            self.board[row][col] = num

            if self.solve():
                return True

            self.board[row][col] = 0

        return False


class DancingLinksSudokuSolver(SudokuSolver):
    """Sudoku solver using Algorithm X with dancing-links-style cover/uncover."""

    name = "Dancing Links"

    def __init__(self, board):
        super().__init__(board)
        self._solution_rows = []

    def _constraint_names(self, row, col, num):
        box = (row // 3) * 3 + (col // 3)

        return (
            ("cell", row, col),
            ("row", row, num),
            ("column", col, num),
            ("box", box, num),
        )

    def _build_exact_cover(self):
        columns = {}
        rows = {}

        for row in range(9):
            for col in range(9):
                value = self.board[row][col]
                nums = [value] if value != 0 else range(1, 10)

                for num in nums:
                    row_id = (row, col, num)
                    constraints = self._constraint_names(row, col, num)
                    rows[row_id] = constraints

                    for constraint in constraints:
                        columns.setdefault(constraint, set()).add(row_id)

        return columns, rows

    def _cover(self, columns, rows, row_id):
        removed_columns = []

        for constraint in rows[row_id]:
            column_rows = columns.pop(constraint, set())
            removed_columns.append((constraint, column_rows))

            for other_row_id in column_rows:
                for other_constraint in rows[other_row_id]:
                    if other_constraint != constraint and other_constraint in columns:
                        columns[other_constraint].discard(other_row_id)

        return removed_columns

    def _uncover(self, columns, rows, removed_columns):
        for constraint, column_rows in reversed(removed_columns):
            columns[constraint] = column_rows

            for other_row_id in column_rows:
                for other_constraint in rows[other_row_id]:
                    if other_constraint != constraint and other_constraint in columns:
                        columns[other_constraint].add(other_row_id)

    def _search(self, columns, rows, solution):
        if not columns:
            self._solution_rows = solution[:]
            return True

        constraint = min(columns, key=lambda key: len(columns[key]))

        if len(columns[constraint]) == 0:
            return False

        self.nodes_visited += 1

        for row_id in list(columns[constraint]):
            solution.append(row_id)
            removed_columns = self._cover(columns, rows, row_id)

            if self._search(columns, rows, solution):
                return True

            self._uncover(columns, rows, removed_columns)
            solution.pop()

        return False

    def solve(self):
        if not self.validate_board():
            return False

        columns, rows = self._build_exact_cover()

        if not self._search(columns, rows, []):
            return False

        for row, col, num in self._solution_rows:
            self.board[row][col] = num

        return True


def compare_solvers(board, solver_classes=None):
    if solver_classes is None:
        solver_classes = [
            SudokuSolver,
            MRVSudokuSolver,
            DancingLinksSudokuSolver,
        ]

    results = []

    for solver_class in solver_classes:
        test_board = deepcopy(board)
        solver = solver_class(test_board)
        start = perf_counter()
        solved = solver.validate_board() and solver.solve()
        elapsed = perf_counter() - start

        results.append({
            "algorithm": solver.name,
            "solved": solved,
            "time_seconds": elapsed,
            "nodes_visited": solver.nodes_visited,
            "board": solver.board,
        })

    return results


def print_comparison(results):
    print(f"{'Algorithm':<26} {'Solved':<8} {'Time (s)':<12} {'Nodes'}")
    print("-" * 55)

    for result in results:
        print(
            f"{result['algorithm']:<26} "
            f"{str(result['solved']):<8} "
            f"{result['time_seconds']:<12.6f} "
            f"{result['nodes_visited']}"
        )


board1 = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]

board2 = [
    [9, 0, 0, 5, 0, 8, 0, 0, 7],
    [0, 8, 0, 3, 0, 2, 9, 0, 5],
    [0, 5, 4, 0, 0, 0, 0, 8, 0],
    [0, 7, 0, 6, 8, 0, 0, 3, 2],
    [1, 0, 0, 0, 0, 4, 0, 0, 8],
    [5, 0, 0, 2, 1, 9, 0, 6, 0],
    [0, 0, 0, 9, 0, 6, 0, 0, 1],
    [7, 2, 6, 0, 0, 1, 0, 4, 0],
    [0, 0, 1, 4, 7, 0, 0, 5, 6]
]

board3 = [
    [0, 4, 1, 0, 0, 9, 0, 3, 0],
    [0, 0, 3, 0, 2, 0, 0, 8, 5],
    [0, 5, 0, 7, 3, 4, 9, 0, 0],
    [0, 0, 0, 0, 0, 5, 3, 0, 0],
    [0, 6, 0, 3, 0, 7, 0, 4, 0],
    [0, 0, 7, 6, 0, 0, 0, 0, 0],
    [0, 0, 9, 5, 8, 2, 0, 6, 0],
    [6, 3, 0, 0, 7, 0, 5, 0, 0],
    [0, 2, 0, 4, 0, 0, 7, 9, 0]
]


if __name__ == "__main__":
    for index, board in enumerate([board1, board2, board3], start=1):
        print(f"\nBoard {index}")
        print_comparison(compare_solvers(board))
