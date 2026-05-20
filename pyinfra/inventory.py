import os

# noinspection PyShadowingBuiltins
all = ["@local"]
local = all

if os.getenv("CI"):
    ci = ["@local"]
