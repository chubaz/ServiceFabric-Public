"""Ensure Wave-8 integration does not absorb provider execution implementations."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
forbidden = ("subprocess.Popen", "subprocess.run", "langgraph")
source = (ROOT / "clients/python/servicefabric_client/agent_providers.py").read_text(encoding="utf-8")
if any(token in source for token in forbidden):
    raise SystemExit("Wave-8 integration registry must not launch providers or orchestrate LangGraph")
print("Wave-8 integration boundaries passed.")
