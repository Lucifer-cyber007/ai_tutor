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
