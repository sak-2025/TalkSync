import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from chatbot_with_tools import app ,retireve_all_threads # Assumes import from the backend file

import uuid

# --------------- utility methods -----------

def generate_thread_ID():
    """Generates a shorter unique ID for thread identification."""
    return str(uuid.uuid4())[:8]

def reset():
    """Resets the current chat session to a new thread."""
    thread_id = generate_thread_ID()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_thread(thread_id)


def add_thread(thread_id):
    """Adds a new thread ID to the sidebar list if it doesn't exist."""
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    """Loads the raw message history from the LangGraph checkpointer for a given thread."""
    state = app.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


# -------------------- session -------------------------

# Initialize session state variables
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_ID()
if 'chat_threads' not in st.session_state:
    # Load all existing thread IDs from the database
    st.session_state['chat_threads'] = retireve_all_threads() 

# Ensure the current thread ID is in the sidebar list
add_thread(st.session_state['thread_id'])

# ------------- Sidebar UI -----------------

st.sidebar.title("TalkSync - AI Chatbot")

if st.sidebar.button("📝 New Chat", use_container_width=True):
    reset()

st.sidebar.markdown("---")
st.sidebar.header("🗂 Chats..")

# Helper: create a label 
def get_thread_label(thread_id):
    messages = load_conversation(thread_id)
    if messages:
        # Find the content of the first HumanMessage to use as a label
        first_human_msg = next((msg.content for msg in messages if isinstance(msg, HumanMessage)), None)
        if first_human_msg:
            first_msg = first_human_msg[:35] + "..." if len(first_human_msg) > 35 else first_human_msg
            return f" {first_msg}"
    return None

# Show chat threads (latest first)
for thread_id in st.session_state['chat_threads'][::-1]:
    label = get_thread_label(thread_id)
    if label:
       if st.sidebar.button(label, key=f"thread_{thread_id}", use_container_width=True):
         st.session_state['thread_id'] = thread_id
         messages = load_conversation(thread_id)
         temp_messages = []

         # FIX: Filter internal LangGraph messages when loading history
         for msg in messages:
             # Only show Human messages
             if isinstance(msg, HumanMessage):
                 temp_messages.append({'role': 'user', 'content': msg.content})
             
             # Only show Assistant messages that have actual content
             elif isinstance(msg, AIMessage) and msg.content:
                 temp_messages.append({'role': 'assistant', 'content': msg.content})

         st.session_state['message_history'] = temp_messages
         st.rerun() # Force rerun to update the main chat window

st.sidebar.markdown("---")
st.sidebar.caption("Powered by LangGraph + Streamlit")


# ----------------------- Main Chat Window -----------------


# Render history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type here")

if user_input:
    # Show user's message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # AI streaming block
    with st.chat_message("assistant"):

        status_holder = {"box": None}

        def ai_only_stream():
            full_response = ""
            for chunk in app.stream( # Iterate over chunks (either tuple or message object)
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                
                # FIX for TypeError: Check if the yielded item is a tuple before indexing
                if isinstance(chunk, tuple):
                    message_chunk = chunk[0]
                else:
                    message_chunk = chunk
                
              
                if isinstance(message_chunk, AIMessage) and message_chunk.tool_calls:
                    tool_name = message_chunk.tool_calls[0]['name']
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Agent is calling tool: `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using Tool  `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens (AIMessage or AIMessageChunk with content)
                if isinstance(message_chunk, (AIMessage, AIMessageChunk)) and message_chunk.content:
                    full_response += message_chunk.content
                    yield message_chunk.content
                
            # st.write_stream captures the final return value
            return full_response


        ai_message = st.write_stream(ai_only_stream) 

        if status_holder["box"] is not None:
            # Complete the status box after the full response is streamed
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
            
    # Save the final AI message to session history
    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )
    st.rerun()