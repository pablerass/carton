from .providers import BggProvider


def bgg_login(bgg: BggProvider, api_key: str | None = None,
              user: str | None = None, password: str | None = None) -> None:
    """Authenticate a provider with an API key, or with a user and password.

    Raises ValueError if the credentials are missing or both methods are given.
    Password login is a blocking request.
    """
    if api_key and password:
        raise ValueError("Only one of an API key or a password should be provided for authentication")
    if api_key:
        bgg.api_login(api_key)
    elif user and password:
        bgg.user_login(user, password)
    else:
        raise ValueError("An API key, or a user and a password, must be provided for authentication")
