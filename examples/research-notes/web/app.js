/* Ordinary browser client; the supervisor injects SF_NOTES_API_URL when needed. */
const apiBase = window.SF_NOTES_API_URL || "http://127.0.0.1:8000";
const form = document.querySelector("#create-note");
const feedback = document.querySelector("#feedback");
const list = document.querySelector("#notes");
const query = document.querySelector("#query");

function render(notes) {
  list.replaceChildren(...notes.map((note) => {
    const item = document.createElement("li");
    item.textContent = `${note.title}: ${note.body}`;
    return item;
  }));
}

async function loadNotes() {
  const response = await fetch(`${apiBase}/notes?query=${encodeURIComponent(query.value)}`);
  if (!response.ok) throw new Error("Could not load notes");
  render((await response.json()).notes);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const response = await fetch(`${apiBase}/notes`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ title: document.querySelector("#title").value, body: document.querySelector("#body").value }),
  });
  feedback.textContent = response.ok ? "Note saved." : "Could not save note.";
  if (response.ok) {
    form.reset();
    await loadNotes();
  }
});

query.addEventListener("input", () => loadNotes().catch((error) => { feedback.textContent = error.message; }));
loadNotes().catch((error) => { feedback.textContent = error.message; });
