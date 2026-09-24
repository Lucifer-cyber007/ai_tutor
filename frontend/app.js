// AI Tutor - Phase 3: personalization, Learn / Practice / Quiz / Ask a Doubt, progress + session report.
// The backend is stateless, so everything about this session is kept here in `state`.

const API_BASE = "/api";
const MAX_HISTORY = 20;        // must match MAX_HISTORY_TURNS in backend/main.py
const MAX_MESSAGE_CHARS = 1000;
const PRACTICE_BATCH = 3;      // practice questions fetched at a time
const QUIZ_LENGTH = 5;

const TOPICS = {
  expressions: "Variables and algebraic expressions",
  equations: "Linear equations",
  word_problems: "Word problems",
};

const state = {
  profile: null,               // { name, level, topic }
  mode: "learn",
  busy: false,
  learnStarted: false,
  chats: { learn: [], doubt: [] },   // [{ role: "user" | "assistant", content }]
  practice: newExercise(),
  quiz: { ...newExercise(), status: "intro", results: [] }, // status: intro | loading | question | done
  progress: { results: [], quizScores: [], weakTopics: [] }, // results: [{ skill, correct }]
};

function newExercise() {
  return { questions: [], index: 0, attempts: 0, answered: false, checking: false, lastAnswer: "", feedback: null };
}

// ---------- Page elements ----------
const $ = (id) => document.getElementById(id);
const subtitleEl = $("subtitle");
const errorEl = $("error");
const startScreen = $("start-screen");
const startForm = $("start-form");
const mainScreen = $("main-screen");
const tabs = document.querySelectorAll(".tab");
const chatPanel = $("chat-panel");
const chatEl = $("chat");
const chatForm = $("chat-form");
const inputEl = $("message");
const sendBtn = $("send");
const practicePanel = $("practice-panel");
const quizPanel = $("quiz-panel");
const finishBtn = $("finish");
const progressEl = $("progress");
const summaryScreen = $("summary-screen");

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text; // textContent, never innerHTML, so AI text can't inject HTML
  return node;
}

function button(label, className, onClick) {
  const b = el("button", className, label);
  b.type = "button";
  b.addEventListener("click", onClick);
  return b;
}

// ---------- Talking to the backend ----------
async function api(path, body) {
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Can't reach the tutor. Check your internet connection and try again.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `The server had a problem (error ${res.status}). Please try again.`);
  }
  return data;
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = !message;
}

// While waiting for the AI, lock the tabs and the chat box so the learner can't start two things at once.
function setBusy(busy) {
  state.busy = busy;
  tabs.forEach((t) => (t.disabled = busy));
  sendBtn.disabled = busy;
  finishBtn.disabled = busy;
  inputEl.disabled = busy;
}

// ---------- Start screen ----------
startForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = $("name").value.trim();
  if (!name) return showError("Please enter your name.");
  if (!/^[\p{L}\p{M} .'-]{1,40}$/u.test(name)) return showError("Please use only letters in your name.");

  state.profile = {
    name,
    level: startForm.querySelector('input[name="level"]:checked').value,
    topic: startForm.querySelector('input[name="topic"]:checked').value,
  };
  showError("");
  subtitleEl.textContent = `${name} · ${state.profile.level} · ${TOPICS[state.profile.topic]}`;
  startScreen.hidden = true;
  mainScreen.hidden = false;
  finishBtn.hidden = false;
  renderProgress();
  switchMode("learn");
});

// ---------- Tabs ----------
tabs.forEach((tab) => tab.addEventListener("click", () => switchMode(tab.dataset.mode)));

function switchMode(mode) {
  if (state.busy) return;
  state.mode = mode;
  showError("");
  tabs.forEach((t) => {
    t.classList.toggle("active", t.dataset.mode === mode);
    t.setAttribute("aria-selected", t.dataset.mode === mode);
  });
  chatPanel.hidden = !(mode === "learn" || mode === "doubt");
  practicePanel.hidden = mode !== "practice";
  quizPanel.hidden = mode !== "quiz";

  if (mode === "learn" || mode === "doubt") {
    renderChat();
    if (mode === "learn" && !state.learnStarted) {
      state.learnStarted = true;
      sendChat(`Please start teaching me: ${TOPICS[state.profile.topic]}.`);
    } else {
      inputEl.focus();
    }
  } else if (mode === "practice") {
    state.practice.questions.length ? renderPractice() : loadPractice();
  } else if (mode === "quiz") {
    renderQuiz();
  }
}
