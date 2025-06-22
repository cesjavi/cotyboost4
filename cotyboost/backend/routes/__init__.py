from .process_project import project_bp
from .train import train_bp
from .metrics import metrics_bp
from .logs import logs_bp
from .inference import inference_bp

__all__ = [
    'project_bp',
    'train_bp',
    'metrics_bp',
    'logs_bp',
    'inference_bp',
]
