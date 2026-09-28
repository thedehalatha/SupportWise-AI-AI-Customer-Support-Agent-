# 🧠 SupportWise AI — AI Customer Support Agent with Hindsight Memory

> **HackwithHyderabad 3.0 Submission**  
> *Built with Hindsight Memory (Vectorize), Groq LLM, and Streamlit*

---

## 📌 Problem Statement & Solution

Traditional AI customer support chatbots suffer from **"session amnesia"** — every time a customer opens a new chat or returns after a few days, the chatbot forgets their device model, software version, previous troubleshooting steps, and past preferences. Customers are forced to repeat themselves, leading to frustration and poor support experiences.

**SupportWise AI** solves this by integrating **Hindsight Vector Memory** into the support workflow:
- **Long-Term Memory Retention:** Crucial facts, device details, error codes, and troubleshooting outcomes are extracted and stored permanently in customer-specific memory banks.
- **TEMPR Memory Retrieval:** Before answering a new query, the agent queries Hindsight to retrieve relevant past experiences and context.
- **Isolated Customer Memory Banks:** Each customer ID operates in an isolated memory bank (`bank_id`), ensuring 100% data privacy and zero memory cross-leakage.
- **Adaptive Support Responses:** Powered by **Groq LLM** (`llama-3.3-70b-versatile`), the AI agent acknowledges past issues, skips redundant questions, and offers next-level solutions.

---

## ✨ Core Features

1. **🎨 Modern Streamlit Dark Theme UI:**
   - Sleek glassmorphism UI design with vibrant badges, sidebar customer switcher, chat history, and live memory status indicator.

2. **👤 Customer Profile & Memory Bank Isolation:**
   - Switch between preset demo customer profiles (`Sarah Connor - Printer Wi-Fi`, `David Miller - MacBook Battery`, `Priya Sharma - Cloud SSO Error`) or enter any custom Customer ID.

3. **🔍 Live Memory Recall Panel:**
   - Visually displays the exact long-term memories retrieved by Hindsight for the current query, including memory fragment type, relevance score, and LLM reasoning.

4. **🔄 Session Resets with Memory Persistence:**
   - Click **"New Session"** to reset current chat messages while preserving long-term Hindsight memories across app restarts and browser refreshes.

5. **⚡ Dual-Engine Architecture (Cloud SDK & Offline Persistent Mode):**
   - Connects directly to **Hindsight Cloud API** via the official `hindsight-client` Python SDK.
   - Includes an embedded persistent SQLite fallback so the application works out-of-the-box even without active cloud API keys.

6. **🛠️ Interactive Demo Mode:**
   - Pre-loaded synthetic customer support cases specifically designed for hackathon live demonstrations.

---

## 🏗️ Technical Architecture

```
                               ┌────────────────────────────────┐
                               │     Streamlit Chat Interface   │
                               └───────────────┬────────────────┘
                                               │
                                      User Query + Customer ID
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │  Hindsight Memory Manager      │
                               │  (hindsight-client Python SDK) │
                               └───────────────┬────────────────┘
                                               │
                                   Recall Relevant Memories
                                               │
                                               ▼
┌────────────────────────────────┐     ┌────────────────────────────────┐
│          Groq LLM SDK          │◄────┤ System Prompt + Memory Context │
│    (llama-3.3-70b-versatile)   │     └────────────────────────────────┘
└───────────────┬────────────────┘
                │
         Agent Response
                │
                ▼
┌────────────────────────────────┐
│   Retain Extracted Memories    │ ──► Saved back into Hindsight Memory Bank
└────────────────────────────────┘
```

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit 1.64+ (Custom Dark CSS Glassmorphism Layout)
- **Memory Engine:** Hindsight Vector Memory (`hindsight-client` SDK)
- **LLM Engine:** Groq API (`groq` Python SDK, `llama-3.3-70b-versatile`)
- **Backend & Environment:** Python 3.10+, `python-dotenv`, SQLite (Local Fallback)

---

## 🚀 Quickstart & Setup Guide (Windows & VS Code)

### Prerequisites
- **Python 3.10 or higher** installed on Windows.
- **VS Code** (recommended editor).

### Step 1: Clone / Open Project Folder
Open VS Code and navigate to the project directory:
```bash
cd c:\Users\R.Deha latha\OneDrive\Desktop\SupportWiseAI
```

### Step 2: Create a Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure API Keys (`.env`)
Create a `.env` file in the root directory (or copy from `.env.example`):
```env
# Groq LLM API Key (Get free key from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here

# Hindsight Memory API Settings (Get key from https://hindsight.vectorize.io)
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
```

> **Note:** If API keys are not provided immediately, SupportWise AI automatically activates its **Embedded Persistent Fallback Engine**, ensuring full offline demonstrability without crashing!

---

## 🧪 Verification & Automated Testing

To run the automated verification test suite for Hindsight memory retention, TEMPR retrieval, bank isolation, and LLM synthesis:

```powershell
python test_workflow.py
```

**Sample Output:**
```
============================================================
[+] SUPPORTWISE AI - VERIFICATION TEST SUITE
============================================================
[1] Memory Manager initialized.
[2] Storing memories for CUST-1001 (Sarah Connor)...
[3] Storing memories for CUST-1002 (David Miller)...
[4] Querying Hindsight memory for CUST-1001...
    [OK] Verification Passed: Hindsight recalled HP printer & Wi-Fi context.
[5] Verifying Memory Isolation for CUST-1002...
    [OK] Verification Passed: Customer 1002 memory bank is strictly isolated.
[SUCCESS] ALL VERIFICATION TESTS PASSED SUCCESSFULLY!
============================================================
```

---

## 🎬 How to Run & Demonstrate the App

### Launch Streamlit Application
```powershell
python -m streamlit run app.py
```
Or if Streamlit is added to PATH:
```powershell
streamlit run app.py
```

The application will launch in your web browser at `http://localhost:8501`.

---

## 🎭 Step-by-Step Hackathon Judge Demo Walkthrough

Follow these steps to demonstrate long-term memory persistence:

### **Phase 1: Initial Customer Interaction (Session #1)**
1. Select Customer Profile **`👩‍💼 Sarah Connor (CUST-1001)`** in the sidebar.
2. Click **"🚀 Preload Synthetic History"** to populate initial memories (or type a message like *"My HP OfficeJet Pro 9015e printer lost Wi-Fi connection after router restart"*).
3. Observe the **Hindsight Memory Recall Panel** on the right updating with stored facts.

### **Phase 2: Simulate Session Disconnect / App Restart**
1. Click the **"🔄 New Session"** button in the sidebar.
2. Notice that the chat message screen clears completely (simulating a customer returning days later in a brand new chat session).

### **Phase 3: The Returning Customer (Session #2 Memory Recall)**
1. In the new chat session, type:  
   > *"The same problem happened again today."*
2. **Observe the Magic:**
   - Hindsight automatically retrieves the stored memory fragments for `CUST-1001` (*HP OfficeJet Pro 9015e*, *Eero Mesh Wi-Fi*, *Static IP assignment*).
   - The Groq LLM synthesizes a personalized response acknowledging her exact printer model and past static IP step without asking her to repeat herself!
   - The **Memory Recall Panel** highlights the exact fragments retrieved and used.

### **Phase 4: Customer Bank Isolation Test**
1. Switch to Customer **`👨‍💻 David Miller (CUST-1002)`** in the sidebar.
2. Type: *"What printer do I have?"*
3. Notice that David's response and recall panel contain **ZERO** references to Sarah's HP printer. His memory bank is 100% isolated.

---

## 📁 Repository File Structure

```
SupportWiseAI/
├── app.py                  # Main Streamlit web application & UI layout
├── hindsight_helper.py     # Hindsight Cloud SDK & Local SQLite fallback manager
├── llm_helper.py           # Groq LLM API client & memory prompt synthesis
├── demo_data.py            # Synthetic customer profiles & demo scenarios
├── test_workflow.py        # Automated test suite for memory persistence & isolation
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables template
├── .env                    # Local environment variables (API keys)
├── .gitignore              # Git ignore rules
└── README.md               # Complete project documentation
```

---

## 🏆 HackwithHyderabad 3.0 Submission Checklist

- [x] Functional Hindsight Vector Memory integration (`retain` and `recall`).
- [x] Groq LLM integration with memory context prompt engineering.
- [x] Streamlit Dark Theme UI with Memory Recall Drawer.
- [x] Isolated memory banks per customer ID.
- [x] Long-term persistence across session resets and restarts.
- [x] Realistic pre-loaded synthetic hackathon demo scenarios.
- [x] Fully tested automated verification suite (`test_workflow.py`).
- [x] Complete README setup documentation.

---

### 👨‍💻 Developed for HackwithHyderabad 3.0
*Empowering AI Customer Support with True Long-Term Memory.*
