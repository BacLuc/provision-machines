from pyinfra import host
from operations.user import get_user_name

user = get_user_name()

if host.data.fluxcd["enabled"]:
    pass
