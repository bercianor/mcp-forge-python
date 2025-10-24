"""Tool to expose user information."""


def whoami(jwt: str | None = None) -> str:
    """
    Expose information about the user.

    Args:
        jwt: Validated JWT from middleware.

    Returns:
        User information message.

    """
    if not jwt:
        return "JWT is empty. Information is not available"

    return f"Success! Data are in the following JWT. You have to decode it first. JWT: {jwt}"
