import os
import json
from typing import List, Dict, Any, Optional

try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False


SYSTEM_PROMPT_TEMPLATE = """You are SupportWise AI, an advanced AI Customer Support Agent equipped with Hindsight Long-Term Memory.
Your goal is to provide helpful, empathetic, accurate, and concise customer support.

CRITICAL DATA ISOLATION RULE: You are currently assisting Customer ID: [{customer_id}].
You MUST ONLY reference memories and facts provided under HINDSIGHT RECALLED MEMORIES below.
NEVER reference devices, products, or issues belonging to other customers unless explicitly stated in this customer's memories.

HINDSIGHT RECALLED MEMORIES FOR CUSTOMER [{customer_id}]:
{memories_context}

INSTRUCTIONS FOR AGENT:
1. Always check the recalled long-term memories for [{customer_id}] before responding.
2. If the customer asks about a device/product (e.g. "What printer do I have?"):
   - If the recalled memories contain a printer/device for THIS customer, answer with that specific model.
   - If the recalled memories DO NOT contain that device, explicitly state that no record of such device exists in Customer [{customer_id}]'s history.
3. DO NOT ask the user for information already stored in their recalled memories.
4. Keep your tone professional, friendly, and solution-oriented.
"""

MEMORY_EXTRACTION_PROMPT = """Extract 1 to 3 key concise factual statements or support experiences from this user message and agent response to save into long-term Hindsight memory.

Rules for extracted memories:
- Focus on device/product models, specific error codes, troubleshooting steps attempted, solutions succeeded or failed, and user preferences.
- Each memory must be a single self-contained sentence.
- Return ONLY a JSON list of strings, e.g. ["User has HP OfficeJet Pro 9015e printer.", "Wi-Fi disconnection happens after router reboot."]

User Message: {user_query}
Agent Response: {agent_response}

JSON Output:"""


class GroqLLMManager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.client = None
        self.default_model = "llama-3.3-70b-versatile"
        self._init_client()

    def _init_client(self):
        if GROQ_SDK_AVAILABLE and self.api_key and self.api_key.strip() != "your_groq_api_key_here":
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[GroqLLMManager] Failed to initialize Groq client: {e}")
                self.client = None
        else:
            self.client = None

    def is_configured(self) -> bool:
        return self.client is not None

    def generate_response(
        self,
        customer_id: str,
        user_query: str,
        recalled_memories: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an LLM response incorporating Hindsight long-term memories for a specific customer.
        """
        # Format memories context strictly for this customer
        if recalled_memories:
            memories_formatted = "\n".join([
                f"- [{mem.get('type', 'Memory')}] {mem.get('text', '')}"
                for mem in recalled_memories
            ])
        else:
            memories_formatted = f"No previous long-term memories recorded yet for customer [{customer_id}]."

        system_content = SYSTEM_PROMPT_TEMPLATE.format(
            customer_id=customer_id,
            memories_context=memories_formatted
        )

        messages = [{"role": "system", "content": system_content}]

        # Append previous turn history if available
        if chat_history:
            for msg in chat_history[-6:]:  # include up to last 6 messages
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_query})

        chosen_model = model or self.default_model

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=chosen_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                agent_text = response.choices[0].message.content
                
                # Auto-extract key info for retention
                extracted_memories = self._extract_memories(user_query, agent_text, chosen_model)

                return {
                    "status": "success",
                    "response": agent_text,
                    "extracted_memories": extracted_memories,
                    "model_used": chosen_model,
                    "memories_used": len(recalled_memories)
                }

            except Exception as e:
                err_msg = str(e)
                print(f"[GroqLLM] API Error: {err_msg}")
                # Fallback response generation
                return self._rule_based_fallback(customer_id, user_query, recalled_memories, err_msg)
        else:
            # Smart Offline Mock Response Engine for local testing without API key
            return self._rule_based_fallback(customer_id, user_query, recalled_memories, "Groq API Key not set in environment.")

    def _extract_memories(self, user_query: str, agent_response: str, model: str) -> List[str]:
        """
        Extracts structured memory facts using Groq LLM.
        """
        if not self.client:
            return [f"Customer discussed query: '{user_query[:60]}...'"]

        try:
            prompt = MEMORY_EXTRACTION_PROMPT.format(
                user_query=user_query,
                agent_response=agent_response
            )
            res = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=256
            )
            raw = res.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
            memories = json.loads(raw)
            if isinstance(memories, list):
                return memories
        except Exception as e:
            print(f"[GroqLLM] Memory extraction fallback ({e})")
            
        return [f"Customer issue discussed: {user_query[:80]}"]

    def _rule_based_fallback(
        self,
        customer_id: str,
        user_query: str,
        recalled_memories: List[Dict[str, Any]],
        reason: str
    ) -> Dict[str, Any]:
        """
        Rule-based simulation for local demonstration.
        STRICTLY checks recalled memories of THIS customer to prevent cross-customer data leakage.
        """
        query_lower = user_query.lower()

        recalled_texts = [m.get("text", "") for m in recalled_memories]
        recalled_summary = " ".join(recalled_texts)
        recalled_summary_lower = recalled_summary.lower()

        # Check what device/domain memories THIS customer actually possesses
        has_printer_memory = any(
            kw in recalled_summary_lower for kw in ["printer", "officejet", "hp", "wi-fi disconnect", "static ip"]
        )
        has_macbook_memory = any(
            kw in recalled_summary_lower for kw in ["macbook", "battery", "sequoia", "windowserver", "apple", "laptop"]
        )
        has_cloud_memory = any(
            kw in recalled_summary_lower for kw in ["err-403", "okta", "cloud suite", "sso", "saml"]
        )

        # 1. Queries about Printer
        if "printer" in query_lower:
            if has_printer_memory:
                response = (
                    f"Welcome back **{customer_id}**! I recall from your support history that you are using an "
                    "**HP OfficeJet Pro 9015e** printer connected to an Eero Mesh Wi-Fi network (Static IP 192.168.1.150).\n\n"
                    "Since the disconnect issue recurred, here are the next recommended troubleshooting steps:\n"
                    "1. Access your router dashboard and bind the printer strictly to the **2.4GHz Wi-Fi band** (disable band steering).\n"
                    "2. Turn OFF **Wi-Fi Direct** on the HP printer control panel to prevent channel conflict."
                )
            else:
                records_summary = f" (Stored device on record: {recalled_texts[0]})" if recalled_texts else " (No devices registered on file)."
                response = (
                    f"Hello **{customer_id}**! I checked your Hindsight support history{records_summary}. "
                    "I do **not** have any record of a printer registered or previously discussed under your account. "
                    "Could you please share your printer brand and model number so I can assist you and save it to your profile?"
                )

        # 2. Queries about Laptop / Battery / MacBook
        elif "battery" in query_lower or "macbook" in query_lower or "laptop" in query_lower:
            if has_macbook_memory:
                response = (
                    f"Hello **{customer_id}**! I recall from your account history that you are using a "
                    "**MacBook Pro 16-inch (M2 Max)** running macOS Sequoia 15.1.\n\n"
                    "Previously, we identified heavy battery drain (40%/hr) caused by `WindowServer` and GPU acceleration.\n"
                    "Let's check Activity Monitor under the Energy tab to verify if Figma hardware acceleration is still active."
                )
            else:
                response = (
                    f"Hello **{customer_id}**! I searched your memory profile, but I don't see any record of a MacBook or battery issue on file. "
                    "Could you share your laptop model and OS version so I can note it in your profile?"
                )

        # 3. Queries about Cloud / SSO / ERR-403
        elif "err-403" in query_lower or "cloud" in query_lower or "login" in query_lower or "sso" in query_lower:
            if has_cloud_memory:
                response = (
                    f"Hello **{customer_id}**! I recall you previously encountered **ERR-403 Forbidden** on Enterprise Cloud Suite "
                    "due to an Okta SAML directory group token expiration after domain migration.\n\n"
                    "Please clear your browser cookies for the authentication portal and attempt SSO re-login."
                )
            else:
                response = (
                    f"Hello **{customer_id}**! I checked your profile for **{customer_id}**. "
                    "I don't see any previous record of ERR-403 login errors. Could you provide details on the application you are attempting to access?"
                )

        # 4. General Queries
        else:
            if recalled_memories:
                summary_snippet = "; ".join(recalled_texts[:2])
                response = (
                    f"Hello **{customer_id}**! I've retrieved your long-term memory bank.\n"
                    f"**Account History Context:** {summary_snippet}\n\n"
                    f"Regarding your query: *\"{user_query}\"* — I am logging this interaction into your Hindsight memory bank."
                )
            else:
                response = (
                    f"Hello! Your isolated Hindsight memory bank for **{customer_id}** is active. "
                    f"I have recorded your request: *\"{user_query}\"* and will save all key details for your future visits."
                )

        if "not set" in reason.lower() or "your_groq_api_key_here" in reason.lower():
            response += "\n\n*(Note: Running in local demonstration mode. Add your `GROQ_API_KEY` to `.env` for full Groq LLM responses.)*"

        extracted = [f"Customer {customer_id} query: '{user_query[:60]}'"]
        if has_printer_memory and "printer" in query_lower:
            extracted.append(f"Follow-up printer Wi-Fi support session for {customer_id}.")

        return {
            "status": "fallback",
            "response": response,
            "extracted_memories": extracted,
            "model_used": "Groq Demo Engine (Offline)",
            "memories_used": len(recalled_memories),
            "note": reason
        }
