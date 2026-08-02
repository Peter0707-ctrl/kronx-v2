"""
PJKRONX AI OS - Modular Sub-Agent Registry & Router Layer
Separates specialized domain logic cleanly into dedicated sub-agent modules.
"""

from typing import Dict, Any

class BaseAgent:
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain

    def get_context(self) -> str:
        return f"Specialized Sub-Agent: {self.name} ({self.domain})"

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__("Coding Expert", "Software Engineering & Algorithms")

class BusinessAgent(BaseAgent):
    def __init__(self):
        super().__init__("Tanzania Business & Legal Expert", "TRA, BRELA, Budgeting & TZS Financials")

class HealthAgent(BaseAgent):
    def __init__(self):
        super().__init__("Health & Wellness Assistant", "Preventative Health, Medical Terms & First Aid")

class AgricultureAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agriculture & Livestock Specialist", "Kilimo cha Kisasa, Samaki & Mifugo")

class EducationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Academic & Education Tutor", "Step-by-Step Homework, Thesis & Science")

# Multi-Agent Router Registry
AGENT_REGISTRY: Dict[str, BaseAgent] = {
    "coding": CodingAgent(),
    "business": BusinessAgent(),
    "health": HealthAgent(),
    "agriculture": AgricultureAgent(),
    "education": EducationAgent()
}

def route_agent(query: str) -> BaseAgent:
    q = query.lower()
    if any(k in q for k in ["code", "python", "javascript", "c++", "html", "css", "bug", "git"]):
        return AGENT_REGISTRY["coding"]
    elif any(k in q for k in ["tra", "brela", "nida", "biashara", "tin", "vat", "budget", "tzs", "tax"]):
        return AGENT_REGISTRY["business"]
    elif any(k in q for k in ["afya", "health", "ugonjwa", "dawa", "nhif", "hospital", "doctor"]):
        return AGENT_REGISTRY["health"]
    elif any(k in q for k in ["kilimo", "mbolea", "mahindi", "kuku", "samaki", "mifugo", "shamba"]):
        return AGENT_REGISTRY["agriculture"]
    else:
        return AGENT_REGISTRY["education"]
