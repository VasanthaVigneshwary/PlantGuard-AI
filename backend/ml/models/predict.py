"""Backward-compatible import for the active ONNX inference implementation."""

try:
    from ..predict import predict_disease
except ImportError:  # Support legacy execution with ``backend`` as the working directory.
    from ml.predict import predict_disease

__all__ = ["predict_disease"]
