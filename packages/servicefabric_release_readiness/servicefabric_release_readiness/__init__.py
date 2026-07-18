"""Foundation release readiness checks for ServiceFabric."""

from .doctor import DoctorReport, run_doctor

__all__ = ["DoctorReport", "run_doctor"]
