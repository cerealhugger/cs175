import json
import mimetypes
import os
import warnings
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from time import perf_counter

warnings.filterwarnings(
    "ignore",
    message="'cgi' is deprecated.*",
    category=DeprecationWarning,
)
import cgi

from solver import (
    DancingLinksSudokuSolver,
    MRVSudokuSolver,
    SudokuSolver,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


class SudokuAppHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_static_file("index.html")
            return

        if self.path == "/style.css":
            self._send_static_file("style.css")
            return

        if self.path == "/script.js":
            self._send_static_file("script.js")
            return

        self.send_error(404, "Not found")

    def do_POST(self):
        if self.path == "/api/read":
            self._handle_read_image()
            return

        if self.path == "/api/solve":
            self._handle_solve()
            return

        self.send_error(404, "Not found")

    def _send_static_file(self, filename):
        path = os.path.join(WEB_DIR, filename)

        if not os.path.exists(path):
            self.send_error(404, "Not found")
            return

        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"

        with open(path, "rb") as file:
            data = file.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status_code, payload):
        data = json.dumps(payload).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_read_image(self):
        content_type = self.headers.get("Content-Type", "")

        if not content_type.startswith("multipart/form-data"):
            self._send_json(400, {"error": "Upload must be multipart/form-data."})
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            },
        )

        file_item = form["image"] if "image" in form else None

        if file_item is None or not file_item.filename:
            self._send_json(400, {"error": "No image file was uploaded."})
            return

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        _, extension = os.path.splitext(file_item.filename)
        extension = extension if extension else ".png"
        upload_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{extension}")

        try:
            with open(upload_path, "wb") as file:
                file.write(file_item.file.read())

            from reader import image_to_sudoku_matrix

            board = image_to_sudoku_matrix(upload_path)

            if hasattr(board, "tolist"):
                board = board.tolist()

            self._send_json(200, {"board": board})
        except Exception as error:
            message = str(error)

            if "NumPy 1.x" in message or "numpy.core._multiarray_umath" in message:
                message = (
                    "TensorFlow cannot start because NumPy 2.x is installed with "
                    "packages compiled for NumPy 1.x. Run: pip install -r requirements.txt "
                    "then restart python3 app.py."
                )
            elif "BatchNormalization" in message or "load_weights" in message:
                message = (
                    "Could not load mnist_digit_model.h5 with this Keras version. "
                    "Try rerunning python3 mnist.py to regenerate the model, then restart app.py."
                )

            self._send_json(500, {"error": message})
        finally:
            if os.path.exists(upload_path):
                os.remove(upload_path)

    def _handle_solve(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
            board = self._validate_board(payload.get("board"))
            algorithm = payload.get("algorithm", "mrv")
            solver_class = self._get_solver_class(algorithm)

            solver = solver_class(board)
            start = perf_counter()
            solved = solver.validate_board() and solver.solve()
            elapsed = perf_counter() - start

            if not solved:
                self._send_json(422, {
                    "error": "No valid solution exists for this board.",
                })
                return

            self._send_json(200, {
                "solution": solver.board,
                "algorithm": solver.name,
                "time_seconds": elapsed,
                "nodes_visited": solver.nodes_visited,
            })
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except Exception as error:
            self._send_json(500, {"error": str(error)})

    def _validate_board(self, board):
        if not isinstance(board, list) or len(board) != 9:
            raise ValueError("Board must be a 9x9 list.")

        clean_board = []

        for row in board:
            if not isinstance(row, list) or len(row) != 9:
                raise ValueError("Board must be a 9x9 list.")

            clean_row = []

            for value in row:
                try:
                    digit = int(value)
                except (TypeError, ValueError):
                    raise ValueError("Board values must be digits from 0 to 9.")

                if digit < 0 or digit > 9:
                    raise ValueError("Board values must be digits from 0 to 9.")

                clean_row.append(digit)

            clean_board.append(clean_row)

        return clean_board

    def _get_solver_class(self, algorithm):
        solver_classes = {
            "backtracking": SudokuSolver,
            "mrv": MRVSudokuSolver,
            "dancing-links": DancingLinksSudokuSolver,
        }

        if algorithm not in solver_classes:
            raise ValueError("Unknown solver algorithm.")

        return solver_classes[algorithm]


def run(host="127.0.0.1", port=8000):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    server = HTTPServer((host, port), SudokuAppHandler)
    print(f"Sudoku app running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
