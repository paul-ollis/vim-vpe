"""Small module to install Rich tracebacks if available."""

try:
    from rich.traceback import install
except ImportError:
    pass
else:
    install()
