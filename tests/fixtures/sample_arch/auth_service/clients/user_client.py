# auth_service/clients/user_client.py
# This creates a cycle
from user_service.auth.verify import verify_user


def get_user_info():
    verify_user()
