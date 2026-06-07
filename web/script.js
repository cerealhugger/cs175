const uploadForm = document.getElementById("uploadForm");
const imageInput = document.getElementById("imageInput");
const fileName = document.getElementById("fileName");
const imagePreview = document.getElementById("imagePreview");
const previewFrame = document.querySelector(".preview-frame");
const boardGrid = document.getElementById("boardGrid");
const solutionGrid = document.getElementById("solutionGrid");
const solveButton = document.getElementById("solveButton");
const resetButton = document.getElementById("resetButton");
const statusPill = document.getElementById("status");
const algorithmSelect = document.getElementById("algorithmSelect");
const algorithmMetric = document.getElementById("algorithmMetric");
const timeMetric = document.getElementById("timeMetric");
const nodesMetric = document.getElementById("nodesMetric");
const messageBox = document.getElementById("messageBox");

let detectedBoard = emptyBoard();

function emptyBoard() {
    return Array.from({ length: 9 }, () => Array(9).fill(0));
}

function setStatus(message, type = "") {
    statusPill.textContent = message;
    statusPill.className = `status-pill ${type}`;
}

function showMessage(message) {
    messageBox.textContent = message;
    messageBox.hidden = false;
}

function clearMessage() {
    messageBox.textContent = "";
    messageBox.hidden = true;
}

function cellClasses(row, col, extra = "") {
    const classes = [extra];

    if (col === 2 || col === 5) {
        classes.push("box-right");
    }

    if (row === 2 || row === 5) {
        classes.push("box-bottom");
    }

    return classes.filter(Boolean).join(" ");
}

function renderEditableBoard(board) {
    boardGrid.innerHTML = "";

    for (let row = 0; row < 9; row += 1) {
        for (let col = 0; col < 9; col += 1) {
            const value = board[row][col];
            const input = document.createElement("input");
            input.className = cellClasses(row, col, value ? "cell detected" : "cell");
            input.inputMode = "numeric";
            input.maxLength = 1;
            input.dataset.row = row;
            input.dataset.col = col;
            input.value = value === 0 ? "" : String(value);
            input.setAttribute("aria-label", `Row ${row + 1}, column ${col + 1}`);

            input.addEventListener("input", () => {
                const digit = input.value.replace(/[^1-9]/g, "").slice(0, 1);
                input.value = digit;
                input.classList.toggle("detected", digit !== "");
                clearSolution();
            });

            boardGrid.appendChild(input);
        }
    }
}

function renderSolutionBoard(solution, original) {
    solutionGrid.innerHTML = "";

    for (let row = 0; row < 9; row += 1) {
        for (let col = 0; col < 9; col += 1) {
            const value = solution[row][col];
            const added = original[row][col] === 0;
            const cell = document.createElement("div");
            cell.className = cellClasses(row, col, added ? "solution-cell added" : "solution-cell");
            cell.textContent = value === 0 ? "" : String(value);
            solutionGrid.appendChild(cell);
        }
    }
}

function renderBlankSolutionBoard() {
    solutionGrid.innerHTML = "";

    for (let row = 0; row < 9; row += 1) {
        for (let col = 0; col < 9; col += 1) {
            const cell = document.createElement("div");
            cell.className = cellClasses(row, col, "solution-cell");
            solutionGrid.appendChild(cell);
        }
    }
}

function getBoardFromInputs() {
    const board = emptyBoard();
    const inputs = boardGrid.querySelectorAll("input");

    inputs.forEach((input) => {
        const row = Number(input.dataset.row);
        const col = Number(input.dataset.col);
        board[row][col] = input.value === "" ? 0 : Number(input.value);
    });

    return board;
}

function clearSolution() {
    renderBlankSolutionBoard();
    algorithmMetric.textContent = "-";
    timeMetric.textContent = "-";
    nodesMetric.textContent = "-";
}

function resetApp() {
    detectedBoard = emptyBoard();
    imageInput.value = "";
    fileName.textContent = "PNG or JPG";
    imagePreview.removeAttribute("src");
    previewFrame.classList.remove("has-image");
    renderEditableBoard(detectedBoard);
    clearSolution();
    clearMessage();
    solveButton.disabled = true;
    setStatus("Ready");
}

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    if (!file) {
        return;
    }

    fileName.textContent = file.name;
    imagePreview.src = URL.createObjectURL(file);
    previewFrame.classList.add("has-image");
    clearMessage();
    clearSolution();
});

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = imageInput.files[0];

    if (!file) {
        setStatus("Choose image", "error");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    setStatus("Reading...");
    clearMessage();
    solveButton.disabled = true;
    clearSolution();

    try {
        const response = await fetch("/api/read", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Image could not be read.");
        }

        detectedBoard = data.board;
        renderEditableBoard(detectedBoard);
        solveButton.disabled = false;
        setStatus("Board ready", "success");
    } catch (error) {
        setStatus("Read failed", "error");
        showMessage(error.message);
    }
});

solveButton.addEventListener("click", async () => {
    const board = getBoardFromInputs();

    setStatus("Solving...");
    clearMessage();
    clearSolution();

    try {
        const response = await fetch("/api/solve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                board,
                algorithm: algorithmSelect.value,
            }),
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Board could not be solved.");
        }

        renderSolutionBoard(data.solution, board);
        algorithmMetric.textContent = data.algorithm;
        timeMetric.textContent = `${data.time_seconds.toFixed(4)}s`;
        nodesMetric.textContent = `${data.nodes_visited} nodes`;
        setStatus("Solved", "success");
    } catch (error) {
        setStatus("Solve failed", "error");
        showMessage(error.message);
    }
});

resetButton.addEventListener("click", resetApp);

renderEditableBoard(detectedBoard);
renderBlankSolutionBoard();
