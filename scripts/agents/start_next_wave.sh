#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/lib_wave.sh"
NEXT_WAVE=""; BASE_REF=""; DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --wave) NEXT_WAVE="${2:-}"; shift 2 ;;
        --base) BASE_REF="${2:-}"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        *) echo "Usage: start_next_wave.sh --wave NEXT_WAVE --base REF [--dry-run]" >&2; exit 2 ;;
    esac
done
[[ -n "$NEXT_WAVE" && -n "$BASE_REF" ]] || { echo "--wave and --base are required" >&2; exit 2; }
[[ "$NEXT_WAVE" =~ ^wave-[0-9]+$ ]] || { echo "wave must use the form wave-03" >&2; exit 2; }
BASE_SHA="$(git rev-parse --verify "${BASE_REF}^{commit}")" || { echo "base ref does not exist: $BASE_REF" >&2; exit 2; }
sf_load_config
ROOT="$(sf_repo_root)"
[[ "$(pwd -P)" == "$(cd "$SF_WT_INTEGRATION" && pwd -P)" ]] || { echo "Run this command from the integration worktree: $SF_WT_INTEGRATION" >&2; exit 2; }
for lane in $(sf_lanes); do
    path="$(sf_lane_path "$lane")"; sf_is_valid_worktree "$path" || { echo "$lane: invalid Git worktree: $path" >&2; exit 2; }; sf_is_clean "$path" || { echo "$lane: worktree is dirty: $path" >&2; exit 2; }
done
number="${NEXT_WAVE#wave-}"; number="${number#0}"; short="w$number"; integration_branch="integration/phase1-wave$number"
config_dir="config/agents/$NEXT_WAVE"; next_config="$ROOT/.agent-worktrees.$NEXT_WAVE.env"
[[ ! -e "$ROOT/$config_dir/wave.yaml" && ! -e "$next_config" ]] || { echo "next-wave configuration already exists" >&2; exit 2; }
declare -A branches=([integration]="$integration_branch" [supervisor]="agent/$short-supervisor" [runtime-bindings]="agent/$short-runtime-bindings" [kit-execution]="agent/$short-kit-execution" [reference-app]="agent/$short-reference-app")
for lane in "${!branches[@]}"; do git show-ref --verify --quiet "refs/heads/${branches[$lane]}" && { echo "branch already exists: ${branches[$lane]}" >&2; exit 2; }; done
if [[ "$DRY_RUN" == "1" ]]; then
    printf 'DRY-RUN: git switch -c %s %s\n' "$integration_branch" "$BASE_SHA"; printf 'DRY-RUN: generate %s and docs/workplans/parallel/%s\n' "$config_dir" "$NEXT_WAVE"
    for lane in supervisor runtime-bindings kit-execution reference-app; do printf 'DRY-RUN: git -C %s switch -c %s <bootstrap-sha>\n' "$(sf_lane_path "$lane")" "${branches[$lane]}"; done
    exit 0
fi
git switch -c "$integration_branch" "$BASE_SHA"
python3 - "$ROOT" "$NEXT_WAVE" "$BASE_SHA" "$integration_branch" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]); wave_id,base,branch=sys.argv[2:]; n=wave_id.removeprefix("wave-").lstrip("0") or "0"
lanes={"integration":(branch,"SF_WT_INTEGRATION"),"supervisor":(f"agent/w{n}-supervisor","SF_WT_SUPERVISOR"),"runtime-bindings":(f"agent/w{n}-runtime-bindings","SF_WT_RUNTIME_BINDINGS"),"kit-execution":(f"agent/w{n}-kit-execution","SF_WT_KIT_EXECUTION"),"reference-app":(f"agent/w{n}-reference-app","SF_WT_REFERENCE_APP")}
repl={"__WAVE_ID__":wave_id,"__BASE_REF__":base,"__INTEGRATION_BRANCH__":branch}
def render(source,target,extra={}):
 text=source.read_text(encoding="utf-8")
 for old,new in {**repl,**extra}.items(): text=text.replace(old,new)
 target.parent.mkdir(parents=True,exist_ok=True); target.write_text(text,encoding="utf-8")
render(root/"config/agents/templates/wave.yaml",root/f"config/agents/{wave_id}/wave.yaml")
for lane,(lane_branch,env) in lanes.items(): render(root/"config/agents/templates/task.yaml",root/f"config/agents/{wave_id}/tasks/{lane}.json",{"__LANE__":lane,"__BRANCH__":lane_branch,"__WORKTREE_ENV__":env})
for source in (root/"docs/workplans/parallel/template").glob("*.md"): render(source,root/f"docs/workplans/parallel/{wave_id}/{source.name}")
handoffs=root/f"docs/handoffs/{wave_id}"; handoffs.mkdir(parents=True,exist_ok=True)
(handoffs/"task-handoff-template.md").write_text("# Wave Task Handoff\n\nLane:\nBranch:\nBase commit:\nHead commit:\n\n## Changed Paths\n\n## Tests Executed\n\n## Contract Changes\n\n## Blockers\n",encoding="utf-8")
for lane in lanes: (handoffs/f"{lane}.md").write_text(f"# {wave_id} {lane} Handoff\n\nBootstrap template: `task-handoff-template.md`.\n",encoding="utf-8")
PY
git add "$config_dir" "docs/workplans/parallel/$NEXT_WAVE" "docs/handoffs/$NEXT_WAVE"; git commit -m "chore(agents): bootstrap $NEXT_WAVE development harness"; BOOTSTRAP_SHA="$(git rev-parse HEAD)"
cat > "$next_config" <<EOF
SF_WAVE_ID="$NEXT_WAVE"
SF_STATE_BASE="$SF_STATE_BASE"
SF_WT_INTEGRATION="$SF_WT_INTEGRATION"
SF_WT_SUPERVISOR="$SF_WT_SUPERVISOR"
SF_WT_RUNTIME_BINDINGS="$SF_WT_RUNTIME_BINDINGS"
SF_WT_KIT_EXECUTION="$SF_WT_KIT_EXECUTION"
SF_WT_REFERENCE_APP="$SF_WT_REFERENCE_APP"
EOF
export SF_AGENT_WORKTREES_ENV="$next_config"
for lane in supervisor runtime-bindings kit-execution reference-app; do path="$(sf_lane_path "$lane")"; git -C "$path" switch -c "${branches[$lane]}" "$BOOTSTRAP_SHA"; done
for lane in integration supervisor runtime-bindings kit-execution reference-app; do path="$(sf_lane_path "$lane")"; "$path/scripts/agents/init_worktree_runtime.sh" "$lane" "$path" "$SF_STATE_BASE" "$NEXT_WAVE"; (cd "$path"; source .agent-runtime.env; python3 scripts/agent/wave_task_preflight.py --wave "$NEXT_WAVE" --task "$lane" >/dev/null; python3 scripts/agent/render_wave_prompt.py --wave "$NEXT_WAVE" --task "$lane" --output ".agent-runs/$NEXT_WAVE/$lane/prompt.md" >/dev/null); done
echo "Bootstrap commit: $BOOTSTRAP_SHA"; echo "Run scripts/agents/wave_status.sh --wave $NEXT_WAVE"
