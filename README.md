# T3.chat Clone

A modern, full-stack AI chat application built with **FastAPI** and **Next.js**. This project replicates the core functionality of advanced chat interfaces, featuring multi-model support, conversation history, and a premium UI.

## 🚀 Features

### Backend
-   **FastAPI**: High-performance async API.
-   **LangGraph & LangChain-Groq**: Advanced orchestration for AI agents.
-   **MongoDB**: Persistent storage for chat history and user data.
-   **Memory**:
    -   *Short-term*: Conversation context retention.
    -   *Long-term*: User preference and fact recall.
-   **Multi-Model Support**: Seamless switching between different Groq LLMs.

### Frontend
-   **Next.js 16**: Latest React framework for server-side rendering and static generation.
-   **React 19**: Cutting-edge UI library.
-   **TailwindCSS 4**: Utility-first styling.
-   **Shadcn/UI**: Accessible and customizable component library.
-   **Lucide React**: Beautiful, consistent icons.
-   **Dark Mode**: Built-in theme toggler.
-   **Markdown Support**: Rich text rendering for AI responses.

## 🛠️ Getting Started

### Prerequisites
-   Python 3.10+
-   Node.js 18+
-   MongoDB Instance (Local or Atlas)
-   Groq API Key

### Backend Setup
1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Set up environment variables in `.env` (see `.env.example`).
5.  Run the server:
    ```bash
    uvicorn main:app --reload --port 8000
    ```

### Frontend Setup
1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
4.  Open [http://localhost:3000](http://localhost:3000) in your browser.

## 🗺️ Roadmap (Coming Soon)

We are actively working on the following features to enhance the T3.chat experience:

-   [ ] **Web Search**: Real-time browsing capabilities for up-to-date information.
-   [ ] **RAG Tool**: Retrieval-Augmented Generation for chatting with your own documents.
-   [ ] **Redis Caching**: High-performance caching for faster response times.
-   [ ] **Image Generation**: Create images directly within the chat interface.
-   [ ] **Voice Mode**:
    -   *Speech-to-Text (STT)*: Dictate your prompts.
    -   *Text-to-Speech (TTS)*: Hear the AI's responses.
