import os
import time
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from hindsight_helper import HindsightMemoryManager
from llm_helper import GroqLLMManager
from demo_data import DEMO_CUSTOMERS, load_demo_customer_memories

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & DARK THEME CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SupportWise AI — AI Support Agent with Hindsight Memory",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Dark Theme Core Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Container */
    .main-header {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .main-header h1 {
        background: linear-gradient(90deg, #a78bfa, #818cf8, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0 0 6px 0;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin: 0;
    }
    
    /* Custom Memory Badges */
    .badge-memory {
        background: linear-gradient(90deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.25));
        border: 1px solid rgba(139, 92, 246, 0.5);
        color: #c084fc;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-online {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Memory Recall Box */
    .memory-panel {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-left: 5px solid #8b5cf6;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 12px 0 20px 0;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.15);
    }
    .memory-panel-title {
        color: #c084fc;
        font-weight: 700;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .memory-item {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 6px;
        font-size: 0.9rem;
        color: #e2e8f0;
    }
    
    /* Customer Card in Sidebar */
    .customer-card {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .customer-card h4 {
        margin: 0 0 6px 0;
        color: #f1f5f9;
        font-size: 1.1rem;
    }
    .customer-card p {
        margin: 2px 0;
        color: #94a3b8;
        font-size: 0.85rem;
    }

    /* Buttons styling */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION & ISOLATION MANAGEMENT
# -----------------------------------------------------------------------------
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")

if "hindsight_api_key" not in st.session_state:
    st.session_state.hindsight_api_key = os.getenv("HINDSIGHT_API_KEY", "")

if "hindsight_base_url" not in st.session_state:
    st.session_state.hindsight_base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")

if "selected_customer_id" not in st.session_state:
    st.session_state.selected_customer_id = "CUST-1001"

if "current_customer_id" not in st.session_state:
    st.session_state.current_customer_id = st.session_state.selected_customer_id

# Customer-keyed dictionaries for strict data isolation
if "messages" not in st.session_state or not isinstance(st.session_state.messages, dict):
    st.session_state.messages = {}

if "last_recalled_memories" not in st.session_state or not isinstance(st.session_state.last_recalled_memories, dict):
    st.session_state.last_recalled_memories = {}

# Helper to lazy-load managers
@st.cache_resource
def get_hindsight_manager(api_key: str, base_url: str):
    return HindsightMemoryManager(api_key=api_key, base_url=base_url)

memory_mgr = get_hindsight_manager(st.session_state.hindsight_api_key, st.session_state.hindsight_base_url)
llm_mgr = GroqLLMManager(api_key=st.session_state.groq_api_key)


# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & METADATA
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; padding: 4px 0 12px 0;">
        <div style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35); flex-shrink: 0;">
            🧠
        </div>
        <div>
            <h2 style="margin: 0; font-size: 1.35rem; font-weight: 800; background: linear-gradient(90deg, #c084fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">SupportWise AI</h2>
            <span style="font-size: 0.76rem; color: #94a3b8; font-weight: 500;">Hindsight Long-Term Memory</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Customer Selector Section
    st.subheader("👤 Select Customer")
    
    customer_options = list(DEMO_CUSTOMERS.keys()) + ["Custom ID..."]
    current_cust = st.session_state.selected_customer_id
    if current_cust in DEMO_CUSTOMERS:
        default_index = customer_options.index(current_cust)
    elif current_cust in customer_options:
        default_index = customer_options.index(current_cust)
    else:
        default_index = customer_options.index("Custom ID...")

    selected_option = st.selectbox(
        "Choose Customer Profile:",
        options=customer_options,
        index=default_index,
        format_func=lambda x: f"{DEMO_CUSTOMERS[x]['avatar']} {DEMO_CUSTOMERS[x]['name']} ({x})" if x in DEMO_CUSTOMERS else f"➕ {x}",
        key="customer_select_box"
    )

    if selected_option == "Custom ID...":
        custom_id = st.text_input("Enter Customer ID:", value="CUST-9999", key="custom_customer_id_input").strip().upper()
        if custom_id:
            st.session_state.selected_customer_id = custom_id
    else:
        st.session_state.selected_customer_id = selected_option

    active_cust_id = st.session_state.selected_customer_id

    # Handle Customer Change: When selected customer changes, isolate/load only active customer state
    if st.session_state.current_customer_id != active_cust_id:
        st.session_state.current_customer_id = active_cust_id

    # Initialize customer-isolated state structures if not present
    if active_cust_id not in st.session_state.messages:
        st.session_state.messages[active_cust_id] = []
    if active_cust_id not in st.session_state.last_recalled_memories:
        st.session_state.last_recalled_memories[active_cust_id] = []

    # Display Customer Info Card
    if active_cust_id in DEMO_CUSTOMERS:
        cust_info = DEMO_CUSTOMERS[active_cust_id]
        st.markdown(f"""
        <div class="customer-card">
            <h4>{cust_info['avatar']} {cust_info['name']}</h4>
            <p><strong>ID:</strong> {active_cust_id}</p>
            <p><strong>Email:</strong> {cust_info['email']}</p>
            <p><strong>Tier:</strong> {cust_info['plan']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="customer-card">
            <h4>👤 Custom Profile</h4>
            <p><strong>ID:</strong> {active_cust_id}</p>
            <p>Isolated Memory Bank initialized.</p>
        </div>
        """, unsafe_allow_html=True)

    # Preload Demo Memories Button
    if active_cust_id in DEMO_CUSTOMERS:
        if st.button("🚀 Preload Synthetic History", use_container_width=True, type="secondary", key=f"preload_{active_cust_id}"):
            count = load_demo_customer_memories(active_cust_id, memory_mgr)
            st.success(f"Loaded {count} Hindsight memories for {active_cust_id}!")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")

    # Conversation Control Buttons
    st.subheader("💬 Conversation Controls")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 New Session", help="Clears chat messages but keeps Hindsight long-term memories intact!", key=f"new_session_{active_cust_id}"):
            st.session_state.messages[active_cust_id] = []
            st.session_state.last_recalled_memories[active_cust_id] = []
            st.success(f"Started new session for {active_cust_id}. Long-term memory preserved!")
            time.sleep(0.5)
            st.rerun()

    with col_btn2:
        if st.button("🧹 Clear Memory", help="Wipes all stored Hindsight memories for this customer ID", key=f"clear_mem_{active_cust_id}"):
            memory_mgr.clear_customer_memories(active_cust_id)
            st.session_state.messages[active_cust_id] = []
            st.session_state.last_recalled_memories[active_cust_id] = []
            st.warning(f"Cleared all memories for {active_cust_id}")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")

    # Status & Settings Drawer
    with st.expander("⚙️ System Status & API Keys", expanded=False):
        status = memory_mgr.get_status()
        st.markdown(f"**Hindsight Engine:** `{status['mode'].upper()}`")
        st.markdown(f"**Base URL:** `{status['base_url']}`")
        st.markdown(f"**Groq SDK:** `{'Configured' if llm_mgr.is_configured() else 'Fallback Mode'}`")

        new_groq_key = st.text_input("Groq API Key:", value=st.session_state.groq_api_key, type="password", key="input_groq_key")
        new_hindsight_key = st.text_input("Hindsight API Key:", value=st.session_state.hindsight_api_key, type="password", key="input_hindsight_key")

        if st.button("Save API Keys", key="btn_save_keys"):
            st.session_state.groq_api_key = new_groq_key
            st.session_state.hindsight_api_key = new_hindsight_key
            st.cache_resource.clear()
            st.success("API Keys updated!")
            st.rerun()


# -----------------------------------------------------------------------------
# MAIN DASHBOARD HEADER
# -----------------------------------------------------------------------------
all_stored_memories = memory_mgr.get_all_memories(active_cust_id)
memory_count = len(all_stored_memories)

st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>SupportWise AI</h1>
            <p>AI Customer Support Agent with Hindsight Long-Term Memory • HackwithHyderabad 3.0</p>
        </div>
        <div>
            <span class="badge-memory">🧠 {memory_count} Memories Stored</span>
            <span class="badge-online">● Bank: {active_cust_id}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# MAIN CHAT INTERFACE & MEMORY RECALL PANEL
# -----------------------------------------------------------------------------
col_chat, col_recall = st.columns([2.2, 1.2])

with col_chat:
    st.subheader(f"💬 Live Support Conversation ({active_cust_id})")

    # Display Preset Demo Scenarios for Quick Hackathon Demo
    if active_cust_id in DEMO_CUSTOMERS:
        st.markdown("**⚡ Quick Demo Scenarios (Click to test):**")
        cust_demo = DEMO_CUSTOMERS[active_cust_id]
        scenarios = cust_demo.get("preset_scenarios", [])
        if not scenarios and "preset_prompts" in cust_demo:
            default_labels = ["Printer Wi-Fi Issue", "Laptop Battery Issue", "Previous Ticket Follow-up"]
            scenarios = [
                {"label": default_labels[i] if i < len(default_labels) else f"Scenario {i+1}", "prompt": p}
                for i, p in enumerate(cust_demo["preset_prompts"])
            ]
        
        preset_cols = st.columns(len(scenarios))
        preset_clicked = None
        for idx, item in enumerate(scenarios):
            lbl = item.get("label", f"Scenario {idx+1}")
            p_text = item.get("prompt", "")
            with preset_cols[idx]:
                if st.button(lbl, help=p_text, use_container_width=True, key=f"preset_{active_cust_id}_{idx}"):
                    preset_clicked = p_text

    # Display Chat History for active customer ONLY
    messages_to_show = st.session_state.messages.get(active_cust_id, [])

    if not messages_to_show:
        st.info(f"👋 No conversation history for session [{active_cust_id}]. Type a message below or use a quick demo scenario above to test!")

    for msg in messages_to_show:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "recalled_memories" in msg and msg["recalled_memories"]:
                with st.expander("🧠 View Hindsight Memories used for this response"):
                    for m in msg["recalled_memories"]:
                        st.markdown(f"- **[{m.get('type', 'Memory')}]**: {m.get('text')}")

    # Handle User Input
    user_input = st.chat_input(f"Type message for {active_cust_id}...")

    # If preset button was clicked, override user_input
    if 'preset_clicked' in locals() and preset_clicked:
        user_input = preset_clicked

    if user_input:
        user_input = user_input.strip()

        # 1. Append user message to active customer's chat history ONLY
        st.session_state.messages[active_cust_id].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Retrieve Relevant Memories from Hindsight strictly for this customer bank_id
        with st.spinner(f"🧠 Querying Hindsight memory bank for {active_cust_id}..."):
            recalled_memories = memory_mgr.recall(bank_id=active_cust_id, query=user_input, top_k=5)
            st.session_state.last_recalled_memories[active_cust_id] = recalled_memories

        # 3. Generate LLM Response using Groq LLM + Hindsight context for active customer
        with st.spinner("⚡ Groq LLM synthesizing response with long-term memory..."):
            # Explicitly load chat history strictly for the active customer ID only
            active_customer_chat_history = st.session_state.messages.get(active_cust_id, [])[:-1]

            llm_result = llm_mgr.generate_response(
                customer_id=active_cust_id,
                user_query=user_input,
                recalled_memories=recalled_memories,
                chat_history=active_customer_chat_history
            )
            agent_response = llm_result["response"]
            extracted_memories = llm_result.get("extracted_memories", [])

        # 4. Display Assistant Response
        with st.chat_message("assistant"):
            st.markdown(agent_response)
            if recalled_memories:
                with st.expander("🧠 View Hindsight Memories used for this response"):
                    for m in recalled_memories:
                        st.markdown(f"- **[{m.get('type', 'Memory')}]**: {m.get('text')}")

        # 5. Store extracted memories back into Hindsight for this customer ID ONLY
        with st.spinner(f"💾 Retaining new experiences into Hindsight memory bank [{active_cust_id}]..."):
            for mem_text in extracted_memories:
                memory_mgr.retain(
                    bank_id=active_cust_id,
                    content=mem_text,
                    memory_type="Experience",
                    metadata={"query": user_input[:40]}
                )

        # Append assistant message to active customer session state
        st.session_state.messages[active_cust_id].append({
            "role": "assistant",
            "content": agent_response,
            "recalled_memories": recalled_memories
        })

        st.rerun()


def _clean_mem_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    if " | Involving:" in raw_text:
        raw_text = raw_text.split(" | Involving:")[0]
    return raw_text.strip()


with col_recall:
    st.subheader("🔍 Hindsight Memory Recall Panel")

    st.caption(f"Real-time vector memory retrieval strictly isolated for customer **{active_cust_id}**")

    # Display Recently Recalled Memories for active customer ONLY
    st.markdown("#### 🧠 Memories Recalled for Last Query")
    recalled_list = st.session_state.last_recalled_memories.get(active_cust_id, [])

    if recalled_list:
        seen_recalled = set()
        clean_recalled = []
        for mem in recalled_list:
            c_text = _clean_mem_text(mem.get("text", ""))
            if c_text and c_text not in seen_recalled:
                seen_recalled.add(c_text)
                clean_recalled.append((c_text, mem.get("type", "Experience"), mem.get("score", 0.95)))

        for idx, (m_text, m_type, m_score) in enumerate(clean_recalled):
            st.markdown(f"""
            <div class="memory-panel">
                <div class="memory-panel-title">
                    <span>📌 Memory Fragment #{idx+1} • {m_type}</span>
                    <span style="font-size:0.75rem; color:#a78bfa; margin-left:auto;">Relevance: {m_score}</span>
                </div>
                <div class="memory-item">
                    {m_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No memories recalled yet for [{active_cust_id}] in this turn. Click a scenario or type a message to trigger vector recall.")

    st.markdown("---")

    # Display Full Memory Bank Inspection for active customer ONLY
    st.markdown(f"#### 📚 Stored Memory Bank ({active_cust_id})")
    
    if all_stored_memories:
        seen_bank_texts = set()
        clean_bank_memories = []
        for mem in all_stored_memories:
            c_text = _clean_mem_text(mem.get("text", ""))
            if c_text and c_text not in seen_bank_texts:
                seen_bank_texts.add(c_text)
                clean_bank_memories.append({
                    "text": c_text,
                    "type": mem.get("type", "Experience")
                })

        with st.expander(f"Inspect Stored Memories ({len(clean_bank_memories)} unique items)", expanded=True):
            for m in clean_bank_memories:
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.5); border-left: 3px solid #818cf8; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 0.88rem; color: #f1f5f9;">
                    <span style="background: rgba(129, 140, 248, 0.2); color: #c084fc; font-weight: 600; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-right: 6px;">{m['type']}</span>
                    {m['text']}
                </div>
                """, unsafe_allow_html=True)
    else:
        with st.expander(f"Inspect Memory Bank (0 items)", expanded=True):
            st.write(f"Memory bank for [{active_cust_id}] is empty. Preload synthetic history or chat with the agent to populate memory.")
