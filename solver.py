class SudokuSolver:
    def __init__(self, board):
        self.board = board

    def is_valid(self, row, col, num):
        # Check row
        for j in range(9):
            if self.board[row][j] == num:
                return False

        # Check column
        for i in range(9):
            if self.board[i][col] == num:
                return False

        # Check 3x3 sub-box
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

        # Puzzle solved
        if not empty:
            return True

        row, col = empty

        # Try digits 1-9
        for num in range(1, 10):
            if self.is_valid(row, col, num):
                self.board[row][col] = num

                # Recursive backtracking
                if self.solve():
                    return True

                # Backtrack
                self.board[row][col] = 0

        return False

    def validate_board(self):
        # Validate rows
        for row in range(9):
            nums = [x for x in self.board[row] if x != 0]
            if len(nums) != len(set(nums)):
                return False

        # Validate columns
        for col in range(9):
            nums = []
            for row in range(9):
                if self.board[row][col] != 0:
                    nums.append(self.board[row][col])

            if len(nums) != len(set(nums)):
                return False

        # Validate 3x3 sub-boxes
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
            print("\n")


# Example input
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

solver1 = SudokuSolver(board1)
solver2 = SudokuSolver(board2)
solver3 = SudokuSolver(board3)

# Validate input puzzle first
if solver1.validate_board():
    print("Initial board is valid.\n")

    if solver1.solve():
        print("Solved Sudoku:\n")
        solver1.print_board()
    else:
        print("No solution exists.")
else:
    print("Invalid Sudoku puzzle.")

if solver2.validate_board():
    print("Initial board is valid.\n")

    if solver2.solve():
        print("Solved Sudoku:\n")
        solver2.print_board()
    else:
        print("No solution exists.")
else:
    print("Invalid Sudoku puzzle.")
if solver3.validate_board():
    print("Initial board is valid.\n")

    if solver3.solve():
        print("Solved Sudoku:\n")
        solver3.print_board()
    else:
        print("No solution exists.")
else:
    print("Invalid Sudoku puzzle.")