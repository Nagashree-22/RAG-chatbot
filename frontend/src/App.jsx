import { useEffect, useRef, useState } from "react";

const API = "/api";

function BackgroundRobot({ mood, blended }) {
  const [gaze, setGaze] = useState({ x: 0, y: 0 });
  const robotRef = useRef(null);

  useEffect(() => {
    function followPointer(event) {
      const bounds = robotRef.current?.getBoundingClientRect();
      if (!bounds) return;

      setGaze({
        x: Math.max(-17, Math.min(17, ((event.clientX - (bounds.left + bounds.width / 2)) / bounds.width) * 34)),
        y: Math.max(-12, Math.min(12, ((event.clientY - (bounds.top + bounds.height / 2)) / bounds.height) * 24)),
      });
    }

    window.addEventListener("pointermove", followPointer, { passive: true });
    return () => window.removeEventListener("pointermove", followPointer);
  }, []);

  const smile = ["joy", "love", "surprise", "listening"].includes(mood);
  const mouthPath = smile
    ? "M520 680 Q550 708 580 680"
    : mood === "caring"
      ? "M525 692 Q550 681 575 692"
      : "M530 687 Q550 687 570 687";

  return (
    <div
      className={`companion-layer mood-${mood}${blended ? " is-blended" : ""}`}
      aria-hidden="true"
    >
      <div className="companion-glow" />
      <div
        ref={robotRef}
        className="companion-robot"
      >
        <img
          className="companion-art"
          src="/assets/robot_neutral.png"
          alt=""
        />
        <svg
          className="companion-face"
          viewBox="0 0 1024 1536"
          preserveAspectRatio="xMidYMid meet"
          role="presentation"
        >
          <defs>
            <radialGradient id="pupil" cx="35%" cy="30%">
              <stop offset="0" stopColor="#174c69" />
              <stop offset="1" stopColor="#071627" />
            </radialGradient>
          </defs>
          <g className="robot-pupils">
            <g transform={`translate(${451 + gaze.x} ${603 + gaze.y})`}>
              <circle r="13" fill="url(#pupil)" />
              <circle cx="-4" cy="-5" r="3.2" fill="#f1ffff" />
            </g>
            <g transform={`translate(${635 + gaze.x} ${603 + gaze.y})`}>
              <circle r="13" fill="url(#pupil)" />
              <circle cx="-4" cy="-5" r="3.2" fill="#f1ffff" />
            </g>
          </g>
          <g className="robot-blink">
            <ellipse cx="451" cy="603" rx="41" ry="38" fill="#0b1b30" />
            <ellipse cx="635" cy="603" rx="41" ry="38" fill="#0b1b30" />
          </g>
          <path
            className="robot-mouth"
            d={mouthPath}
            fill="none"
            stroke="#ff8eaf"
            strokeWidth="11"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div className="companion-caption">
        <span className="companion-status-dot" />
        {mood === "thinking" ? "Thinking with you" : "Here with you"}
      </div>
    </div>
  );
}

function getRobotMood(emotion) {
  if (["joy", "love", "surprise"].includes(emotion)) return emotion;
  if (["sadness", "anger", "fear", "stress", "loneliness"].includes(emotion)) {
    return "caring";
  }
  return "neutral";
}

async function request(path, options) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail || "The request could not be completed.");
  }
  return result;
}

async function streamChat(message, onToken) {
  const response = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const result = await response.json();
    throw new Error(result.detail || "The request could not be completed.");
  }
  if (!response.body) {
    throw new Error("The browser could not read the streamed response.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result = null;
  const handleEvent = (line) => {
    if (!line.trim()) return;
    const event = JSON.parse(line);
    if (event.type === "token") {
      onToken(event.content);
    } else if (event.type === "done") {
      result = event;
    } else if (event.type === "error") {
      throw new Error(event.detail || "The request could not be completed.");
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || "";
    lines.forEach(handleEvent);
    if (done) break;
  }
  if (buffer.trim()) handleEvent(buffer);
  if (!result) throw new Error("The AI service ended the response unexpectedly.");
  return result;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [popupImage, setPopupImage] = useState(null);
  const [popupEmotion, setPopupEmotion] = useState(null);
  const [health, setHealth] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState("");
  const [robotMood, setRobotMood] = useState("listening");
  const [backgroundBlended, setBackgroundBlended] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    request("/health")
      .then(setHealth)
      .catch(() => setHealth({ status: "offline", groq_configured: false }));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  useEffect(() => {
    if (!popupImage) return undefined;
    const timer = window.setTimeout(() => setPopupImage(null), 3500);
    return () => window.clearTimeout(timer);
  }, [popupImage]);

  async function openHistory() {
    setShowHistory((visible) => !visible);
    try {
      setHistory(await request("/history"));
    } catch (cause) {
      setError(cause.message);
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;

    setQuestion("");
    setError("");
    setAnalysis(null);
    setPopupImage(null);
    setPopupEmotion(null);
    setRobotMood("thinking");
    setBackgroundBlended(true);
    setMessages((current) => [...current, { role: "user", content: text }]);
    setBusy(true);
    let previewShown = false;
    try {
      try {
        const preview = await request("/emotion", {
          method: "POST",
          body: JSON.stringify({ message: text }),
        });
        setPopupImage(preview.robot_image);
        setPopupEmotion(preview.emotion);
        setRobotMood(getRobotMood(preview.emotion));
        previewShown = true;
      } catch (cause) {
        console.error("Could not show the immediate emotion preview.", cause);
      }

      const result = await streamChat(text, (token) => {
        setMessages((current) => {
          const last = current[current.length - 1];
          if (last?.role === "assistant") {
            return [
              ...current.slice(0, -1),
              { ...last, content: last.content + token },
            ];
          }
          return [...current, { role: "assistant", content: token }];
        });
      });
      setMessages((current) => {
        const finalMessage = { role: "assistant", content: result.answer };
        if (current[current.length - 1]?.role === "assistant") {
          return [...current.slice(0, -1), finalMessage];
        }
        return [...current, finalMessage];
      });
      setAnalysis(result);
      if (!previewShown) {
        setPopupImage(result.robot_image);
        setPopupEmotion(result.emotion);
      }
      setHistory((current) => [
        ...current,
        { role: "user", content: text },
        { role: "assistant", content: result.answer },
      ]);
    } catch (cause) {
      setError(cause.message);
    } finally {
      setBusy(false);
    }
  }

  function startNewChat() {
    setMessages([]);
    setQuestion("");
    setAnalysis(null);
    setPopupImage(null);
    setPopupEmotion(null);
    setError("");
    setRobotMood("listening");
    setBackgroundBlended(false);
    setShowHistory(false);
  }

  async function clearHistory() {
    if (!window.confirm("Clear all saved chat history?")) return;
    try {
      await request("/history", { method: "DELETE" });
      setHistory([]);
    } catch (cause) {
      setError(cause.message);
    }
  }

  return (
    <>
    <BackgroundRobot mood={robotMood} blended={backgroundBlended} />
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" onClick={(event) => event.preventDefault()}>
          <img src="/assets/logo.png" alt="" />
          <span>
            <strong>MindCare</strong>
            <small>YOUR WELLNESS COMPANION</small>
          </span>
        </a>

        <button className="new-chat-button" onClick={startNewChat}>
          <span aria-hidden="true">＋</span> New conversation
        </button>
        <button
          className={`side-link ${showHistory ? "selected" : ""}`}
          onClick={openHistory}
        >
          <span aria-hidden="true">◷</span> Chat history
        </button>

        {showHistory && (
          <section className="history-panel" aria-label="Chat history">
            <div className="history-heading">
              <span>Recent messages</span>
              <button onClick={clearHistory} title="Clear all saved history">
                Clear
              </button>
            </div>
            {history.length === 0 ? (
              <p className="history-empty">Your saved conversations will show here.</p>
            ) : (
              [...history].reverse().map((item, index) => (
                <div className="history-item" key={`${index}-${item.role}`}>
                  <span>{item.role === "user" ? "You" : "MindCare"}</span>
                  <p>{item.content}</p>
                </div>
              ))
            )}
          </section>
        )}

        <div className="sidebar-bottom">
          <div className="privacy-note">
            <span aria-hidden="true">♡</span>
            <p>A gentle space to reflect, learn, and feel heard.</p>
          </div>
          <div className="service-state">
            <span className={health?.status === "ok" ? "status-dot" : "status-dot offline"} />
            {health?.status === "ok" ? "Assistant is ready" : "Connecting to assistant"}
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="eyebrow">A LITTLE SPACE FOR YOU</span>
            <h1>How are you feeling today?</h1>
          </div>
          <div className="topbar-mark">
            <span className="sparkle">✦</span>
            MindCare AI
          </div>
        </header>

        <div className="conversation">
          {messages.length === 0 ? (
            <section className="welcome-card">
              <div className="welcome-copy">
                <span className="welcome-tag">YOU’RE IN A SAFE SPACE</span>
                <h2>Every feeling<br />has a place here.</h2>
                <p>
                  Share what’s on your mind. I’m here to listen, offer support,
                  and help you find a helpful next step.
                </p>
                <div className="prompt-chips">
                  {[
                    "I’ve been feeling stressed",
                    "I want to celebrate something",
                    "I’m not sure how I feel",
                  ].map((prompt) => (
                    <button key={prompt} onClick={() => setQuestion(prompt)}>
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </section>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <article className={`message ${message.role}`} key={index}>
                  {message.role === "assistant" && (
                    <img src="/assets/logo.png" alt="" className="message-avatar" />
                  )}
                  <div className="message-body">
                    <span className="message-author">
                      {message.role === "user" ? "You" : "MindCare"}
                    </span>
                    <p>{message.content}</p>
                  </div>
                </article>
              ))}
              {busy && (
                <div className="typing-indicator" aria-live="polite">
                  <span /><span /><span /> MindCare is thinking
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}

          {error && <div className="error-banner" role="alert">{error}</div>}

          {analysis && (
            <section className="analysis-card" aria-live="polite">
              <div className="analysis-content">
                <div className="analysis-title">
                  <div>
                    <span className="eyebrow">I HEAR YOU</span>
                    <h2>Let’s check in</h2>
                  </div>
                  <span className="emotion-pill">
                    {analysis.emotion.replaceAll("_", " ")}
                  </span>
                </div>
                <div className="confidence">
                  <span>Feeling match</span>
                  <strong>{Math.round(analysis.confidence * 100)}%</strong>
                  <div className="confidence-track">
                    <span style={{ width: `${analysis.confidence * 100}%` }} />
                  </div>
                </div>
                {analysis.suggestions.length > 0 && (
                  <div className="suggestions">
                    <h3>A few gentle ideas</h3>
                    <ul>
                      {analysis.suggestions.slice(0, 4).map((suggestion) => (
                        <li key={suggestion}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {analysis.retrieved_documents.length > 0 && (
                  <details className="knowledge-details">
                    <summary>Helpful reading</summary>
                    {analysis.retrieved_documents.map((document, index) => (
                      <p key={index}>{document}</p>
                    ))}
                  </details>
                )}
              </div>
            </section>
          )}
        </div>

        {popupImage && (
          <div
            className="emotion-popover"
            key={`${messages.length}-${analysis?.emotion}`}
            aria-label={`${analysis?.emotion.replaceAll("_", " ")} emotion robot`}
          >
            <img
              src={popupImage}
              alt={`${analysis?.emotion.replaceAll("_", " ")} robot`}
            />
          </div>
        )}

        {!health?.groq_configured && health?.status === "ok" && (
          <div className="setup-notice">
            Add your <code>GROQ_API_KEY</code> to the project <code>.env</code> file
            to enable replies.
          </div>
        )}

        <form className="composer" onSubmit={sendMessage}>
          <label className="sr-only" htmlFor="message-input">Your message</label>
          <textarea
            id="message-input"
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
              if (event.target.value.trim()) setBackgroundBlended(true);
              setRobotMood(event.target.value.trim() ? "listening" : "neutral");
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage(event);
              }
            }}
            placeholder="Share what’s on your mind..."
            rows={1}
            maxLength={4000}
            disabled={busy}
          />
          <span className="composer-hint">Press Enter to send · Shift + Enter for a new line</span>
          <button className="send-button" type="submit" disabled={!question.trim() || busy}>
            {busy ? "…" : "↑"}
            <span className="sr-only">Send message</span>
          </button>
        </form>
        <p className="disclaimer">
          MindCare offers supportive information, not a substitute for professional care.
        </p>
      </main>
    </div>
    </>
  );
}

export default App;
