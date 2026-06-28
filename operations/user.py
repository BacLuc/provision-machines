from pyinfra.facts.server import User

from pyinfra import host


def get_user_name() -> str:
    return str(host.get_fact(User))
