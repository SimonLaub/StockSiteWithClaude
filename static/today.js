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

async function showToday() {
    errorMessage.hidden = true;
    resultsBody.innerHTML = "";
    showBtn.disabled = true;
    showBtn.textContent = "Henter...";

    try {
        const response = await fetch("/live");
        const data = await response.json();

        if (!response.ok) {
            errorMessage.textContent = data.error || "Der skete en fejl";
            errorMessage.hidden = false;
            return;
        }

        for (const row of data) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${row.name}</td>
                <td>${formatPrice(row.live_price)}</td>
                <td>${formatPrice(row.predicted)}</td>
                <td>${formatDirection(row.predicted_direction)}</td>
            `;
            resultsBody.appendChild(tr);
        }
    } finally {
        showBtn.disabled = false;
        showBtn.textContent = "Vis dagens kurser";
    }
}

showBtn.addEventListener("click", showToday);
