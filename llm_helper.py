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

CUSTOMER IDENTIFIER: {customer_id}

HINDSIGHT RECALLED MEMORIES FOR THIS CUSTOMER:
{memories_context}

INSTRUCTIONS FOR AGENT:
1. Always check the recalled long-term memories before responding.
2. If the customer mentions a previous issue, product, device, or setup step, explicitly reference it! (e.g., "I see you contacted us earlier about your HP OfficeJet printer Wi-Fi issue...").
3. DO NOT ask the user for information that is already stored in your recalled memories.
4. Keep your tone professional, friendly, and solution-oriented.
5. Provide actionable step-by-step guidance.
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
        Generates an LLM response incorporating Hindsight long-term memories.
        """
        # Format memories context
        if recalled_memories:
            memories_formatted = "\n".join([
                f"- [{mem.get('type', 'Memory')}] {mem.get('text', '')}"
                for mem in recalled_memories
            ])
        else:
            memories_formatted = "No previous long-term memories recorded yet for this customer."

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
                return self._rule_based_fallback(user_query, recalled_memories, err_msg)
        else:
            # Smart Offline Mock Response Engine for local testing without API key
            return self._rule_based_fallback(user_query, recalled_memories, "Groq API Key not set in environment.")

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
            # Clean JSON formatting backticks if any
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

    def _rule_based_fallback(self, user_query: str, recalled_memories: List[Dict[str, Any]], reason: str) -> Dict[str, Any]:
        """
        Rule-based simulation for testing when Groq API key is missing or encounters issues.
        """
        query_lower = user_query.lower()

        # Check if we recalled relevant memories
        recalled_texts = [m.get("text", "") for m in recalled_memories]
        recalled_summary = " ".join(recalled_texts).lower()

        if "printer" in query_lower or "printer" in recalled_summary or "wi-fi" in query_lower or "wifi" in query_lower:
            if "same problem" in query_lower or "again" in query_lower or len(recalled_memories) > 0:
                response = (
                    "Welcome back! I recall from our previous conversation that you're using an **HP OfficeJet Pro 9015e** "
                    "connected to a mesh Wi-Fi network, and we previously assigned a Static IP address.\n\n"
                    "Since the disconnect happened again, let's try the next step:\n"
                    "1. Access your router settings and **disable 5GHz steering** for the printer, binding it strictly to the 2.4GHz band.\n"
                    "2. Toggle Wi-Fi Direct OFF on the HP printer control panel as it can cause channel interference.\n\n"
                    "Let me know if the Wi-Fi status light turns solid blue after trying this!"
                )
            else:
                response = (
                    "I understand you're experiencing Wi-Fi connection drops on your printer. "
                    "Could you confirm your printer model and router setup so I can note it for future reference?"
                )
        elif "battery" in query_lower or "laptop" in query_lower:
            response = (
                "I've noted your issue regarding laptop battery drain. "
                "Let's check background process consumption in Activity Monitor/Task Manager, and verify power adapter wattage."
            )
        else:
            response = (
                f"Thank you for contacting SupportWise AI. I have logged your query regarding: '{user_query}'. "
                "Based on your support history, I will keep track of this incident for future follow-ups."
            )

        if "not set" in reason.lower() or "your_groq_api_key_here" in reason.lower():
            response += "\n\n*(Note: Running in local demonstration mode. Add your `GROQ_API_KEY` to `.env` for full LLM responses.)*"

        extracted = [f"Customer query: '{user_query[:60]}'"]
        if "printer" in query_lower or "wi-fi" in query_lower:
            extracted.append("Customer reported Wi-Fi printer disconnection issue.")

        return {
            "status": "fallback",
            "response": response,
            "extracted_memories": extracted,
            "model_used": "Groq Demo Engine (Offline)",
            "memories_used": len(recalled_memories),
            "note": reason
        }
