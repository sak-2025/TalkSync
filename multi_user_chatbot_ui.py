import streamlit as st
from langchain_core.messages import HumanMessage
#from chatbot_langgraph import app
from chatbot_with_tools import app ,retireve_all_threads
import uuid

# --------------- utility methods -----------

def generate_thread_ID():
    return str(uuid.uuid4())[:8]  # shorter for display

def reset():
    thread_id = generate_thread_ID()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    add_thread(thread_id)


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    state = app.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])  # if nothing return empty list

# -------------------- session -------------------------

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_ID()
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retireve_all_threads()

add_thread(st.session_state['thread_id'])

# ------------- Sidebar UI -----------------

st.sidebar.title("Ai Chatbot ")

if st.sidebar.button("📝 New Chat", use_container_width=True):
    reset()

st.sidebar.markdown("---")
st.sidebar.header("🗂 Chats..")

# Helper: create a label 
def get_thread_label(thread_id):
    messages = load_conversation(thread_id)
    if messages:
        first_msg = messages[0].content[:35] + "..." if len(messages[0].content) > 35 else messages[0].content
        label = f" {first_msg}"
    else:
        label = None
    return label

# Show chat threads (latest first)
for thread_id in st.session_state['chat_threads'][::-1]:
    label = get_thread_label(thread_id)
    if label:
     if st.sidebar.button(label, key=f"thread_{thread_id}", use_container_width=True):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        temp_messages = []

        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages

st.sidebar.markdown("---")
st.sidebar.caption("Powered by LangGraph + Streamlit")


# ----------------------- Main Chat Window -----------------

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
user_input = st.chat_input("Type here")

if user_input:
 
    # Display user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Stream AI response
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in app.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    # Save AI message to history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
