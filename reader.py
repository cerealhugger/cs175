import cv2
import numpy as np

MODEL_PATH = "mnist_digit_model.h5"
_model = None


def build_digit_model():
    from tensorflow.keras.layers import (
        BatchNormalization,
        Conv2D,
        Dense,
        Dropout,
        Flatten,
        Input,
        MaxPooling2D,
    )
    from tensorflow.keras.models import Sequential

    return Sequential([
        Input(shape=(28, 28, 1)),
        Conv2D(32, (3, 3), activation="relu"),
        BatchNormalization(),
        MaxPooling2D((2, 2)),

        Conv2D(64, (3, 3), activation="relu"),
        BatchNormalization(),
        MaxPooling2D((2, 2)),

        Conv2D(128, (3, 3), activation="relu"),
        BatchNormalization(),

        Flatten(),

        Dense(128, activation="relu"),
        Dropout(0.4),

        Dense(10, activation="softmax")
    ])


def get_model(model_path=MODEL_PATH):
    global _model

    if _model is None:
        from tensorflow.keras.models import load_model

        try:
            _model = load_model(model_path, compile=False)
        except Exception:
            _model = build_digit_model()
            _model.load_weights(model_path)

    return _model


def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype=np.float32)

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    rect[1] = pts[np.argmin(diff)]   # top-right
    rect[3] = pts[np.argmax(diff)]   # bottom-left

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
        raise ValueError("Could not find Sudoku grid.")

    src = order_points(sudoku_contour)

    dst = np.array([
        [0, 0],
        [size - 1, 0],
        [size - 1, size - 1],
        [0, size - 1]
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(gray, matrix, (size, size))

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

    # remove borders/grid lines
    margin = 5
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

    digit = cv2.resize(digit, (28, 28))

    return digit


def classify_digit(digit_img, model=None):
    """
    Replace this with your trained digit classifier.

    Right now:
    - empty cell handled before this
    - non-empty cell returns -1 as unknown digit
    """

    if digit_img is None:
        return 0

    if model is None:
        return -1

    img = digit_img.astype("float32") / 255.0
    img = img.reshape(1, 28, 28, 1)

    prediction = model.predict(img,verbose=0)
    digit = np.argmax(prediction)

    return int(digit)


def image_to_sudoku_matrix(image_path, model=None):
    if model is None:
        model = get_model()

    warped, cells = preprocess(image_path)

    board = np.zeros((9, 9), dtype=int)

    for row in range(9):
        for col in range(9):
            digit_img = extract_digit(cells[row][col])

            if digit_img is None:
                board[row][col] = 0
            else:
                board[row][col] = classify_digit(digit_img, model)

    return board


def print_board(board):
    for row in board:
        print(row.tolist())


if __name__ == "__main__":
    image_path = "img/sudoku2.png"

    board = image_to_sudoku_matrix(image_path)

    print("Detected Sudoku matrix:")
    print_board(board)
