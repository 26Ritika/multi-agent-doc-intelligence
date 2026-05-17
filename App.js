import { useState, useEffect, useRef } from "react";

const AGENTS = [
  { id: "orchestrator", name: "Orchestrator", icon: "⬡", color: "#00D4FF", role: "Coordinates all agents" },
  { id: "extractor", name: "Extractor", icon: "◈", color: "#00FF94", role: "Extracts raw text & tables" },
  { id: "summarizer", name: "Summarizer", icon: "◎", color: "#FFB800", role: "Generates multi-level summaries" },
  { id: "analyzer", name: "Analyzer", icon: "◆", color: "#FF6B6B", role: "Finds entities & risks" },
  { id: "qa", name: "QA Agent", icon: "◉", color: "#B388FF", role: "Answers with citations" },
  { id: "aggregator", name: "Aggregator", icon: "⬟", color: "#FF8C42", role: "Combines all outputs" },
];

const MOCK_LOGS = [
  { agent: "orchestrator", msg: "Document received. Analyzing type..." },
  { agent: "orchestrator", msg: "Detected: Research Paper. Routing to agents." },
  { agent: "extractor", msg: "Extracting raw text from pages..." },
  { agent: "extractor", msg: "Chunking complete. Storing in ChromaDB..." },
  { agent: "summarizer", msg: "Generating summaries..." },
  { agent: "summarizer", msg: "One-line summary ready." },
  { agent: "analyzer", msg: "Scanning for named entities..." },
  { agent: "analyzer", msg: "Found entities, risks & insights." },
  { agent: "qa", msg: "Building Graph RAG index..." },
  { agent: "qa", msg: "Multilingual RAG pipeline ready." },
  { agent: "aggregator", msg: "Merging all agent outputs..." },
  { agent: "aggregator", msg: "Final report compiled successfully." },
];

export default function App() {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [activeAgents, setActiveAgents] = useState({});
  const [result, setResult] = useState(null);
  const [question, setQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [activeTab, setActiveTab] = useState("summary");
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const fetchMetrics = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/metrics");
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error("Metrics error:", error);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.type === "application/pdf") setFile(dropped);
  };

  const startProcessing = async () => {
    if (!file) return;
    setIsProcessing(true);
    setLogs([]);
    setActiveAgents({});
    setResult(null);
    setProgress(0);

    const logSequence = [
      { agent: "orchestrator", msg: "Document received. Analyzing type..." },
      { agent: "extractor", msg: "Extracting text from PDF..." },
      { agent: "extractor", msg: "Storing chunks in ChromaDB..." },
      { agent: "extractor", msg: "Building Graph RAG connections..." },
      { agent: "summarizer", msg: "Generating summaries..." },
      { agent: "analyzer", msg: "Finding entities, risks & insights..." },
      { agent: "qa", msg: "Building QA index..." },
      { agent: "aggregator", msg: "Combining all outputs..." },
    ];

    let i = 0;
    const logInterval = setInterval(() => {
      if (i < logSequence.length) {
        const log = logSequence[i];
        setLogs((prev) => [...prev, { ...log, time: new Date().toLocaleTimeString() }]);
        setActiveAgents((prev) => ({ ...prev, [log.agent]: true }));
        setProgress(Math.round(((i + 1) / logSequence.length) * 100));
        i++;
      }
    }, 800);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      clearInterval(logInterval);
      setProgress(100);
      setLogs((prev) => [...prev, { agent: "aggregator", msg: "Final report ready!", time: new Date().toLocaleTimeString() }]);
      setResult(data);
      setIsProcessing(false);
      setTimeout(() => setActiveAgents({}), 1000);
      fetchMetrics();
    } catch (error) {
      clearInterval(logInterval);
      setLogs((prev) => [...prev, { agent: "orchestrator", msg: "Error: " + error.message, time: new Date().toLocaleTimeString() }]);
      setIsProcessing(false);
    }
  };

  const handleQuestion = async () => {
    if (!question.trim()) return;
    setQaAnswer("Searching document...");
    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await response.json();
      setQaAnswer(data.answer);
      fetchMetrics();
    } catch (error) {
      setQaAnswer("Error: Could not get answer.");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#050810", color: "#E8EAF6", fontFamily: "'JetBrains Mono', monospace" }}>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #1a1f35", padding: "16px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 36, height: 36, background: "linear-gradient(135deg, #00D4FF, #B388FF)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>⬡</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, letterSpacing: 1 }}>MULTI-AGENT DOC INTELLIGENCE</div>
            <div style={{ fontSize: 10, color: "#4a5568", letterSpacing: 2 }}>LANGGRAPH + CHROMADB + GRAPH RAG + MULTILINGUAL</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {AGENTS.map(a => (
            <div key={a.id} style={{
              width: 10, height: 10, borderRadius: "50%",
              background: activeAgents[a.id] ? a.color : "#1a1f35",
              boxShadow: activeAgents[a.id] ? `0 0 8px ${a.color}` : "none",
              transition: "all 0.3s"
            }} title={a.name} />
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0, height: "calc(100vh - 70px)" }}>

        {/* LEFT PANEL */}
        <div style={{ borderRight: "1px solid #1a1f35", display: "flex", flexDirection: "column" }}>

          {/* Upload Zone */}
          <div style={{ padding: 24, borderBottom: "1px solid #1a1f35" }}>
            <div
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onClick={() => document.getElementById("fileInput").click()}
              style={{
                border: `2px dashed ${isDragging ? "#00D4FF" : file ? "#00FF94" : "#1a1f35"}`,
                borderRadius: 12, padding: 28, textAlign: "center", cursor: "pointer",
                background: isDragging ? "rgba(0,212,255,0.05)" : "rgba(255,255,255,0.01)",
                transition: "all 0.3s"
              }}
            >
              <div style={{ fontSize: 32, marginBottom: 8 }}>{file ? "📄" : "⬆"}</div>
              <div style={{ fontSize: 13, color: file ? "#00FF94" : "#4a5568" }}>
                {file ? file.name : "Drop PDF here or click to upload"}
              </div>
              <input id="fileInput" type="file" accept=".pdf" style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files[0])} />
            </div>

            {file && (
              <button onClick={startProcessing} disabled={isProcessing} style={{
                marginTop: 12, width: "100%", padding: "12px 0",
                background: isProcessing ? "#1a1f35" : "linear-gradient(135deg, #00D4FF, #B388FF)",
                border: "none", borderRadius: 8, color: "#050810",
                fontWeight: 700, fontSize: 13, cursor: isProcessing ? "not-allowed" : "pointer",
                letterSpacing: 2, fontFamily: "inherit"
              }}>
                {isProcessing ? `PROCESSING... ${progress}%` : "▶ RUN ALL AGENTS"}
              </button>
            )}

            {isProcessing && (
              <div style={{ marginTop: 8, height: 4, background: "#1a1f35", borderRadius: 2 }}>
                <div style={{ height: "100%", width: `${progress}%`, background: "linear-gradient(90deg, #00D4FF, #B388FF)", borderRadius: 2, transition: "width 0.5s" }} />
              </div>
            )}
          </div>

          {/* Agents Grid */}
          <div style={{ padding: 24, borderBottom: "1px solid #1a1f35" }}>
            <div style={{ fontSize: 10, color: "#4a5568", letterSpacing: 3, marginBottom: 12 }}>AGENT STATUS</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              {AGENTS.map(agent => (
                <div key={agent.id} style={{
                  padding: "10px 12px",
                  background: activeAgents[agent.id] ? `${agent.color}15` : "rgba(255,255,255,0.02)",
                  border: `1px solid ${activeAgents[agent.id] ? agent.color : "#1a1f35"}`,
                  borderRadius: 8, transition: "all 0.4s",
                  boxShadow: activeAgents[agent.id] ? `0 0 12px ${agent.color}30` : "none"
                }}>
                  <div style={{ fontSize: 18, marginBottom: 4, color: activeAgents[agent.id] ? agent.color : "#2a3050" }}>{agent.icon}</div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: activeAgents[agent.id] ? agent.color : "#4a5568" }}>{agent.name}</div>
                  <div style={{ fontSize: 9, color: "#4a5568", marginTop: 2 }}>{agent.role}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Live Logs */}
          <div style={{ flex: 1, padding: 24, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 10, color: "#4a5568", letterSpacing: 3, marginBottom: 12 }}>LIVE AGENT LOGS</div>
            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
              {logs.length === 0 && (
                <div style={{ color: "#2a3050", fontSize: 12, textAlign: "center", marginTop: 20 }}>Waiting for document...</div>
              )}
              {logs.map((log, i) => {
                const agent = AGENTS.find(a => a.id === log.agent);
                return (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <span style={{ color: agent?.color, fontSize: 10, minWidth: 80 }}>[{agent?.name}]</span>
                    <span style={{ color: "#8892b0", fontSize: 11, flex: 1 }}>{log.msg}</span>
                    <span style={{ color: "#2a3050", fontSize: 9 }}>{log.time}</span>
                  </div>
                );
              })}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          {!result ? (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 12, color: "#2a3050" }}>
              <div style={{ fontSize: 48 }}>⬡</div>
              <div style={{ fontSize: 13, letterSpacing: 2 }}>AWAITING ANALYSIS</div>
              <div style={{ fontSize: 11, color: "#1a1f35" }}>Upload a PDF to begin</div>
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div style={{ display: "flex", borderBottom: "1px solid #1a1f35" }}>
                {["summary", "entities", "risks", "qa", "metrics"].map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)} style={{
                    flex: 1, padding: "14px 0", background: "none", border: "none",
                    borderBottom: `2px solid ${activeTab === tab ? "#00D4FF" : "transparent"}`,
                    color: activeTab === tab ? "#00D4FF" : "#4a5568",
                    fontFamily: "inherit", fontSize: 10, fontWeight: 700,
                    letterSpacing: 2, cursor: "pointer", textTransform: "uppercase"
                  }}>{tab}</button>
                ))}
              </div>

              <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>

                {activeTab === "summary" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div style={{ background: "rgba(0,212,255,0.05)", border: "1px solid rgba(0,212,255,0.2)", borderRadius: 10, padding: 16 }}>
                      <div style={{ fontSize: 9, color: "#00D4FF", letterSpacing: 3, marginBottom: 8 }}>ONE-LINE SUMMARY</div>
                      <div style={{ fontSize: 13, lineHeight: 1.6 }}>{result.summary?.oneline}</div>
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid #1a1f35", borderRadius: 10, padding: 16 }}>
                      <div style={{ fontSize: 9, color: "#FFB800", letterSpacing: 3, marginBottom: 8 }}>FULL SUMMARY</div>
                      <div style={{ fontSize: 12, lineHeight: 1.8, color: "#8892b0" }}>{result.summary?.paragraph}</div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                      {[
                        [result.pages || 0, "Pages"],
                        [result.word_count || 0, "Words"],
                        [`${result.processing_time || 0}s`, "Time"]
                      ].map(([n, l]) => (
                        <div key={l} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid #1a1f35", borderRadius: 10, padding: 16, textAlign: "center" }}>
                          <div style={{ fontSize: 28, fontWeight: 700, color: "#00D4FF" }}>{n}</div>
                          <div style={{ fontSize: 10, color: "#4a5568", letterSpacing: 1 }}>{l}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === "entities" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <div style={{ fontSize: 9, color: "#00FF94", letterSpacing: 3, marginBottom: 4 }}>EXTRACTED ENTITIES</div>
                    {result.entities?.map((e, i) => (
                      <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", background: "rgba(0,255,148,0.05)", border: "1px solid rgba(0,255,148,0.15)", borderRadius: 8 }}>
                        <span style={{ color: "#00FF94" }}>◈</span>
                        <span style={{ fontSize: 12 }}>{e}</span>
                      </div>
                    ))}
                    <div style={{ fontSize: 9, color: "#FF6B6B", letterSpacing: 3, margin: "16px 0 4px" }}>KEY INSIGHTS</div>
                    {result.insights?.map((ins, i) => (
                      <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", background: "rgba(255,107,107,0.05)", border: "1px solid rgba(255,107,107,0.15)", borderRadius: 8 }}>
                        <span style={{ color: "#FF6B6B" }}>◆</span>
                        <span style={{ fontSize: 12 }}>{ins}</span>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "risks" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    <div style={{ fontSize: 9, color: "#FF6B6B", letterSpacing: 3, marginBottom: 4 }}>⚠ RISK FLAGS</div>
                    {result.risks?.map((r, i) => (
                      <div key={i} style={{ padding: 16, background: "rgba(255,107,107,0.07)", border: "1px solid rgba(255,107,107,0.25)", borderRadius: 10, borderLeft: "3px solid #FF6B6B" }}>
                        <div style={{ fontSize: 12, color: "#FF6B6B", marginBottom: 4 }}>Risk #{i + 1}</div>
                        <div style={{ fontSize: 13 }}>{r}</div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === "qa" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <div style={{ fontSize: 9, color: "#B388FF", letterSpacing: 3 }}>ASK THE DOCUMENT</div>
                    <div style={{ fontSize: 10, color: "#4a5568" }}>✨ Supports Hindi, Spanish, French and more!</div>
                    <div style={{ display: "flex", gap: 8 }}>
                      <input
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleQuestion()}
                        placeholder="Ask in any language..."
                        style={{
                          flex: 1, padding: "10px 14px",
                          background: "rgba(255,255,255,0.03)",
                          border: "1px solid #1a1f35", borderRadius: 8,
                          color: "#E8EAF6", fontFamily: "inherit", fontSize: 12, outline: "none"
                        }}
                      />
                      <button onClick={handleQuestion} style={{
                        padding: "10px 16px", background: "linear-gradient(135deg, #B388FF, #00D4FF)",
                        border: "none", borderRadius: 8, color: "#050810",
                        fontWeight: 700, cursor: "pointer", fontFamily: "inherit", fontSize: 12
                      }}>ASK</button>
                    </div>
                    {qaAnswer && (
                      <div style={{ padding: 16, background: "rgba(179,136,255,0.07)", border: "1px solid rgba(179,136,255,0.25)", borderRadius: 10 }}>
                        <div style={{ fontSize: 9, color: "#B388FF", letterSpacing: 3, marginBottom: 8 }}>◉ QA AGENT RESPONSE</div>
                        <div style={{ fontSize: 12, lineHeight: 1.8, whiteSpace: "pre-line" }}>{qaAnswer}</div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "metrics" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div style={{ fontSize: 9, color: "#00D4FF", letterSpacing: 3 }}>PERFORMANCE METRICS</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                      {[
                        ["📄", "Documents", metrics?.total_documents || 0],
                        ["❓", "Questions", metrics?.total_questions || 0],
                        ["⚡", "Avg Time", `${metrics?.avg_processing_time || 0}s`],
                        ["🔄", "Avg Retries", metrics?.avg_retries || 0],
                      ].map(([icon, label, value]) => (
                        <div key={label} style={{ padding: 16, background: "rgba(0,212,255,0.05)", border: "1px solid rgba(0,212,255,0.2)", borderRadius: 10, textAlign: "center" }}>
                          <div style={{ fontSize: 24 }}>{icon}</div>
                          <div style={{ fontSize: 22, fontWeight: 700, color: "#00D4FF" }}>{value}</div>
                          <div style={{ fontSize: 10, color: "#4a5568" }}>{label}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid #1a1f35", borderRadius: 10, padding: 16 }}>
                      <div style={{ fontSize: 9, color: "#FFB800", letterSpacing: 3, marginBottom: 12 }}>RECENT DOCUMENTS</div>
                      {metrics?.recent_documents?.length > 0 ? (
                        metrics.recent_documents.map((doc, i) => (
                          <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #1a1f35", fontSize: 11 }}>
                            <span style={{ color: "#E8EAF6" }}>📄 {doc.filename}</span>
                            <span style={{ color: "#00FF94" }}>{doc.processing_time}s</span>
                            <span style={{ color: "#4a5568" }}>{doc.timestamp}</span>
                          </div>
                        ))
                      ) : (
                        <div style={{ color: "#4a5568", fontSize: 12, textAlign: "center" }}>No documents yet!</div>
                      )}
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid #1a1f35", borderRadius: 10, padding: 16 }}>
                      <div style={{ fontSize: 9, color: "#B388FF", letterSpacing: 3, marginBottom: 12 }}>LANGUAGES DETECTED</div>
                      {metrics?.languages_detected && Object.entries(metrics.languages_detected).map(([lang, count]) => (
                        <div key={lang} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 12 }}>
                          <span style={{ color: "#E8EAF6" }}>🌍 {lang.toUpperCase()}</span>
                          <span style={{ color: "#B388FF" }}>{count} questions</span>
                        </div>
                      ))}
                      {(!metrics?.languages_detected || Object.keys(metrics.languages_detected).length === 0) && (
                        <div style={{ color: "#4a5568", fontSize: 12, textAlign: "center" }}>No questions asked yet!</div>
                      )}
                    </div>
                  </div>
                )}

              </div>
            </>
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #050810; }
        ::-webkit-scrollbar-thumb { background: #1a1f35; border-radius: 2px; }
      `}</style>
    </div>
  );
}