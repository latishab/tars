"""Version information for TARS SDK."""

__version__ = "0.3.4"
__version_tuple__ = (0, 3, 4)
__minimum_compatible_client__ = "0.1.0"
__git_commit__ = None  # Set during build

def get_version_info():
    """Return version information as dict."""
    import platform
    return {
        "version": __version__,
        "version_tuple": __version_tuple__,
        "minimum_compatible_client": __minimum_compatible_client__,
        "git_commit": __git_commit__,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
