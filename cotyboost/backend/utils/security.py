import re
from werkzeug.utils import secure_filename

def validate_project_id(project_id):
    """
    Validates the project_id to prevent path traversal and other injection attacks.
    Returns the sanitized project_id if valid, or None if invalid.
    """
    if not project_id:
        return None

    # Basic sanitization
    sanitized = secure_filename(project_id)

    # Ensure it matches expected pattern (alphanumeric, underscores, dashes)
    if not re.match(r'^[a-zA-Z0-9_-]+$', sanitized):
        return None

    return sanitized
