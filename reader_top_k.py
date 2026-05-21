import cv2
import numpy as np
from tensorflow.keras.models import load_model


MODEL_PATH = "mnist_digit_model.h5"
IMAGE_PATH = "img/sudoku1.png"
TOP_K = 3


def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype=np.float32)

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def preprocess(image_path, size=450):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    sudoku_contour = None

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            sudoku_contour = approx
            break

    if sudoku_contour is None:
        raise ValueError("Could not find Sudoku grid contour.")

    src = order_points(sudoku_contour)

    dst = np.array([
        [0, 0],
        [size - 1, 0],
        [size - 1, size - 1],
        [0, size - 1]
    ], dtype=np.float32)

    transform = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(gray, transform, (size, size))

    cell_size = size // 9
    cells = []

    for row in range(9):
        row_cells = []

        for col in range(9):
            y1 = row * cell_size
            y2 = (row + 1) * cell_size
            x1 = col * cell_size
            x2 = (col + 1) * cell_size

            cell = warped[y1:y2, x1:x2]
            row_cells.append(cell)

        cells.append(row_cells)

    return warped, cells


def center_digit(digit):
    h, w = digit.shape

    size = max(h, w)
    canvas = np.zeros((size, size), dtype=np.uint8)

    y = (size - h) // 2
    x = (size - w) // 2

    canvas[y:y + h, x:x + w] = digit

    canvas = cv2.resize(canvas, (20, 20))

    final = np.zeros((28, 28), dtype=np.uint8)
    final[4:24, 4:24] = canvas

    return final


def extract_digit(cell):
    cell = cv2.resize(cell, (50, 50))

    thresh = cv2.adaptiveThreshold(
        cell,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    margin = 7
    thresh[:margin, :] = 0
    thresh[-margin:, :] = 0
    thresh[:, :margin] = 0
    thresh[:, -margin:] = 0

    nonzero = cv2.countNonZero(thresh)

    if nonzero < 50:
        return None

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(largest)

    if w * h < 100:
        return None

    digit = thresh[y:y + h, x:x + w]
    digit = center_digit(digit)

    return digit


def classify_digit_top_k(digit_img, model, k=3):
    if digit_img is None:
        return [(0, 1.0)]

    img = digit_img.astype("float32") / 255.0
    img = img.reshape(1, 28, 28, 1)

    probs = model.predict(img, verbose=0)[0]

    candidates = []

    for digit in range(1, 10):
        candidates.append((digit, float(probs[digit])))

    candidates.sort(key=lambda x: x[1], reverse=True)

    return candidates[:k]


def build_candidate_board(image_path, model, k=3):
    _, cells = preprocess(image_path)

    candidate_board = [[[] for _ in range(9)] for _ in range(9)]

    for row in range(9):
        for col in range(9):
            digit_img = extract_digit(cells[row][col])
            candidate_board[row][col] = classify_digit_top_k(digit_img, model, k)

    return candidate_board


def is_valid(board, row, col, digit):
    for c in range(9):
        if board[row][c] == digit:
            return False

    for r in range(9):
        if board[r][col] == digit:
            return False

    box_row = (row // 3) * 3
    box_col = (col // 3) * 3

    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == digit:
                return False

    return True


def sudoku_rule_selection(candidate_board):
    board = [[0 for _ in range(9)] for _ in range(9)]

    filled_cells = []

    for row in range(9):
        for col in range(9):
            candidates = candidate_board[row][col]

            if candidates[0][0] == 0:
                board[row][col] = 0
            else:
                filled_cells.append((row, col, candidates))

    # Higher confidence cells are assigned earlier.
    filled_cells.sort(key=lambda item: item[2][0][1], reverse=True)

    best_board = None
    best_score = -1

    def backtrack(index, score):
        nonlocal best_board, best_score

        if index == len(filled_cells):
            if score > best_score:
                best_score = score
                best_board = [r[:] for r in board]
            return

        row, col, candidates = filled_cells[index]

        for digit, confidence in candidates:
            if is_valid(board, row, col, digit):
                board[row][col] = digit
                backtrack(index + 1, score + confidence)
                board[row][col] = 0

    backtrack(0, 0)

    return best_board


def image_to_sudoku_matrix_top_k(image_path, model_path=MODEL_PATH, k=TOP_K):
    model = load_model(model_path)

    candidate_board = build_candidate_board(image_path, model, k)

    final_board = sudoku_rule_selection(candidate_board)

    if final_board is None:
        print("No valid board found. Try increasing TOP_K.")
        return None

    return np.array(final_board)


def print_candidate_board(candidate_board):
    for row in range(9):
        for col in range(9):
            print(f"Cell ({row}, {col}): {candidate_board[row][col]}")


def print_board(board):
    if board is None:
        print("No board found.")
        return

    for row in board:
        print(row.tolist())


if __name__ == "__main__":
    board = image_to_sudoku_matrix_top_k(
        IMAGE_PATH,
        MODEL_PATH,
        TOP_K
    )

    print("Final matrix after top-k + Sudoku rule selection:")
    print_board(board)