# Introduce circular dependency
from sample_arch.user_service.api import get_user


def fetch_user():
    return get_user()
