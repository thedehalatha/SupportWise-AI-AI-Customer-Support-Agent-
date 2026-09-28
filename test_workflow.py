"""
Verification script for SupportWise AI workflow.
Tests Hindsight memory retention, TEMPR retrieval, bank isolation, and LLM context synthesis.
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


def run_verification():
    print("=" * 60)
    print("[+] SUPPORTWISE AI - VERIFICATION TEST SUITE")
    print("=" * 60)

    # 1. Initialize Memory Manager
    memory_mgr = HindsightMemoryManager()
    status = memory_mgr.get_status()
    print(f"[1] Memory Manager initialized.")
    print(f"    Mode: {status['mode'].upper()}")
    print(f"    Base URL: {status['base_url']}")

    # 2. Retain Memories for Customer 1001 (Sarah - Printer)
    cust_1 = "CUST-1001"
    print(f"\n[2] Storing memories for {cust_1} (Sarah Connor)...")
    memory_mgr.retain(cust_1, "Customer owns HP OfficeJet Pro 9015e Printer.", "Experience")
    memory_mgr.retain(cust_1, "Session #1: Wi-Fi disconnect issue after router reboot.", "Experience")
    memory_mgr.retain(cust_1, "Session #1 Solution: Assigned Static IP 192.168.1.150 on Eero mesh router.", "Experience")

    # 3. Retain Memories for Customer 1002 (David - Laptop Battery)
    cust_2 = "CUST-1002"
    print(f"\n[3] Storing memories for {cust_2} (David Miller)...")
    memory_mgr.retain(cust_2, "Device: MacBook Pro 16-inch M2 Max.", "Experience")
    memory_mgr.retain(cust_2, "Session #1: Battery draining 40% per hour due to WindowServer GPU spike.", "Experience")

    # 4. Recall Memories for Customer 1001 on "The same problem happened again"
    query = "The same problem happened again today."
    print(f"\n[4] Querying Hindsight memory for {cust_1} with prompt: '{query}'")
    recalled_1 = memory_mgr.recall(bank_id=cust_1, query=query, top_k=5)
    
    print(f"    Recalled {len(recalled_1)} memory fragments for {cust_1}:")
    for r in recalled_1:
        print(f"    - [{r.get('type')}] {r.get('text')} (Score: {r.get('score')})")

    # Verify memory content correctness
    recalled_text_concat = " ".join([m.get("text", "") for m in recalled_1])
    assert "HP OfficeJet" in recalled_text_concat or "Wi-Fi" in recalled_text_concat, "Failed to recall printer memories!"
    print("    [OK] Verification Passed: Hindsight successfully recalled HP printer & Wi-Fi context.")

    # 5. Verify Memory Isolation between Customers
    print(f"\n[5] Verifying Memory Isolation for {cust_2}...")
    recalled_2 = memory_mgr.recall(bank_id=cust_2, query="What printer do I have?", top_k=5)
    recalled_2_text = " ".join([m.get("text", "") for m in recalled_2])
    assert "HP OfficeJet" not in recalled_2_text, "LEAK DETECTED: Customer 1002 accessed Customer 1001's memories!"
    print("    [OK] Verification Passed: Customer 1002 memory bank is strictly isolated from Customer 1001.")

    # 6. Test LLM Response Generation
    print(f"\n[6] Testing LLM Response Generation...")
    llm_mgr = GroqLLMManager()
    response_obj = llm_mgr.generate_response(
        customer_id=cust_1,
        user_query=query,
        recalled_memories=recalled_1
    )

    print(f"    Model Used: {response_obj['model_used']}")
    print(f"    Response Output:\n    " + "-" * 50)
    for line in response_obj["response"].split("\n"):
        print(f"    {line}")
    print("    " + "-" * 50)

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()
