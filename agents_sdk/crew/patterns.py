"""
Detects the type and development stage of a service without calling an LLM.
This shapes how every crew agent frames its work.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from config import CATALOG_DIR


# ── Service types ──────────────────────────────────────────────────────────────

class ServiceType:
    SVELTE_CRUD    = "svelte_crud"      # Svelte 5 + Flask CRUD (most common)
    REACT_CRUD     = "react_crud"       # React 18 + Flask CRUD
    FAAS           = "faas"             # Mainly service.py, minimal frontend
    AI_AGENT       = "ai_agent"         # Uses Gemini / OpenAI / LangChain
    VISUALIZATION  = "visualization"    # Heavy D3 / vis-network / Chart.js
    UNKNOWN        = "unknown"


class DevStage:
    SCAFFOLDED  = "scaffolded"    # Just created — no real logic yet
    EARLY       = "early"         # Has basic routes and a few components
    DEVELOPED   = "developed"     # Feature-complete for its initial scope
    MATURE      = "mature"        # Multiple components, needs scaling attention


# ── Service context ────────────────────────────────────────────────────────────

@dataclass
class ServicePattern:
    service_name:  str
    service_type:  str
    dev_stage:     str
    has_models:    bool
    has_routes:    bool
    has_service_py: bool
    has_frontend:  bool
    is_svelte:     bool
    is_react:      bool
    has_ai:        bool
    has_viz:       bool
    component_count: int
    route_file_count: int
    existing_files:  list[str] = field(default_factory=list)

    # Populated progressively by crew agents
    coordinator_plan:     str = ""
    backend_output:       str = ""
    frontend_output:      str = ""
    integration_output:   str = ""
    security_report:      str = ""
    quality_report:       str = ""
    architecture_report:  str = ""
    supervisor_summary:   str = ""

    @property
    def type_label(self) -> str:
        labels = {
            ServiceType.SVELTE_CRUD:   "Svelte 5 CRUD Service",
            ServiceType.REACT_CRUD:    "React 18 CRUD Service",
            ServiceType.FAAS:          "FaaS / Serverless Script",
            ServiceType.AI_AGENT:      "AI Agent Service",
            ServiceType.VISUALIZATION: "Data Visualization Service",
            ServiceType.UNKNOWN:       "Service (unknown pattern)",
        }
        return labels.get(self.service_type, self.service_type)

    @property
    def stage_label(self) -> str:
        labels = {
            DevStage.SCAFFOLDED: "Just scaffolded — needs initial development",
            DevStage.EARLY:      "Early development — basic structure in place",
            DevStage.DEVELOPED:  "Feature-complete for initial scope",
            DevStage.MATURE:     "Mature — ready for scaling and refactoring",
        }
        return labels.get(self.dev_stage, self.dev_stage)

    def summary(self) -> str:
        return (
            f"Service: {self.service_name}\n"
            f"Type: {self.type_label}\n"
            f"Stage: {self.stage_label}\n"
            f"Frontend: {'Svelte 5' if self.is_svelte else 'React 18' if self.is_react else 'none'}\n"
            f"Has models: {self.has_models} | Has routes: {self.has_routes} | "
            f"Has service.py: {self.has_service_py}\n"
            f"Components: {self.component_count} | Route files: {self.route_file_count}\n"
            f"AI integration: {self.has_ai} | Visualization: {self.has_viz}"
        )


# ── Detector ───────────────────────────────────────────────────────────────────

def detect(service_name: str) -> ServicePattern:
    """Analyse a service directory and return its ServicePattern."""
    d = CATALOG_DIR / service_name
    if not d.exists():
        raise FileNotFoundError(f"Service not found: {d}")

    # File presence
    has_models    = (d / "models.py").exists()
    has_routes    = (d / "routes").is_dir() or (d / "routes.py").exists()
    has_service   = (d / "service.py").exists()
    is_svelte     = (d / "src" / "main.ts").exists()
    is_react      = (d / "src" / "main.jsx").exists()
    has_frontend  = is_svelte or is_react

    # Component count (Svelte or React)
    comp_dir = d / "src" / "components"
    component_count = len(list(comp_dir.glob("*.svelte")) + list(comp_dir.glob("*.jsx")) + list(comp_dir.glob("*.tsx"))) if comp_dir.exists() else 0

    # Route file count
    routes_dir = d / "routes"
    route_file_count = len([f for f in routes_dir.glob("*.py") if f.name != "__init__.py"]) if routes_dir.is_dir() else (1 if has_routes else 0)

    # AI / viz detection via keyword scan
    has_ai = has_viz = False
    for py_file in d.rglob("*.py"):
        try:
            text = py_file.read_text(errors="ignore")
            if any(k in text for k in ["genai", "openai", "langchain", "crewai", "gemini"]):
                has_ai = True
        except Exception:
            pass
    for ts_file in list(d.rglob("*.ts")) + list(d.rglob("*.svelte")) + list(d.rglob("*.jsx")):
        try:
            text = ts_file.read_text(errors="ignore")
            if any(k in text for k in ["d3", "vis-network", "Chart", "chart.js"]):
                has_viz = True
            if any(k in text for k in ["genai", "openai", "gemini"]):
                has_ai = True
        except Exception:
            pass

    # Existing files list (relative to service dir)
    existing = [str(f.relative_to(d)) for f in d.rglob("*") if f.is_file()
                and "__pycache__" not in str(f) and ".pyc" not in str(f)]

    # Service type
    if has_ai:
        stype = ServiceType.AI_AGENT
    elif has_viz:
        stype = ServiceType.VISUALIZATION
    elif not has_frontend and has_service:
        stype = ServiceType.FAAS
    elif is_react:
        stype = ServiceType.REACT_CRUD
    elif is_svelte:
        stype = ServiceType.SVELTE_CRUD
    else:
        stype = ServiceType.UNKNOWN

    # Dev stage
    if component_count == 0 and route_file_count <= 1:
        stage = DevStage.SCAFFOLDED
    elif component_count <= 2 and route_file_count <= 2:
        stage = DevStage.EARLY
    elif component_count <= 5:
        stage = DevStage.DEVELOPED
    else:
        stage = DevStage.MATURE

    return ServicePattern(
        service_name     = service_name,
        service_type     = stype,
        dev_stage        = stage,
        has_models       = has_models,
        has_routes       = has_routes,
        has_service_py   = has_service,
        has_frontend     = has_frontend,
        is_svelte        = is_svelte,
        is_react         = is_react,
        has_ai           = has_ai,
        has_viz          = has_viz,
        component_count  = component_count,
        route_file_count = route_file_count,
        existing_files   = sorted(existing),
    )
