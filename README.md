**TalkSync — Multi-User AI Chat with Memory and Tools**

TalkSync is an intelligent, multi-user chatbot platform powered by LangChain, LangGraph, OpenAI, and SQLite — designed for persistent, tool-augmented conversations.
Each user gets a personalized AI chat experience that remembers context, demonstrating production-ready LLM integration with external APIs, and evolves over time.

## Key Features
- **Multi-Threaded Conversations**: Supports multiple chat threads with persistent message storage using SQLite.
- **Integrated Tools**:
  - **Tavily Search** (preferred) or **DuckDuckGo** fallback for real-time information retrieval.
  - **Stock Price Lookup** via AlphaVantage API for accurate market data.
- **LLM-Powered Responses**: Utilizes `ChatOpenAI` (GPT-4o-mini) with tool invocation to provide context-aware answers.
- **Streamlit Interface**: Intuitive and responsive UI with sidebar thread management.
- **Persistent Storage**: Conversation history maintained using `SqliteSaver`.
- **Real-Time Response Streaming**: Delivers AI responses in a dynamic, streaming format.

## Technology Stack
- **Backend**: Python, LangChain, LangGraph, SQLite
- **LLM**: OpenAI GPT-4o-mini
- **Tools**: Tavily Search, DuckDuckGo, AlphaVantage Stock API
- **Frontend**: Streamlit

## Installation
git clone https://github.com/sak-2025/TalkSync-Multi-User-AI-Chat-with-Memory-and-Tools.git

cd TalkSync

pip install -r requirements.txt
