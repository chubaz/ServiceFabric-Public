from .security_scan     import run_security_scan
from .code_review       import run_code_review
from .performance_audit import run_performance_audit
from .doc_sync          import run_doc_sync
from .type_check        import run_type_check
from .full_audit        import run_full_audit

TASK_REGISTRY = {
    "security_scan":     run_security_scan,
    "code_review":       run_code_review,
    "performance_audit": run_performance_audit,
    "doc_sync":          run_doc_sync,
    "type_check":        run_type_check,
    "full_audit":        run_full_audit,
}
