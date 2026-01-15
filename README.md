# T3.chat Clone - Advanced AI Chat Application

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16.1.1-black?style=for-the-badge&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/React-19.2.3-61DAFB?style=for-the-badge&logo=react" alt="React"/>
  <img src="https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/LangGraph-Latest-blue?style=for-the-badge" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/Groq-LPU-orange?style=for-the-badge" alt="Groq"/>
  <img src="https://img.shields.io/badge/Tavily-Search-purple?style=for-the-badge" alt="Tavily"/>
  <img src="https://img.shields.io/badge/Ollama-Embeddings-green?style=for-the-badge" alt="Ollama"/>
</p>

A full-stack AI chat application inspired by [T3.chat](https://t3.chat). Built with **Next.js 16** (App Router) and **FastAPI**, featuring:
- **Web Search** via Tavily API for real-time information
- **RAG (Retrieval-Augmented Generation)** for PDF document Q&A
- **Persistent Memory System** that learns about users over time
- **Multi-model Support** via Groq's ultra-fast LPU inference
- **Real-time Streaming** responses via SSE

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Architecture Overview](#-architecture-overview)
- [System Design Deep Dive](#-system-design-deep-dive)
- [Tool System (Search & RAG)](#-tool-system-search--rag)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Component Hierarchy](#-component-hierarchy)
- [Data Flow](#-data-flow)
- [API Reference](#-api-reference)
- [Memory System](#-memory-system)
- [MongoDB Collections](#-mongodb-collections)
- [Setup & Installation](#-setup--installation)
- [Environment Variables](#-environment-variables)
- [Development](#-development)
- [Available Models](#-available-models)
- [UI Features](#-ui-features)

---

## 🚀 Key Features

### 🔍 Web Search Tool (Tavily)

Real-time web search integration for current information queries.

| Feature | Description |
|---------|-------------|
| **Tavily API** | Uses httpx to call Tavily's advanced search with answer generation |
| **Smart Auto-Detection** | Automatically detects queries needing search (dates, news, prices, events) |
| **Manual Toggle** | Users can force search via the search button in the input area |
| **Article Reader** | Fetches full content from top URLs for detailed extraction |
| **Source Citations** | Responses include URLs and source attribution |
| **Confidence Scoring** | Sources rated HIGH/MEDIUM/LOW based on domain reputation |

### 📄 RAG Tool (PDF Q&A)

Upload PDFs and ask questions about their content within a specific chat.

| Feature | Description |
|---------|-------------|
| **PDF Upload** | Drag-and-drop or click to upload PDF files |
| **Text Extraction** | Uses `pdfplumber` for accurate text extraction |
| **Chunking** | Custom text splitting with sentence boundary detection (1000 chars, 200 overlap) |
| **Embeddings** | Ollama's `nomic-embed-text` model for vectorization |
| **Vector Storage** | MongoDB stores embeddings alongside chunks |
| **Similarity Search** | Cosine similarity for relevant chunk retrieval |
| **Per-Chat Scope** | Documents are scoped to individual conversations |

### 🧠 Adaptive Memory System

Unlike standard chatbots that forget you after a session, this application maintains a **long-term memory** of user facts and preferences.

| Feature | Description |
|---------|-------------|
| **Automatic Fact Extraction** | A lightweight LLM (`llama-3.1-8b-instant`) extracts personal facts after each conversation |
| **Smart Deduplication** | Three-tier strategy: exact matching, substring containment, token overlap (≥80%) |
| **Context Injection** | Relevant memories automatically injected into the system prompt |
| **Manual Memory Management** | Users can view, add, and delete memories through Settings modal |
| **Core Facts from Settings** | User profile info stored as `core_fact` type memories |

### ⚡ Real-Time Streaming (SSE)

| Feature | Description |
|---------|-------------|
| **Protocol** | Server-Sent Events (SSE) via `sse-starlette` |
| **Tool Metadata** | Stream includes `tool_metadata` indicating search/RAG usage |
| **Robust Parsing** | Custom SSE parser handles Windows line endings, multi-line data, event types |
| **Optimized Rendering** | `React.memo()` on `MarkdownRenderer` prevents re-renders |
| **Smart Auto-Scroll** | Pauses when user scrolls up, resumes when near bottom |

### 🤖 Multi-Model Intelligence

| Feature | Description |
|---------|-------------|
| **Groq LPU** | Near-instant inference via Groq's Language Processing Unit |
| **Dynamic Model Selection** | Switch models mid-session via dropdown |
| **Default Model** | `meta-llama/llama-4-maverick-17b-128e-instruct` |
| **8 Available Models** | See [Available Models](#-available-models) section |

### 🔐 Authentication & Personalization

| Feature | Description |
|---------|-------------|
| **Clerk Integration** | Full authentication via `@clerk/nextjs` |
| **Protected Actions** | Chat/upload requires authentication |
| **User Settings** | "About You" panel for nickname, occupation, and bio |
| **Conversation History** | Persistent conversations grouped by date |

### 🎨 Theme Support

| Feature | Description |
|---------|-------------|
| **Dark/Light Mode** | System-aware theming with manual toggle |
| **Smooth Transitions** | CSS transitions on theme change |

---

## 🏗️ Architecture Overview

The application follows a **decoupled client-server architecture** with tool integration.

```mermaid
graph TB
    subgraph Client["Frontend - Next.js 16"]
        direction TB
        UI["React UI Components"]
        Context["ChatContext Provider"]
        API_Client["API Client - Fetch + SSE"]
        Auth["Clerk Authentication"]
    end

    subgraph Server["Backend - FastAPI"]
        direction TB
        Routes["API Routes"]
        
        subgraph Agent["LangGraph Agent"]
            LoadMem["load_memory"]
            LoadTools["load_tool_context"]
            Generate["generate_response"]
            Extract["extract_memories"]
        end
        
        subgraph Tools["Tool System"]
            SearchTool["SearchTool - Tavily"]
            ReaderTool["ReaderTool - Article Fetcher"]
            RAGRetriever["RAGRetriever"]
        end
        
        MemMgr["MemoryManager"]
        RAGStore["RAGStore - GridFS + Chunks"]
    end

    subgraph External["External Services"]
        MongoDB[("MongoDB Atlas")]
        Groq["Groq Cloud API"]
        Tavily["Tavily Search API"]
        Ollama["Ollama Embeddings"]
        ClerkAPI["Clerk API"]
    end

    UI --> Context
    Context --> API_Client
    Auth --> ClerkAPI
    API_Client -->|"REST/SSE"| Routes
    Routes --> Agent
    LoadMem --> MemMgr
    LoadTools --> Tools
    SearchTool --> Tavily
    RAGRetriever --> RAGStore
    RAGStore --> Ollama
    Generate -->|"Streaming"| Groq
    Extract --> MemMgr
    MemMgr --> MongoDB
    RAGStore --> MongoDB
```

---

## 🔬 System Design Deep Dive

### Request-Response Lifecycle with Tools

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Frontend
    participant FastAPI
    participant LangGraph
    participant Tools
    participant Tavily
    participant RAGStore
    participant Groq
    participant MongoDB

    User->>Frontend: Send Message + Toggle Search
    Frontend->>FastAPI: POST /api/chat/stream with tool_mode
    FastAPI->>LangGraph: stream_chat()
    
    rect rgb(240, 248, 255)
        Note over LangGraph: Step 1 - Load Memory
        LangGraph->>MongoDB: Query memory_store
        MongoDB-->>LangGraph: User memories
    end

    rect rgb(255, 240, 245)
        Note over LangGraph: Step 2 - Load Tool Context
        LangGraph->>Tools: get_tool_context()
        
        alt Search Enabled
            Tools->>Tavily: Search query
            Tavily-->>Tools: Search results + answer
            Tools->>Tools: ReaderTool fetches top URLs
        end
        
        alt RAG Documents Exist
            Tools->>RAGStore: retrieve(query, conversation_id)
            RAGStore->>MongoDB: Query rag_chunks with embeddings
            MongoDB-->>RAGStore: Relevant chunks
            RAGStore-->>Tools: Formatted RAG context
        end
        
        Tools-->>LangGraph: Combined tool context
    end

    rect rgb(255, 248, 240)
        Note over LangGraph: Step 3 - Generate Response
        LangGraph->>Groq: astream() with tools context
        loop Token Stream
            Groq-->>LangGraph: Token chunk
            LangGraph-->>FastAPI: yield chunk
            FastAPI-->>Frontend: SSE event=message
            Frontend-->>User: Update message
        end
    end

    rect rgb(240, 255, 240)
        Note over LangGraph: Step 4 - Extract Memories
        LangGraph->>Groq: Extract facts with llama-3.1-8b
        Groq-->>LangGraph: JSON facts array
        LangGraph->>MongoDB: Store new facts
    end

    FastAPI->>MongoDB: Save conversation
    FastAPI-->>Frontend: SSE event=done with tool_metadata
    Frontend-->>User: Show tool usage indicators
```

### LangGraph State Machine

The backend uses LangGraph's `StateGraph` with a `ChatState` TypedDict:

```python
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation history
    user_id: str                              # User identifier
    model_name: str                           # Selected LLM model
    memory_context: str                       # Formatted memories
    last_user_message: str                    # For extraction
    last_assistant_response: str              # For extraction
    tool_context: str                         # Search/RAG results
    tool_mode: str                            # auto/search/none
    use_rag: bool                             # Whether to use RAG
    conversation_id: str                      # Thread ID
    tool_metadata: dict                       # {search_used, rag_used, ...}
```

```mermaid
stateDiagram-v2
    [*] --> load_memory: START
    load_memory --> load_tool_context: Memory Context Ready
    load_tool_context --> generate_response: Tool Context Ready
    generate_response --> extract_memories: Response Complete
    extract_memories --> [*]: END

    state load_memory {
        [*] --> QueryMemoryStore
        QueryMemoryStore --> FormatMemoryContext
        FormatMemoryContext --> [*]
    }

    state load_tool_context {
        [*] --> CheckToolMode
        CheckToolMode --> RunSearch: search or auto_detected
        CheckToolMode --> CheckRAG: no search needed
        RunSearch --> FetchArticles: Get detailed content
        FetchArticles --> CheckRAG
        CheckRAG --> RetrieveChunks: has documents
        CheckRAG --> CombineContext: no documents
        RetrieveChunks --> CombineContext
        CombineContext --> [*]
    }

    state generate_response {
        [*] --> BuildSystemPrompt
        BuildSystemPrompt --> InjectToolContext
        InjectToolContext --> StreamFromGroq
        StreamFromGroq --> [*]
    }

    state extract_memories {
        [*] --> AnalyzeConversation
        AnalyzeConversation --> DeduplicateAndSave
        DeduplicateAndSave --> [*]
    }
```

---

## 🔧 Tool System (Search & RAG)

### Search Tool Architecture

```mermaid
flowchart TB
    subgraph Input["User Query"]
        Query["Message + tool_mode"]
    end

    subgraph Detection["Search Detection"]
        AutoDetect{"Auto-detect<br/>patterns?"}
        ForceSearch{"tool_mode<br/>= search?"}
    end

    subgraph SearchTool["SearchTool Class"]
        TavilyAPI["Tavily API via httpx"]
        RetryLogic["Retry Logic - 2 attempts"]
        ConfidenceScore["Score sources HIGH/MED/LOW"]
    end

    subgraph ReaderTool["ReaderTool Class"]
        FetchURL["Fetch top 2 URLs"]
        ParseHTML["BeautifulSoup parsing"]
        ExtractContent["Extract article content"]
    end

    subgraph Output["Search Context"]
        Results["Formatted results with URLs"]
        Instructions["Grounding instructions for LLM"]
    end

    Query --> ForceSearch
    ForceSearch -->|Yes| SearchTool
    ForceSearch -->|No| AutoDetect
    AutoDetect -->|Yes| SearchTool
    AutoDetect -->|No| Skip["Skip Search"]
    
    SearchTool --> TavilyAPI
    TavilyAPI --> RetryLogic
    RetryLogic --> ConfidenceScore
    ConfidenceScore --> ReaderTool
    ReaderTool --> FetchURL
    FetchURL --> ParseHTML
    ParseHTML --> ExtractContent
    ExtractContent --> Results
    Results --> Instructions
```

### Search Auto-Detection Patterns

```python
SEARCH_INDICATORS = [
    # Time-sensitive
    r"\b(today|yesterday|this week|current|latest|recent|now|202[0-9])\b",
    
    # Events and schedules  
    r"\b(when is|when's|when will|what date|exact date)\b",
    r"\b(next|upcoming|scheduled|event|fight|match|game)\b",
    r"\b(ufc|nfl|nba|mlb|premier league)\b",
    
    # Real-time info
    r"\b(weather|forecast|temperature)\b.*\b(in|at|for)\b",
    r"\b(stock|share|market|trading)\b.*\b(price|value)\b",
    r"\b(news|headlines|latest)\b",
    
    # Search-like queries
    r"\b(search|look up|find|google|check)\b",
]

NO_SEARCH_INDICATORS = [
    r"\b(explain|teach me|how does .* work|what is the concept)\b",
    r"\b(write|create|generate|make|code|implement)\b",
    r"\b(translate|summarize|rewrite)\b",
    r"\b(my|our|we|I)\b.*(document|pdf|file|upload)",
]
```

### Tool Grounding Instructions

When tools return results, the LLM receives strict instructions to prevent generic responses:

```
=== CRITICAL: TOOL RESULTS PROVIDED - YOU MUST USE THEM ===

1. USE THE DATA: Extract specific facts, dates, names from the results
2. CITE SOURCES: Include source URLs in format [Source Name](URL)
3. BE SPECIFIC: Include exact dates, times, locations found
4. NO GENERIC RESPONSES: Don't say "check the website" - results ARE current
5. ACKNOWLEDGE LIMITATIONS: If results don't have the answer, say what IS available

FORBIDDEN RESPONSES:
- "I recommend checking [website] for the latest information"
- "I don't have access to real-time data"
- "As of my knowledge cutoff..."
```

### RAG Pipeline Architecture

```mermaid
flowchart TB
    subgraph Upload["PDF Upload Flow"]
        PDF["PDF File"]
        Extract["pdfplumber.extract_text()"]
        Chunk["Custom chunking with sentence boundaries"]
        Embed["OllamaEmbeddings - nomic-embed-text"]
        StoreChunks["Store chunks + embeddings"]
        StoreFile["Store PDF in GridFS"]
    end

    subgraph Query["Query Flow"]
        UserQuery["User Question"]
        QueryEmbed["Embed query with Ollama"]
        FetchChunks["Fetch all conversation chunks"]
        CalcSim["Calculate cosine similarity"]
        TopK["Sort and get top K"]
        Filter["Filter score > 0.3"]
        Format["Format RAG context"]
    end

    subgraph Storage["MongoDB Collections"]
        RagDocs["rag_documents"]
        RagChunks["rag_chunks"]
        RagFiles["rag_files GridFS"]
    end

    PDF --> Extract
    Extract --> Chunk
    Chunk --> Embed
    Embed --> StoreChunks
    PDF --> StoreFile
    StoreChunks --> RagChunks
    StoreFile --> RagFiles

    UserQuery --> QueryEmbed
    QueryEmbed --> FetchChunks
    FetchChunks --> RagChunks
    RagChunks --> CalcSim
    CalcSim --> TopK
    TopK --> Filter
    Filter --> Format
```

### RAG Storage Schema

```python
# rag_documents collection - Document metadata
{
    "_id": "document_uuid",           # Unique document ID
    "filename": "report.pdf",         # Original filename
    "user_id": "clerk_user_id",       # Owner
    "conversation_id": "conv_uuid",   # Scoped to conversation
    "file_id": ObjectId("..."),       # GridFS reference
    "chunk_count": 15,                # Number of chunks
    "text_length": 12500,             # Total characters
    "created_at": datetime            # Upload timestamp
}

# rag_chunks collection - Text chunks with embeddings
{
    "_id": "doc_uuid_chunk_0",         # Composite ID
    "document_id": "doc_uuid",         # Parent document
    "conversation_id": "conv_uuid",    # For efficient querying
    "user_id": "clerk_user_id",        # Owner
    "chunk_index": 0,                  # Order in document
    "text": "chunk text content...",   # Actual text
    "embedding": [0.123, -0.456, ...], # 768-dim nomic-embed-text vector
    "created_at": datetime             # Creation timestamp
}

# Retrieval uses cosine similarity:
# score = dot(query_embedding, chunk_embedding) / (||query|| * ||chunk||)
# Chunks with score > 0.3 are included in context
```

---

## 🛠️ Technology Stack

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.1.1 | React framework with App Router |
| **React** | 19.2.3 | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 4.1.18 | Utility-first styling |
| **Radix UI** | Latest | Accessible UI primitives |
| **Clerk** | 6.36.7 | Authentication |
| **next-themes** | 0.4.6 | Dark/Light mode theming |
| **Lucide React** | 0.562.0 | Icon library |
| **react-markdown** | 10.1.0 | Markdown rendering |
| **react-syntax-highlighter** | 16.1.0 | Code syntax highlighting |

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | Latest | Async web framework |
| **Python** | 3.11+ | Runtime |
| **LangGraph** | Latest | Agent workflow orchestration |
| **LangChain** | Latest | LLM abstractions |
| **langchain-groq** | Latest | Groq LLM integration |
| **langchain-ollama** | Latest | Ollama embeddings |
| **Motor** | Latest | Async MongoDB driver |
| **PyMongo** | Latest | Sync MongoDB driver |
| **httpx** | Latest | HTTP client for Tavily |
| **pdfplumber** | Latest | PDF text extraction |
| **beautifulsoup4** | Latest | HTML parsing for articles |
| **tavily-python** | Latest | Tavily search client |
| **SSE-Starlette** | Latest | Server-Sent Events |
| **pydantic-settings** | Latest | Environment management |

### External Services

| Service | Purpose |
|---------|---------|
| **MongoDB Atlas** | Database - conversations, memories, RAG vectors |
| **Groq Cloud** | LLM inference with LPU acceleration |
| **Tavily** | Web search API |
| **Ollama** | Local embeddings (nomic-embed-text) |
| **Clerk** | User authentication |

---

## 📂 Project Structure

```
t3_chat/
├── 📄 README.md                    # This documentation file
│
├── 📁 backend/                     # FastAPI Backend (Python)
│   ├── 📄 main.py                  # FastAPI app, CORS, routers
│   ├── 📄 config.py                # Settings, AVAILABLE_MODELS, env loading
│   ├── 📄 database.py              # MongoDB connection (async + sync)
│   ├── 📄 requirements.txt         # Python dependencies
│   │
│   ├── 📁 agent/                   # LangGraph AI Agent
│   │   ├── 📄 __init__.py          # Exports invoke_chat(), stream_chat()
│   │   ├── 📄 graph.py             # ChatState, nodes, create_chat_graph()
│   │   ├── 📄 llm_provider.py      # get_llm() factory for ChatGroq
│   │   ├── 📄 prompts.py           # SYSTEM_PROMPT, MEMORY_EXTRACTION_PROMPT
│   │   └── 📄 tools.py             # SearchTool, ReaderTool, get_tool_context()
│   │
│   ├── 📁 rag/                     # RAG Subsystem (NEW)
│   │   ├── 📄 __init__.py          # Module exports
│   │   ├── 📄 store.py             # RAGStore - PDF ingestion, chunking, embeddings
│   │   └── 📄 retriever.py         # RAGRetriever - similarity search
│   │
│   ├── 📁 memory/                  # Memory Subsystem
│   │   ├── 📄 manager.py           # MemoryManager with CRUD + deduplication
│   │   ├── 📄 store.py             # get_memory_store() -> MongoDBStore
│   │   ├── 📄 checkpointer.py      # get_checkpointer() -> MongoDBSaver
│   │   └── 📄 cleanup.py           # cleanup_conversation_memory()
│   │
│   ├── 📁 models/                  # Pydantic Schemas
│   │   └── 📄 schemas.py           # ChatRequest (with tool_mode), ChatResponse, etc.
│   │
│   └── 📁 routes/                  # API Endpoints
│       ├── 📄 chat.py              # POST /api/chat, POST /api/chat/stream
│       ├── 📄 conversations.py     # GET/PATCH/DELETE /api/conversations
│       ├── 📄 models.py            # GET /api/models
│       ├── 📄 users.py             # User profile, memories endpoints
│       └── 📄 rag.py               # POST /api/rag/upload, GET/DELETE documents (NEW)
│
└── 📁 frontend/                    # Next.js Frontend (TypeScript)
    ├── 📄 package.json             # Node dependencies
    ├── 📄 next.config.ts           # Next.js configuration
    │
    └── 📁 src/
        ├── 📄 middleware.ts        # Clerk middleware
        │
        ├── 📁 app/                 # Next.js App Router
        │   ├── 📄 layout.tsx       # Root layout with ClerkProvider
        │   ├── 📄 page.tsx         # Home page -> MainLayout
        │   └── 📄 globals.css      # Global Tailwind styles
        │
        ├── 📁 components/          # React Components
        │   ├── 📄 MainLayout.tsx   # App shell (ThemeProvider + ChatProvider)
        │   ├── 📄 ChatArea.tsx     # Chat interface with search/upload buttons (UPDATED)
        │   ├── 📄 Sidebar.tsx      # Conversation list, user profile
        │   ├── 📄 MarkdownRenderer.tsx  # Memoized markdown rendering
        │   ├── 📄 SettingsModal.tsx    # About You + Memory tabs
        │   ├── 📄 LoginPromptModal.tsx # Auth prompt
        │   └── 📁 ui/              # shadcn/ui components
        │
        └── 📁 lib/                 # Utilities & Context
            ├── 📄 api.ts           # API client with RAG functions (UPDATED)
            ├── 📄 chat-context.tsx # ChatProvider with search/RAG state (UPDATED)
            └── 📄 utils.ts         # cn() helper
```

---

## 🧩 Component Hierarchy

```mermaid
graph TD
    subgraph App["Next.js App"]
        Layout["layout.tsx - ClerkProvider"]
        Page["page.tsx"]
    end

    subgraph MainLayout["MainLayout.tsx"]
        ThemeProvider["ThemeProvider"]
        ChatProvider["ChatProvider"]
        Shell["Flex Container"]
    end

    subgraph Sidebar["Sidebar.tsx"]
        NewChatBtn["New Chat Button"]
        SearchInput["Search Input"]
        ConvoList["Conversation List"]
        UserProfile["User Profile"]
        SettingsBtn["Settings Button"]
    end

    subgraph ChatArea["ChatArea.tsx"]
        Header["Theme Toggle"]
        EmptyState["Quick Actions"]
        MessageList["Message List"]
        ToolIndicators["Search/RAG Indicators"]
        InputArea["Input + Controls"]
    end

    subgraph InputControls["Input Area Controls"]
        ModelDropdown["Model Selector"]
        SearchToggle["Search Toggle Button"]
        UploadButton["PDF Upload Button"]
        DocBadge["Document Count Badge"]
        SendButton["Send Button"]
    end

    Layout --> Page
    Page --> MainLayout
    MainLayout --> Shell
    Shell --> Sidebar
    Shell --> ChatArea
    ChatArea --> MessageList
    ChatArea --> ToolIndicators
    ChatArea --> InputArea
    InputArea --> InputControls
```

---

## 🔄 Data Flow

### Frontend State Management

The `ChatContext` provides global state including tool settings:

```typescript
interface ChatContextType {
    // Messages
    messages: Message[];
    isLoading: boolean;
    error: string | null;

    // Conversation
    conversationId: string | null;
    conversations: ConversationSummary[];

    // Model
    selectedModel: string;
    models: ModelInfo[];

    // User
    userId: string;
    isAuthenticated: boolean;

    // Tool Settings (NEW)
    searchEnabled: boolean;
    setSearchEnabled: (enabled: boolean) => void;
    documentCount: number;
    lastToolMetadata: ToolMetadata | null;

    // Actions
    sendChatMessage: (content: string) => Promise<void>;
    startNewChat: () => void;
    selectConversation: (id: string) => Promise<void>;
    deleteConversation: (id: string) => Promise<void>;
    setSelectedModel: (modelId: string) => void;
    uploadDocument: (file: File) => Promise<string | null>;  // NEW
    refreshDocumentCount: () => Promise<void>;  // NEW
}
```

```mermaid
flowchart LR
    subgraph ChatContext["ChatContext State"]
        direction TB
        Messages["messages[]"]
        ConvoId["conversationId"]
        Model["selectedModel"]
        SearchEnabled["searchEnabled"]
        DocCount["documentCount"]
        ToolMeta["lastToolMetadata"]
    end

    subgraph Actions["Actions"]
        SendMsg["sendChatMessage()"]
        ToggleSearch["setSearchEnabled()"]
        UploadDoc["uploadDocument()"]
        NewChat["startNewChat()"]
    end

    subgraph Components["Components"]
        ChatArea["ChatArea"]
        Sidebar["Sidebar"]
    end

    Components -->|"useChat()"| ChatContext
    Components -->|"dispatch"| Actions
    Actions -->|"update"| ChatContext
    Actions -->|"fetch"| API["API Layer"]
```

---

## 📡 API Reference

### Chat Endpoints

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| `POST` | `/api/chat` | Send message, get full response | `ChatRequest` |
| `POST` | `/api/chat/stream` | Send message, stream response (SSE) | `ChatRequest` |

**ChatRequest Schema (Updated):**
```json
{
    "message": "string",
    "user_id": "string",
    "conversation_id": "string | null",
    "model_name": "string | null",
    "tool_mode": "auto | search | none",  // NEW
    "use_rag": true                        // NEW
}
```

**SSE Events from `/api/chat/stream`:**
- `event: message` → `data: <token chunk>`
- `event: done` → `data: {"conversation_id": "...", "model_used": "...", "tool_metadata": {...}}`
- `event: error` → `data: <error message>`

**Tool Metadata:**
```json
{
    "search_used": true,
    "rag_used": false,
    "search_query": "when is next ufc event",
    "rag_chunks": 0
}
```

**Important Implementation Note:**  
The frontend uses a `useRef` pattern (`conversationIdRef`) to handle conversation ID updates across async callbacks:

```typescript
// Prevents stale closure issues where useState doesn't update in time
const conversationIdRef = useRef<string | null>(null);

// Sync ref with state
useEffect(() => {
    conversationIdRef.current = conversationId;
}, [conversationId]);

// In async callbacks, use ref instead of state:
const currentConversationId = conversationIdRef.current;
```

### RAG Endpoints (NEW)

| Method | Endpoint | Description | Body/Params |
|--------|----------|-------------|-------------|
| `POST` | `/api/rag/upload` | Upload PDF document | `multipart/form-data: file, user_id, conversation_id?` |
| `GET` | `/api/rag/documents` | List documents for conversation | `user_id, conversation_id` |
| `DELETE` | `/api/rag/documents/{id}` | Delete document | `user_id` |
| `GET` | `/api/rag/documents/{conversation_id}/count` | Get document count | `user_id` |

**Upload Response:**
```json
{
    "document_id": "uuid",
    "conversation_id": "uuid",
    "filename": "report.pdf",
    "chunk_count": 15,
    "text_length": 12500,
    "message": "Document uploaded and processed successfully"
}
```

### Conversation Endpoints

| Method | Endpoint | Description | Params |
|--------|----------|-------------|--------|
| `GET` | `/api/conversations` | List user conversations | `user_id, limit, offset` |
| `GET` | `/api/conversations/{id}` | Get conversation with messages | `user_id` |
| `PATCH` | `/api/conversations/{id}` | Update title | `user_id` |
| `DELETE` | `/api/conversations/{id}` | Delete conversation | `user_id` |

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users/{id}/about` | Get "About You" settings |
| `PUT` | `/api/users/{id}/about` | Update "About You" |
| `GET` | `/api/users/{id}/memories` | List user memories |
| `DELETE` | `/api/users/{id}/memories/{key}` | Delete specific memory |
| `DELETE` | `/api/users/{id}/memories` | Clear all memories |

### Model Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/models` | List available LLM models |
| `GET` | `/health` | Health check |

---

## 🧠 Memory System

### How Memory Works

```mermaid
flowchart TB
    subgraph Extraction["Automatic Fact Extraction"]
        Conv["Conversation"] --> Analyze["Analyze with llama-3.1-8b"]
        Analyze --> Facts["Extracted Facts"]
    end

    subgraph Dedup["Deduplication"]
        Facts --> Check1{"Exact Match?"}
        Check1 -->|No| Check2{"Substring?"}
        Check2 -->|No| Check3{"Token Overlap >= 80%?"}
        Check3 -->|No| Save["Save to Store"]
    end

    subgraph Usage["Context Injection"]
        Query["New Message"] --> GetMem["Get memories"]
        GetMem --> Format["Format context"]
        Format --> Inject["Inject into prompt"]
    end
```

---

## 🗄️ MongoDB Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `conversations` | Chat history | `_id, user_id, title, messages[], model_name` |
| `memory_store` | Long-term user memories | `namespace, key, value` |
| `user_settings` | User preferences | `_id, nickname, occupation, about` |
| `checkpoints` | LangGraph state | `thread_id, state` |
| `checkpoint_writes` | LangGraph writes | `thread_id, data` |
| `rag_documents` | PDF metadata | `_id, filename, conversation_id, chunk_count` |
| `rag_chunks` | Text chunks + embeddings | `document_id, text, embedding[]` |
| `rag_files.files` | GridFS file metadata | `_id, filename, document_id` |
| `rag_files.chunks` | GridFS binary data | `files_id, data` |

---

## 🚀 Setup & Installation

### Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- **MongoDB Atlas** account (or local MongoDB)
- **Groq API Key** ([Get one here](https://console.groq.com))
- **Tavily API Key** ([Get one here](https://tavily.com))
- **Ollama** running locally with `nomic-embed-text` model
- **Clerk Account** ([Sign up here](https://clerk.com))

### 1. Clone and Setup Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables)
```

### 2. Setup Ollama (for RAG embeddings)

```bash
# Install Ollama from https://ollama.com
# Then pull the embedding model:
ollama pull nomic-embed-text
```

### 3. Setup Frontend

```bash
cd frontend
npm install
# Create .env.local file (see Environment Variables)
```

---

## 🔐 Environment Variables

### Backend `.env`

```env
# Required - Groq API
GROQ_API_KEY=gsk_your_groq_api_key

# Required - Tavily Search
TAVILY_API_KEY=tvly-your_tavily_api_key

# MongoDB Atlas
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DATABASE_NAME=t3_chat

# Ollama Embeddings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# RAG Configuration
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Optional - LangSmith Tracing
LANGSMITH_API_KEY=
LANGSMITH_TRACING=false
```

### Frontend `.env.local`

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

---

## 💻 Development

### Running the Backend

```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

### Running the Frontend

```bash
cd frontend
npm run dev
```

- **App**: http://localhost:3000

---

## 📊 Available Models

All models are served via Groq's LPU infrastructure:

| Model | ID | Context | Best For |
|-------|-----|---------|----------|
| **Llama 4 Maverick** ⭐ | `meta-llama/llama-4-maverick-17b-128e-instruct` | 128K | Complex reasoning (Default) |
| **Llama 4 Scout** | `meta-llama/llama-4-scout-17b-16e-instruct` | 128K | Fast exploration |
| **Qwen 3 32B** | `qwen/qwen3-32b` | 32K | General tasks |
| **Kimi K2** | `moonshotai/kimi-k2-instruct-0905` | 128K | Moonshot AI |
| **GPT OSS 120B** | `openai/gpt-oss-120b` | 128K | Large-scale tasks |
| **Llama 3.3 70B Versatile** | `llama-3.3-70b-versatile` | 128K | Versatile tasks |
| **Llama 3.1 8B Instant** | `llama-3.1-8b-instant` | 128K | Fast responses, fact extraction |
| **Groq Compound** | `groq/compound` | 8K | Compound AI tasks |

⭐ = Default model for chat, Llama 3.1 8B Instant is used for memory extraction

---

## 🎨 UI Features

### Chat Interface

- **Search Toggle**: Blue button when enabled, searches the web
- **Upload Button**: Paperclip icon with document count badge
- **Tool Indicators**: Shows "Web search used" / "X doc chunk(s) used" above assistant messages
- **Model Dropdown**: Switch between LLM models
- **Smart Auto-Scroll**: Pauses when scrolling up

### Visual Design

- **Dark/Light Theme**: System-aware with manual toggle
- **Pink Accent Color**: User messages and primary buttons
- **Glassmorphism**: Backdrop blur effects
- **Responsive**: Collapsible sidebar for mobile

---

## 📝 License

This project is for educational purposes.

---

<p align="center">
  Built with Next.js 16, FastAPI, LangGraph, Groq, Tavily, and Ollama
</p>
