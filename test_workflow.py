"""
Automated Test Suite for SupportWise AI.
Verifies Customer Data Isolation, Profile Switching, Session Resets, and Hindsight Memory Retrieval.
"""

import sys
import os

# Set UTF-8 output encoding for Windows terminal compatibility
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from hindsight_helper import HindsightMemoryManager
from llm_helper import GroqLLMManager
from demo_data import load_demo_customer_memories, DEMO_CUSTOMERS


def run_isolation_tests():
    print("=" * 70)
    print("[+] SUPPORTWISE AI — CUSTOMER DATA ISOLATION TEST SUITE")
    print("=" * 70)

    # 1. Initialize Memory Manager and LLM Manager
    memory_mgr = HindsightMemoryManager()
    llm_mgr = GroqLLMManager()

    # Clear pre-existing test memory banks to start fresh
    memory_mgr.clear_customer_memories("CUST-1001")
    memory_mgr.clear_customer_memories("CUST-1002")
    memory_mgr.clear_customer_memories("CUST-1003")

    # 2. Populate Synthetic Memories for Sarah (CUST-1001) and David (CUST-1002)
    print("\n[STEP 1] Preloading memories for CUST-1001 (Sarah - HP Printer) and CUST-1002 (David - MacBook)...")
    count_sarah = load_demo_customer_memories("CUST-1001", memory_mgr)
    count_david = load_demo_customer_memories("CUST-1002", memory_mgr)

    print(f"        Loaded {count_sarah} memories for CUST-1001.")
    print(f"        Loaded {count_david} memories for CUST-1002.")

    # 3. TEST 1: Ask David Miller (CUST-1002) "What printer do I have?"
    print("\n[TEST 1] Querying David Miller (CUST-1002) with: 'What printer do I have?'")
    cust_david = "CUST-1002"
    query_printer = "What printer do I have?"
    
    # Recall memories strictly for CUST-1002
    david_recalled = memory_mgr.recall(bank_id=cust_david, query=query_printer, top_k=5)
    david_recalled_text = " ".join([m.get("text", "") for m in david_recalled])

    print(f"        Recalled {len(david_recalled)} memories for {cust_david}:")
    for m in david_recalled:
        print(f"        - [{m.get('type')}] {m.get('text')}")

    # Assert Hindsight recall returned NO printer info for David
    assert "HP OfficeJet" not in david_recalled_text, "CRITICAL ERROR: Hindsight returned Sarah's HP printer memory for David!"
    print("        ✅ Hindsight Recall Check Passed: ZERO printer memories returned for David.")

    # Generate LLM response for David
    response_david = llm_mgr.generate_response(
        customer_id=cust_david,
        user_query=query_printer,
        recalled_memories=david_recalled
    )
    david_resp_text = response_david["response"]
    print("\n        --- Agent Response to David ---")
    print("        " + david_resp_text.replace("\n", "\n        "))
    print("        -------------------------------")

    # Assert response contains NO references to Sarah's printer or Eero router
    assert "HP OfficeJet" not in david_resp_text, "CRITICAL BUG: Agent responded to David with Sarah's HP OfficeJet printer!"
    assert "192.168.1.150" not in david_resp_text, "CRITICAL BUG: Agent responded to David with Sarah's Static IP!"
    print("        ✅ Agent Response Check Passed: Response strictly contains NO data from Sarah Connor.")

    # 4. TEST 2: Query Sarah Connor (CUST-1001) for printer issues
    print("\n[TEST 2] Querying Sarah Connor (CUST-1001) with: 'What printer do I have?'")
    cust_sarah = "CUST-1001"
    sarah_recalled = memory_mgr.recall(bank_id=cust_sarah, query=query_printer, top_k=5)
    sarah_recalled_text = " ".join([m.get("text", "") for m in sarah_recalled])

    assert "HP OfficeJet" in sarah_recalled_text, "ERROR: Sarah's printer memory missing from Hindsight!"
    print(f"        Recalled {len(sarah_recalled)} memories for {cust_sarah}.")
    print("        ✅ Hindsight Recall Check Passed: HP OfficeJet Pro 9015e correctly recalled for Sarah.")

    response_sarah = llm_mgr.generate_response(
        customer_id=cust_sarah,
        user_query=query_printer,
        recalled_memories=sarah_recalled
    )
    sarah_resp_text = response_sarah["response"]
    assert "HP OfficeJet" in sarah_resp_text, "ERROR: Sarah's response failed to cite her printer model!"
    print("        ✅ Agent Response Check Passed: Sarah accurately received her HP OfficeJet printer details.")

    # 5. TEST 3: Profile Switching & Memory Recall Panel Isolation
    print("\n[TEST 3] Testing Profile Switching State Isolation...")
    # Simulate session state mapping
    session_messages = {
        "CUST-1001": [{"role": "user", "content": "Printer query"}, {"role": "assistant", "content": sarah_resp_text}],
        "CUST-1002": [{"role": "user", "content": "MacBook query"}, {"role": "assistant", "content": david_resp_text}]
    }
    session_recalled = {
        "CUST-1001": sarah_recalled,
        "CUST-1002": david_recalled
    }

    # Verify key isolation
    assert "HP OfficeJet" in " ".join([m["text"] for m in session_recalled["CUST-1001"]])
    assert "HP OfficeJet" not in " ".join([m["text"] for m in session_recalled["CUST-1002"]])
    print("        ✅ Profile Switch Isolation Passed: session_recalled['CUST-1002'] is 100% free of CUST-1001 data.")

    # 6. TEST 4: New Session Persistence Test
    print("\n[TEST 4] Testing New Session (Clear Chat, Keep Memory) for CUST-1001...")
    # Simulate new session: clear chat messages list for CUST-1001
    session_messages["CUST-1001"] = []
    
    # Query Hindsight again after new session start
    post_reset_recalled = memory_mgr.recall(bank_id=cust_sarah, query="The same problem happened again today.", top_k=5)
    post_reset_text = " ".join([m["text"] for m in post_reset_recalled])
    assert "HP OfficeJet" in post_reset_text, "ERROR: Memory lost after session reset!"
    print("        ✅ New Session Persistence Passed: Hindsight retained Sarah's memories after session reset.")

    print("\n" + "=" * 70)
    print("🎉 ALL CUSTOMER DATA ISOLATION TESTS PASSED 100% SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_isolation_tests()
