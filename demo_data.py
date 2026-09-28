"""
Synthetic Demo Customer Scenarios for SupportWise AI.
Used for hackathon demonstrations to showcase Hindsight long-term memory retrieval.
"""

DEMO_CUSTOMERS = {
    "CUST-1001": {
        "name": "Sarah Connor",
        "email": "sarah.c@techcorp.io",
        "plan": "Enterprise VIP",
        "avatar": "👩‍💼",
        "initial_memories": [
            "Customer owns HP OfficeJet Pro 9015e Printer.",
            "Network topology: Eero Pro 6 Mesh Wi-Fi network with dual-band 2.4GHz/5GHz.",
            "Session #1 (2026-09-20): Printer lost Wi-Fi IP address after router reboot.",
            "Attempted solution in Session #1: Configured static IP reservation 192.168.1.150.",
            "Customer prefers email support and step-by-step numbered instructions."
        ],
        "preset_scenarios": [
            {
                "label": "🖨️ Printer Wi-Fi Issue",
                "prompt": "Hi, my HP OfficeJet Pro 9015e keeps disconnecting from Wi-Fi whenever the router restarts."
            },
            {
                "label": "⚡ Outage Recurrence",
                "prompt": "The same problem happened again today. The printer disconnected after a power outage."
            },
            {
                "label": "📋 Previous Ticket Follow-up",
                "prompt": "What static IP did we assign last time?"
            }
        ],
        "preset_prompts": [
            "Hi, my HP OfficeJet Pro 9015e keeps disconnecting from Wi-Fi whenever the router restarts.",
            "The same problem happened again today. The printer disconnected after a power outage.",
            "What static IP did we assign last time?"
        ]
    },
    "CUST-1002": {
        "name": "David Miller",
        "email": "david.m@designstudio.co",
        "plan": "Pro Tier",
        "avatar": "👨‍💻",
        "initial_memories": [
            "Device: MacBook Pro 16-inch (M2 Max, 32GB RAM).",
            "OS Version: macOS Sequoia 15.1.",
            "Session #1 (2026-09-15): Reported battery draining 40% per hour after OS update.",
            "Identified cause: 'WindowServer' and heavy GPU rendering background tasks.",
            "Troubleshooting done: Reset SMC/NVRAM, disabled hardware acceleration in Figma."
        ],
        "preset_scenarios": [
            {
                "label": "🔋 Laptop Battery Issue",
                "prompt": "My MacBook Pro battery is draining super fast after the latest Sequoia update."
            },
            {
                "label": "💻 Design App Drain",
                "prompt": "I noticed my laptop battery is dropping fast again while running design apps."
            },
            {
                "label": "📋 Previous Ticket Follow-up",
                "prompt": "Which background process was causing the spike before?"
            }
        ],
        "preset_prompts": [
            "My MacBook Pro battery is draining super fast after the latest Sequoia update.",
            "I noticed my laptop battery is dropping fast again while running design apps.",
            "Which background process was causing the spike before?"
        ]
    },
    "CUST-1003": {
        "name": "Priya Sharma",
        "email": "priya.s@fintechglobal.com",
        "plan": "Standard",
        "avatar": "👩‍💻",
        "initial_memories": [
            "Software License: Enterprise Cloud Suite 2026.",
            "Error Code encountered: ERR-403 Forbidden on SSO Authentication.",
            "Session #1 (2026-09-18): Okta SAML token expired after corporate domain migration.",
            "Resolved by re-syncing Okta Directory groups and clearing browser cookies."
        ],
        "preset_scenarios": [
            {
                "label": "🔐 Cloud ERR-403 Issue",
                "prompt": "I cannot log into the Enterprise Cloud Suite, getting error ERR-403."
            },
            {
                "label": "🌐 Home SSO Error",
                "prompt": "Hi again! ERR-403 popped up when I tried signing in from my home laptop."
            },
            {
                "label": "📋 Previous Ticket Follow-up",
                "prompt": "Did we fix this with Okta SAML directory re-sync last week?"
            }
        ],
        "preset_prompts": [
            "I cannot log into the Enterprise Cloud Suite, getting error ERR-403.",
            "Hi again! ERR-403 popped up when I tried signing in from my home laptop.",
            "Did we fix this with Okta SAML directory re-sync last week?"
        ]
    }
}


def load_demo_customer_memories(customer_id: str, memory_manager):
    """
    Populates Hindsight memory store with synthetic history for the selected demo customer.
    """
    if customer_id not in DEMO_CUSTOMERS:
        return 0

    customer = DEMO_CUSTOMERS[customer_id]
    count = 0
    for mem_text in customer["initial_memories"]:
        memory_manager.retain(
            bank_id=customer_id,
            content=mem_text,
            memory_type="Experience",
            metadata={"source": "Synthetic Demo Preload"}
        )
        count += 1
    return count
