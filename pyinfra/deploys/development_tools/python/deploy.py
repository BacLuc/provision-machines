from operations.filesystem import dirname_of
from operations.include_children import include_children
from pyinfra import host

if host.data.python["enabled"]:
    include_children(f"{dirname_of(__file__)}")
