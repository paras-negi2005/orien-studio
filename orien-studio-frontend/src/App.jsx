import { useState, useEffect } from "react";
import "./App.css";
import API from "./api";

function App() {
  const [url, setUrl] = useState("");
  const [hasCaptions, setHasCaptions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  
  // Project ID state (MongoDB project identifier)
  const [projectId, setProjectId] = useState("");
  const [results, setResults] = useState(null);

  // Google Cloud Agent Builder settings
  const [agentId, setAgentId] = useState(() => localStorage.getItem("gcb_agent_id") || "");
  const [gcpProjectId, setGcpProjectId] = useState(() => localStorage.getItem("gcb_project_id") || "");
  const [showSettings, setShowSettings] = useState(false);

  // Local Copilot Chat state (when Agent Builder is not configured)
  const [chatMessages, setChatMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I am your Orien AI Copilot. Paste a YouTube URL or ask me to generate clips, captions, or vertical shorts for you."
    }
  ]);
  const [chatInput, setChatInput] = useState("");

  // Load GCP script dynamically when credentials are set
  useEffect(() => {
    if (agentId && gcpProjectId) {
      const script = document.createElement("script");
      script.src = "https://www.gstatic.com/agentbuilder/web-agent/sdks/web-agent-sdk.js";
      script.async = true;
      document.head.appendChild(script);
      return () => {
        document.head.removeChild(script);
      };
    }
  }, [agentId, gcpProjectId]);

  // Save GCP settings
  const saveSettings = (e) => {
    e.preventDefault();
    localStorage.setItem("gcb_agent_id", agentId);
    localStorage.setItem("gcb_project_id", gcpProjectId);
    setShowSettings(false);
    setChatMessages((prev) => [
      ...prev,
      { sender: "bot", text: `Connected successfully to Google Cloud Agent ${agentId}!` }
    ]);
  };

  // Helper to format video source links
  const getClipUrl = (path) => {
    if (!path) return "";
    const cleanPath = path.replace(/\\/g, "/").replace(/^clips\//, "");
    return `${API.defaults.baseURL}/clips/${cleanPath}`;
  };

  // Poll results for active project ID
  const fetchResults = async (idToFetch) => {
    const id = idToFetch || projectId;
    if (!id) return;
    try {
      const response = await API.get(`/results?project_id=${id}`);
      if (response.data && response.data.status === "success") {
        setResults(response.data);
      }
    } catch (err) {
      console.error("Error fetching project results:", err);
    }
  };

  // Refresh current project results manually
  const handleRefresh = () => {
    if (projectId) {
      fetchResults(projectId);
    } else {
      // Find latest project
      API.get("/results")
        .then((res) => {
          if (res.data && res.data.project_id) {
            setProjectId(res.data.project_id);
            setResults(res.data);
          }
        })
        .catch(console.error);
    }
  };

  // Load latest project on mount
  useEffect(() => {
    API.get("/results")
      .then((res) => {
        if (res.data && res.data.project_id) {
          setProjectId(res.data.project_id);
          setResults(res.data);
        }
      })
      .catch(console.error);
  }, []);

  // Poll database updates during loading
  useEffect(() => {
    let interval;
    if (loading && projectId) {
      interval = setInterval(() => {
        fetchResults(projectId);
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [loading, projectId]);

  // Standard sequential UI run
  const processVideo = async () => {
    if (!url) {
      alert("Please enter a YouTube URL");
      return;
    }

    try {
      setLoading(true);
      setStatus("Initializing project...");

      // 1. Download
      setStatus("Downloading Video...");
      const dlRes = await API.post("/download", { url });
      const currentProjId = dlRes.data.project_id;
      setProjectId(currentProjId);
      setUrl("");

      // 2. Transcribe
      setStatus("Transcribing Video...");
      await API.post("/transcribe", { project_id: currentProjId });

      // 3. Highlights
      setStatus("Finding Engagement Highlights...");
      await API.post("/highlights", { project_id: currentProjId });
      await fetchResults(currentProjId);

      // 4. Refine
      setStatus("Refining Sentence Boundaries...");
      await API.post("/refine-highlights", { project_id: currentProjId });
      await fetchResults(currentProjId);

      // 5. Generate Landscape Clips
      setStatus("Generating Landscape Clips...");
      await API.post("/generate-clips", { project_id: currentProjId });
      await fetchResults(currentProjId);

      // 6. Metadata
      setStatus("Generating Viral Titles & Social Captions...");
      await API.post("/generate-metadata", { project_id: currentProjId });

      // 7. Subtitles
      if (!hasCaptions) {
        setStatus("Creating Captions...");
        await API.post("/generate-captions", { project_id: currentProjId });

        setStatus("Burning Captions...");
        await API.post("/burn-captions", { project_id: currentProjId });
      }

      // 8. Convert to Vertical
      setStatus("Generating Vertical Shorts...");
      await API.post("/vertical-shorts", { project_id: currentProjId });

      setStatus("Completed Successfully ✅");
      await fetchResults(currentProjId);

    } catch (error) {
      console.error(error);
      setStatus("Something went wrong ❌");
    }
    setLoading(false);
  };

  // Mock Copilot chat automation (Triggers backend routes dynamically!)
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput;
    setChatMessages((prev) => [...prev, { sender: "user", text: userText }]);
    setChatInput("");

    // Look for YouTube URLs
    const ytRegex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/[^\s]+/i;
    const match = userText.match(ytRegex);

    if (match) {
      const videoUrl = match[0];
      setChatMessages((prev) => [
        ...prev,
        { sender: "bot", text: `I found a video URL! Let me download and queue this video into MongoDB...` }
      ]);
      try {
        setLoading(true);
        setStatus("Downloading via Chat...");
        const dlRes = await API.post("/download", { url: videoUrl });
        const currentId = dlRes.data.project_id;
        setProjectId(currentId);
        
        setChatMessages((prev) => [
          ...prev,
          { sender: "bot", text: `Successfully downloaded: "${dlRes.data.title}". Now initiating Whisper transcription (Project ID: ${currentId}).` }
        ]);

        setStatus("Transcribing via Chat...");
        await API.post("/transcribe", { project_id: currentId });

        setChatMessages((prev) => [
          ...prev,
          { sender: "bot", text: `Transcription completed. Finding engage highlights via Gemini...` }
        ]);

        setStatus("Finding Highlights via Chat...");
        await API.post("/highlights", { project_id: currentId });
        await fetchResults(currentId);

        setChatMessages((prev) => [
          ...prev,
          { sender: "bot", text: `Found highlights in database. Running refinement and cropping clips now...` }
        ]);

        setStatus("Refining via Chat...");
        await API.post("/refine-highlights", { project_id: currentId });
        await API.post("/generate-clips", { project_id: currentId });
        await fetchResults(currentId);

        setChatMessages((prev) => [
          ...prev,
          { sender: "bot", text: `Metadata & vertical converter pipeline initiated. The dashboard will automatically populate shortly!` }
        ]);

        setStatus("Converting to Vertical via Chat...");
        await API.post("/generate-metadata", { project_id: currentId });
        await API.post("/generate-captions", { project_id: currentId });
        await API.post("/burn-captions", { project_id: currentId });
        await API.post("/vertical-shorts", { project_id: currentId });
        await fetchResults(currentId);
        
        setStatus("Chat process completed ✅");
        setLoading(false);
      } catch (err) {
        console.error(err);
        setChatMessages((prev) => [
          ...prev,
          { sender: "bot", text: `Sorry, I hit an error during execution: ${err.message}` }
        ]);
        setLoading(false);
      }
    } else {
      // General QA mock responses
      setTimeout(() => {
        let reply = "I'm on it! Let me know if you want to parse another YouTube video URL.";
        if (userText.toLowerCase().includes("status") || userText.toLowerCase().includes("results")) {
          reply = projectId 
            ? `Active project is ${projectId}. I retrieved ${results?.clips?.length || 0} clips in MongoDB.`
            : "No active project. Paste a YouTube URL to create one.";
        } else if (userText.toLowerCase().includes("hello") || userText.toLowerCase().includes("hi")) {
          reply = "Hello there! How can I assist you with your video clips today?";
        }
        setChatMessages((prev) => [...prev, { sender: "bot", text: reply }]);
      }, 800);
    }
  };

  return (
    <div className="layout-container">
      {/* Settings Modal */}
      {showSettings && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <h3>Google Cloud Agent Configuration</h3>
            <form onSubmit={saveSettings}>
              <div className="form-group">
                <label>GCP Agent ID</label>
                <input
                  type="text"
                  placeholder="Enter Agent ID"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>GCP Project ID</label>
                <input
                  type="text"
                  placeholder="Enter GCP Project ID"
                  value={gcpProjectId}
                  onChange={(e) => setGcpProjectId(e.target.value)}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowSettings(false)}>
                  Cancel
                </button>
                <button type="submit">Save Settings</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Workspace (Left Column) */}
      <div className="workspace-panel">
        <header className="workspace-header">
          <div className="logo-group">
            <h1>Orien Studio</h1>
            <span className="badge">MongoDB + Agentic AI</span>
          </div>
          <div className="project-selector">
            <input 
              type="text" 
              placeholder="Load Project ID" 
              value={projectId} 
              onChange={(e) => setProjectId(e.target.value)} 
            />
            <button className="btn-icon" onClick={handleRefresh} title="Fetch Database Results">
              🔄 Load/Refresh
            </button>
          </div>
        </header>

        <main className="hero">
          <h2>Turn Long Videos Into Viral Shorts With AI</h2>
          <p>
            Paste any YouTube video and automatically generate viral clips, 
            captions, and vertical shorts stored directly in MongoDB.
          </p>

          <div className="search-box">
            <input
              type="text"
              placeholder="Paste YouTube URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            />
            <button onClick={processVideo} disabled={loading}>
              {loading ? "Processing..." : "Generate Shorts"}
            </button>
          </div>

          <div className="checkbox">
            <input
              type="checkbox"
              id="captions"
              checked={hasCaptions}
              onChange={() => setHasCaptions(!hasCaptions)}
            />
            <label htmlFor="captions">Video already has captions</label>
          </div>

          {status && <div className="pipeline-status">{status}</div>}

          {results && (
            <div className="results-section">
              <h3>Generated Shorts ({results.clips?.length || 0})</h3>
              
              {results.project && (
                <div className="project-info-card">
                  <h4>{results.project.title}</h4>
                  <p>Creator: {results.project.uploader} | Duration: {results.project.duration}s</p>
                </div>
              )}

              <div className="clips-grid">
                {results.clips?.map((clip, index) => {
                  const videoSrc = getClipUrl(clip.vertical_path || clip.captioned_path || clip.clip_path);
                  return (
                    <div key={index} className="clip-card">
                      <div className="video-container">
                        {videoSrc ? (
                          <video width="260" controls key={videoSrc}>
                            <source src={videoSrc} type="video/mp4" />
                            Your browser does not support the video tag.
                          </video>
                        ) : (
                          <div className="video-placeholder">
                            Clip Rendering (Status: {clip.status})
                          </div>
                        )}
                      </div>

                      <div className="clip-meta">
                        <div className="score-badge">🔥 Score: {clip.score || "N/A"}</div>
                        <h4>{clip.title || `Viral Highlight #${clip.clip_index}`}</h4>
                        <p className="hook-text"><strong>Hook:</strong> "{clip.hook}"</p>
                        <p className="caption-text">{clip.caption}</p>
                        <p className="hashtags">{clip.hashtags?.join(" ")}</p>
                        
                        {videoSrc && (
                          <a href={videoSrc} download target="_blank" rel="noreferrer">
                            <button className="btn-sm">Download MP4</button>
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* AI Copilot Panel (Right Column) */}
      <div className="copilot-sidebar">
        <div className="copilot-header">
          <h3>Orien AI Copilot</h3>
          <button className="btn-settings" onClick={() => setShowSettings(true)} title="GCP Settings">
            ⚙️ Setup GCP Agent
          </button>
        </div>

        <div className="chat-container">
          {/* Render GCP Agent if configured, otherwise render local mock chat */}
          {agentId && gcpProjectId ? (
            <div className="gcb-agent-wrapper">
              <gcb-web-agent-chat
                agent-id={agentId}
                project-id={gcpProjectId}
                chat-title="Orien AI Copilot"
              ></gcb-web-agent-chat>
            </div>
          ) : (
            <>
              <div className="chat-log">
                {chatMessages.map((msg, index) => (
                  <div key={index} className={`chat-message ${msg.sender}`}>
                    <div className="message-bubble">{msg.text}</div>
                  </div>
                ))}
              </div>
              <form onSubmit={handleSendMessage} className="chat-input-form">
                <input
                  type="text"
                  placeholder="Paste URL or ask a question..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                />
                <button type="submit">Send</button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;