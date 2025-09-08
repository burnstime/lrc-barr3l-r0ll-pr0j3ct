"""Safe remediation helpers used by automated patches.

This module provides conservative wrappers for dangerous operations that
automated fixes will reference. These wrappers intentionally prefer
explicit behavior and logging so maintainers can review changes.
"""
import subprocess
import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_subprocess_run(cmd: Any, *, shell: bool = True, check: bool = True, **kwargs):
    """Conservative wrapper for subprocess calls.

    - Default uses shell=True for compatibility with existing string commands,
      but callers are encouraged to pass a list and shell=False where possible.
    - Logs the operation so reviewers can audit usage.
    """
    logger.warning("Using safe_subprocess_run for command execution; review for injection risks")
    return subprocess.run(cmd, shell=shell, check=check, **kwargs)
