
# Sudoku Solver with Computer Vision

This project reads a Sudoku puzzle from an image, recognizes the digits using a trained MNIST-based model, converts the puzzle into a 9x9 matrix, and solves it using backtracking.

## Project Structure
```text
sudoku/
├── mnist.py
├── reader.py
├── solver.py
├── mnist_digit_model.h5
└── README.md
````

## Files

### `mnist.py`

This file trains the digit recognition model.

Pipeline:

```text
Load MNIST dataset
↓
Normalize image pixel values
↓
Reshape images to 28x28x1
↓
Train CNN model
↓
Save trained model
```

The output of this file is:

```text
mnist_digit_model.h5
```

This model is later loaded by `reader.py` to classify digits inside each Sudoku cell.

---

### `reader.py`

This file handles the image processing and digit recognition pipeline.

Its goal is to take an input Sudoku image and return a 9x9 matrix.

Reader pipeline:

```text
Input Sudoku image
↓
Convert image to grayscale
↓
Apply Gaussian blur
↓
Apply adaptive thresholding
↓
Find the largest square contour
↓
Apply perspective transform
↓
Crop the Sudoku board into a top-down view
↓
Split the board into 81 cells
↓
For each cell:
    Detect whether the cell is empty
    If not empty, extract the digit
    Resize digit to 28x28
    Load mnist_digit_model.h5
    Predict the digit using the trained model
↓
Return a 9x9 matrix
```

Empty cells are represented as:

```text
0
```

Example output:

```python
[
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
```

Currently, `reader.py` focuses on image preprocessing and single-digit prediction for each detected cell.

---

### `solver.py`

This file solves the Sudoku puzzle using backtracking.

Input:

```python
9x9 matrix
```

Output:

```python
solved 9x9 matrix
```

The solver checks whether each number placement is valid based on Sudoku rules:

```text
Each row must contain digits 1-9 without repetition
Each column must contain digits 1-9 without repetition
Each 3x3 subgrid must contain digits 1-9 without repetition
```

Solver pipeline:

```text
Receive 9x9 Sudoku matrix
↓
Find an empty cell
↓
Try digits 1-9
↓
Check row, column, and subgrid validity
↓
Place valid digit
↓
Recursively solve the rest of the board
↓
Backtrack if no valid digit works
↓
Return solved board
```

---

## Current Workflow

```text
mnist.py
↓
Train digit recognition model
↓
mnist_digit_model.h5
↓
reader.py
↓
Process Sudoku image and predict digits
↓
9x9 matrix
↓
solver.py
↓
Solve Sudoku puzzle
```

## Future Implementation

The next step is to improve the post-processing layer between `reader.py` and `solver.py`.

Currently, `reader.py` predicts one digit per cell directly from the MNIST model. However, MNIST accuracy on test data does not always transfer well to real Sudoku images because of differences in font, lighting, rotation, grid lines, and image quality.

Future improvement:

```text
For each detected digit cell:
    Store top-k digit predictions with confidence scores
```

Example:

```python
[
    (5, 0.82),
    (6, 0.10),
    (8, 0.04)
]
```

Then validate the predicted matrix using Sudoku rules before sending it to `solver.py`.

Future post-processing pipeline:

```text
reader.py produces candidate predictions
↓
Validate row, column, and 3x3 subgrid constraints
↓
If duplicated digits appear:
    Keep the digit with the highest confidence
    Try the next-best candidate for the conflicting cells
↓
Generate a more reliable 9x9 matrix
↓
Send matrix to solver.py
```

This future layer will help reduce recognition errors before solving the puzzle.

## How to Run

Train the digit recognition model:

```bash
python3 mnist.py
```

This creates:

```text
mnist_digit_model.h5
```

Run the image reader:

```bash
python3 reader.py
```

Run the solver:

```bash
python3 solver.py
```

## Dependencies

Recommended environment:

```bash
conda create -n sudoku-cv python=3.11
conda activate sudoku-cv
```

Install dependencies:

```bash
pip install opencv-python numpy tensorflow matplotlib
```

## Notes

The computer vision component and the solver component are designed separately. This makes the project easier to debug:

```text
reader.py = image to matrix
solver.py = matrix to solved matrix
mnist.py = model training
```

The final goal is to connect all three parts into one complete Sudoku-solving pipeline.


