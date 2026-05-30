from operations.filesystem import dirname_of
from operations.include_children import include_children

include_children(f"{dirname_of(__file__)}/deploys")
