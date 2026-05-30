from pyinfra import host

from operations.filesystem import dirname_of
from operations.include_children import include_children

if host.data.python["enabled"]:
    include_children(f"{dirname_of(__file__)}")
