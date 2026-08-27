const COPY_FEEDBACK_DURATION_MS = 1600;
const copyResetTimers = new WeakMap();

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-copy-value]").forEach(button => {
        button.addEventListener("click", async () => {
            const value = button.dataset.copyValue;

            try {
                await copyText(value);
                showCopyFeedback(button, true);
            } catch (_error) {
                showCopyFeedback(button, false);
            }
        });
    });
});

async function copyText(value) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        try {
            await navigator.clipboard.writeText(value);
            return;
        } catch (_error) {
            // Fall back for browsers that expose the API but deny this context.
        }
    }

    const input = document.createElement("textarea");
    input.value = value;
    input.setAttribute("readonly", "");
    input.style.position = "fixed";
    input.style.opacity = "0";
    document.body.appendChild(input);
    input.select();
    const copied = document.execCommand("copy");
    input.remove();

    if (!copied) {
        throw new Error("Clipboard copy failed");
    }
}

function showCopyFeedback(button, copied) {
    const feedback = button.querySelector("[data-copy-feedback]");
    const icon = button.querySelector("i");
    const existingTimer = copyResetTimers.get(button);

    if (existingTimer) {
        window.clearTimeout(existingTimer);
    }

    feedback.textContent = copied ? "Copied" : "Try again";
    icon.className = copied ? "bi bi-check2" : "bi bi-exclamation-circle";
    button.classList.toggle("is-copied", copied);

    const resetTimer = window.setTimeout(() => {
        feedback.textContent = "Copy";
        icon.className = "bi bi-clipboard";
        button.classList.remove("is-copied");
        copyResetTimers.delete(button);
    }, COPY_FEEDBACK_DURATION_MS);
    copyResetTimers.set(button, resetTimer);
}
