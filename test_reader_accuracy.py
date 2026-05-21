import numpy as np
from reader import image_to_sudoku_matrix
from tensorflow.keras.models import load_model

model = load_model("mnist_digit_model.h5")


def calculate_accuracy(predicted, ground_truth):
    predicted = np.array(predicted)
    ground_truth = np.array(ground_truth)

    if predicted.shape != (9, 9) or ground_truth.shape != (9, 9):
        raise ValueError("Both matrices must be 9x9.")

    total_cells = 81
    correct_cells = np.sum(predicted == ground_truth)
    accuracy = correct_cells / total_cells

    return correct_cells, total_cells, accuracy


def print_mistakes(predicted, ground_truth):
    print("\nMistakes:")

    has_mistake = False

    for row in range(9):
        for col in range(9):
            if predicted[row][col] != ground_truth[row][col]:
                has_mistake = True
                print(
                    f"Cell ({row}, {col}): "
                    f"predicted={predicted[row][col]}, "
                    f"expected={ground_truth[row][col]}"
                )

    if not has_mistake:
        print("No mistakes found.")


def test_reader(image_path, ground_truth):
    predicted = image_to_sudoku_matrix(image_path, model)

    print("Predicted matrix:")
    print(predicted)

    print("\nGround truth matrix:")
    print(np.array(ground_truth))

    correct, total, accuracy = calculate_accuracy(predicted, ground_truth)

    print(f"\nCorrect cells: {correct}/{total}")
    print(f"Accuracy: {accuracy * 100:.2f}%")

    print_mistakes(predicted, ground_truth)


if __name__ == "__main__":
    image_paths = ['img/sudoku1.png',
                   'img/sudoku2.png'
                    ]

    truth = [
        [
        [9, 0, 0, 5, 0, 8, 0, 0, 7],
        [0, 8, 0, 3, 0, 2, 9, 0, 5],
        [0, 5, 4, 0, 0, 0, 0, 8, 0],
        [0, 7, 0, 6, 8, 0, 0, 3, 2],
        [1, 0, 0, 0, 0, 4, 0, 0, 8],
        [5, 0, 0, 2, 1, 9, 0, 6, 0],
        [0, 0, 0, 9, 0, 6, 0, 0, 1],
        [7, 2, 6, 0, 0, 1, 0, 4, 0],
        [0, 0, 1, 4, 7, 0, 0, 5, 6]
        ],
        [
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

    ]

    for p,t in zip(image_paths,truth):

        test_reader(p, t)