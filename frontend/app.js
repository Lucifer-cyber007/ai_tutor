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

// ---------- Learn + Ask a Doubt (chat) ----------
const CHAT_INTROS = {
  learn: (p) => `Hi ${p.name}! Let's learn ${TOPICS[p.topic].toLowerCase()} together. I'll explain one idea at a time and ask you small questions.`,
  doubt: (p) => `Hi ${p.name}! Ask me any doubt about Class 8 algebra. For example: "Why does the sign change when a term moves to the other side?"`,
};

function addBubble(role, text) {
  const row = el("div", `msg ${role === "user" ? "user" : "tutor"}`);
  if (role !== "user") row.appendChild(el("div", "avatar", "x"));
  row.appendChild(el("div", "bubble", text));
  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;
  return row;
}

function addTypingIndicator() {
  const row = addBubble("tutor", "Thinking");
  row.classList.add("typing");
  const dots = el("span", "dots");
  dots.append(el("span"), el("span"), el("span"));
  row.lastChild.appendChild(dots);
  return row;
}

function renderChat() {
  chatEl.replaceChildren();
  addBubble("tutor", CHAT_INTROS[state.mode](state.profile));
  for (const turn of state.chats[state.mode]) addBubble(turn.role, turn.content);
}

async function sendChat(text) {
  const mode = state.mode;
  const history = state.chats[mode];
  showError("");
  addBubble("user", text);
  setBusy(true);
  const typing = addTypingIndicator();

  try {
    const data = await api("/chat", {
      profile: state.profile,
      mode,
      message: text,
      history: history.slice(-MAX_HISTORY),
    });
    history.push({ role: "user", content: text }, { role: "assistant", content: data.reply });
    addBubble("tutor", data.reply);
  } catch (err) {
    showError(err.message);
    inputEl.value = text; // give the text back so the learner can simply press Send again
    growInput();
  } finally {
    typing.remove();
    setBusy(false);
    inputEl.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return showError("Please type a message first.");
  if (text.length > MAX_MESSAGE_CHARS) {
    return showError(`Your message is too long. Please keep it under ${MAX_MESSAGE_CHARS} characters.`);
  }
  inputEl.value = "";
  growInput();
  sendChat(text);
});

// The message box grows with the text (up to a limit set in CSS).
function growInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${inputEl.scrollHeight}px`;
}
inputEl.addEventListener("input", growInput);

// Enter sends, Shift+Enter makes a new line.
inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

// ---------- Shared pieces for Practice and Quiz ----------
function answerForm(ex, label, onSubmit) {
  const form = el("form", "answer-form");
  const input = el("input");
  input.type = "text";
  input.maxLength = 200;
  input.placeholder = "Your answer, e.g. x = 4";
  input.setAttribute("aria-label", "Your answer");
  input.value = ex.lastAnswer;
  const submit = el("button", "primary", label);
  submit.type = "submit";
  input.disabled = submit.disabled = ex.answered || ex.checking;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const answer = input.value.trim();
    if (!answer) return showError("Please type your answer first.");
    ex.lastAnswer = answer;
    onSubmit(answer);
  });
  form.append(input, submit);
  if (!input.disabled) setTimeout(() => input.focus(), 0);
  return form;
}

function feedbackBox(fb) {
  const box = el("div", `feedback ${fb.kind}`);
  box.appendChild(el("strong", "", fb.title));
  for (const line of fb.lines) if (line) box.appendChild(el("div", "", line));
  return box;
}

function checkAnswer(q, answer, attempt) {
  return api("/evaluate", {
    profile: state.profile,
    question: q.question,
    correct_answer: q.answer,
    learner_answer: answer,
    skill: q.skill,
    attempt,
  });
}

function loadingLine(text) {
  const line = el("p", "loading");
  line.append(el("span", "spinner"), text);
  return line;
}

function loadingCard(text) {
  const card = el("div", "card");
  card.appendChild(loadingLine(text));
  return card;
}

function questionMeta(label, skill) {
  const meta = el("div", "q-meta");
  meta.appendChild(el("span", "", label));
  if (skill) meta.appendChild(el("span", "tag", skill));
  return meta;
}

// ---------- Practice ----------
// Hint after the 1st wrong try; full answer after the 2nd wrong try or "Show answer".
async function loadPractice() {
  const p = state.practice;
  showError("");
  setBusy(true);
  practicePanel.replaceChildren(loadingCard("Making practice questions for you..."));
  try {
    const data = await api("/practice", { profile: state.profile, count: PRACTICE_BATCH });
    const done = p.number || 0;
    Object.assign(p, newExercise(), { questions: data.questions, number: done + 1 });
    renderPractice();
  } catch (err) {
    showError(err.message);
    const card = el("div", "card");
    card.append(el("p", "", "Could not load questions."), button("Try again", "primary", loadPractice));
    practicePanel.replaceChildren(card);
  } finally {
    setBusy(false);
  }
}

function renderPractice() {
  const p = state.practice;
  const q = p.questions[p.index];
  const card = el("div", "card");
  card.append(
    questionMeta(`Practice question ${p.number}`, q.skill),
    el("p", "q-text", q.question),
    answerForm(p, "Check", checkPractice),
  );
  if (p.checking) card.appendChild(loadingLine("Checking your answer..."));
  else if (p.feedback) card.appendChild(feedbackBox(p.feedback));

  const actions = el("div", "actions");
  if (p.answered) {
    actions.appendChild(button("Next question", "primary", nextPractice));
  } else if (!p.checking) {
    actions.appendChild(button("Show answer", "secondary", revealPracticeAnswer));
  }
  card.appendChild(actions);
  practicePanel.replaceChildren(card);
}

async function checkPractice(answer) {
  const p = state.practice;
  const q = p.questions[p.index];
  p.attempts += 1;
  p.checking = true;
  showError("");
  setBusy(true);
  renderPractice();
  try {
    const r = await checkAnswer(q, answer, Math.min(p.attempts, 2));
    if (r.correct) {
      p.answered = true;
      recordResult(q.skill, true);
      p.feedback = { kind: "good", title: "Correct! Well done.", lines: [r.encouragement, r.explanation] };
    } else if (p.attempts < 2) {
      p.feedback = { kind: "try", title: "Not quite. Here's a hint:", lines: [r.hint, r.encouragement] };
    } else {
      p.answered = true;
      recordResult(q.skill, false, r.weak_topic);
      p.feedback = { kind: "bad", title: `The answer is ${r.correct_answer}`, lines: [r.explanation, r.encouragement] };
    }
  } catch (err) {
    p.attempts -= 1; // the check failed, so this try doesn't count
    showError(err.message);
  } finally {
    p.checking = false;
    setBusy(false);
    renderPractice();
  }
}

function revealPracticeAnswer() {
  const p = state.practice;
  const q = p.questions[p.index];
  p.answered = true;
  recordResult(q.skill, false); // gave up = not solved
  p.feedback = { kind: "info", title: `The answer is ${q.answer}`, lines: [q.solution] };
  renderPractice();
}

function nextPractice() {
  const p = state.practice;
  if (p.index + 1 >= p.questions.length) return loadPractice();
  const { questions, index, number } = p;
  Object.assign(p, newExercise(), { questions, index: index + 1, number: number + 1 });
  renderPractice();
}
