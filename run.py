from pyinfra.operations import apt

from operations.filesystem import dirname_of
from operations.include_children import include_children

apt.update(
    name="Update apt cache",
    _sudo=True,
)

include_children(f"{dirname_of(__file__)}/deploys")
