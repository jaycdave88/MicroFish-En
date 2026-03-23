"""
API routing module
"""

import traceback as _traceback_module
from flask import Blueprint

from ..config import Config


graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)


def error_response_body(error: Exception) -> dict:
    """Build error response body, only including traceback in debug mode."""
    body = {
        "success": False,
        "error": str(error),
    }
    if Config.DEBUG:
        body["traceback"] = _traceback_module.format_exc()
    return body


from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401

