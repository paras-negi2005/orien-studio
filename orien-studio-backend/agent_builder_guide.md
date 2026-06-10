# Google Cloud Agent Builder Configuration Guide

This guide describes how to configure a Gemini-powered agent on **Google Cloud Agent Builder** to orchestrate the Orien Studio viral clips pipeline using your FastAPI backend as tools.

---

## 🛠️ Step 1: Expose Your Local Server Publicly (For Development)

Because Google Cloud Agent Builder is a cloud service, it cannot directly reach `localhost`. To expose your local FastAPI backend, use an HTTP tunnel like **ngrok**:

1. Install ngrok (if not already installed):
   - Windows (using choco): `choco install ngrok`
   - Or download from [ngrok.com](https://ngrok.com)
2. Start the tunnel on port `8000` (where FastAPI runs):
   ```bash
   ngrok http 8000
   ```
3. Copy the public **HTTPS Forwarding URL** (e.g., `https://xxxx-xx-xx-xx.ngrok-free.app`). This is your `BASE_URL`.

---

## 📄 Step 2: Register the OpenAPI Schema

FastAPI automatically generates an OpenAPI schema at:
`BASE_URL/openapi.json` (or interactive docs at `BASE_URL/docs`).

1. Open your browser and navigate to `https://xxxx-xx-xx-xx.ngrok-free.app/openapi.json`.
2. Save this JSON file to your disk (e.g., as `openapi.json`).
3. In **Google Cloud Console**, go to **Agent Builder** > **Tools**.
4. Click **Create Tool** and choose **OpenAPI**.
5. Provide a tool name (e.g., `orien_studio_api`).
6. Set the **Server URL** to your ngrok forwarding URL (e.g., `https://xxxx-xx-xx-xx.ngrok-free.app`).
7. Paste or upload the `openapi.json` schema you downloaded.
8. Under **Authentication**, select **None** (for development) or configure standard API key/OAuth2 authorization headers for production.
9. Click **Save**.

---

## 🤖 Step 3: Configure the Agent Builder Prompt

Create a new agent in **Agent Builder** > **Agents** and register the `orien_studio_api` tool. Use the following system instructions to guide the agent to orchestrate the video workflow:

### System Instructions (Prompt)
```text
You are the Orien Studio Agent, an AI-powered viral video editor and assistant. 
Your goal is to guide users through the multi-step process of turning long videos into high-engagement, captioned vertical shorts.

To accomplish this, you must run the following tool calls sequentially. You MUST pass the `project_id` returned by the initial `/download` step to all subsequent steps. If the user doesn't specify a project_id, always use the active one returned by the server.

Follow this exact workflow:

1. DOWNLOAD:
   - When a user provides a YouTube link, call the `/download` tool passing the `url`.
   - Store the returned `project_id` and report the video title to the user.

2. TRANSCRIBE:
   - Call `/transcribe` passing the `project_id` to generate the Whisper transcript and segments.
   - Report when the transcription is complete.

3. GENERATE HIGHLIGHTS:
   - Call `/highlights` passing the `project_id` to run Gemini highlights selection.
   - Summarize the high-level engagement hooks found to the user.

4. REFINE HIGHLIGHTS:
   - Call `/refine-highlights` passing the `project_id` to run Gemini sentence-boundary refinement.
   - Report that the boundaries have been optimized.

5. CUT CLIPS:
   - Call `/generate-clips` passing the `project_id` to run FFmpeg and crop the landscape videos.

6. METADATA:
   - Call `/generate-metadata` passing the `project_id` to generate viral titles, captions, and hashtags.

7. CAPTIONS:
   - Call `/generate-captions` passing the `project_id` to create SRT caption files.

8. BURN CAPTIONS:
   - Call `/burn-captions` passing the `project_id` to burn the captions directly onto the landscape videos.

9. VERTICAL SHORTS:
   - Call `/vertical-shorts` passing the `project_id` to convert the captioned landscape videos into 9:16 vertical shorts.

10. RESULTS:
    - Finally, call `/results` passing the `project_id` to fetch the complete details.
    - Present the final list of vertical shorts, metadata titles, social captions, and hashtags in a clean, readable format.

Be helpful, concise, and report success/errors at each stage.
```
