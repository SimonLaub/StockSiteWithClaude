const datePicker = document.getElementById("date-picker");
const showBtn = document.getElementById("show-btn");
const resultsBody = document.querySelector("#results tbody");
const errorMessage = document.getElementById("error-message");

function formatPrice(value) {
    return value === null ? "–" : value.toFixed(2);
}

function formatDirection(direction) {
    if (direction === "op") return '<span class="up">▲ Op</span>';
    if (direction === "ned") return '<span class="down">▼ Ned</span>';
    if (direction === "uændret") return '<span class="flat">– Uændret</span>';
    return "–";
}

async function showPredictions() {
    errorMessage.hidden = true;
    resultsBody.innerHTML = "";

    const response = await fetch(`/predict?date=${datePicker.value}`);
    const data = await response.json();

    if (!response.ok) {
        errorMessage.textContent = data.error || "Der skete en fejl";
        errorMessage.hidden = false;
        return;
    }

    for (const row of data) {
        const tr = document.createElement("tr");

        const diff = row.predicted !== null && row.actual !== null
            ? row.predicted - row.actual
            : null;

        tr.innerHTML = `
            <td>${row.name}</td>
            <td>${formatPrice(row.predicted)}</td>
            <td>${formatDirection(row.predicted_direction)}</td>
            <td>${formatPrice(row.actual)}</td>
            <td>${formatDirection(row.actual_direction)}</td>
            <td>${formatPrice(diff)}</td>
        `;
        resultsBody.appendChild(tr);
    }
}

showBtn.addEventListener("click", showPredictions);
