from pyinfra import host
from pyinfra.facts.server import User


def get_user_name() -> str:
    return str(host.get_fact(User))
