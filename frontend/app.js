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
