from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=astral-sh/uv
python_uv_version = "0.12.10"
python_uv_checksum = "d81fcbac0a85c070a16cd3e8f3c1ef3b5592deda01a84234bec04a7f3c7105fe"
python_uvx_checksum = "b8704f4a037b92dc8c0d79f0801befa25dd3b86c81407556e692b0fba76813d1"

enabled = host.data.python["uv"]["enabled"]

github_release_binary(
    url=f"https://releases.astral.sh/github/uv/releases/download/{python_uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
    binary_name="uv",
    checksum=python_uv_checksum,
    strip_components=1,
    _if=enabled,
)


github_release_binary(
    url=f"https://releases.astral.sh/github/uv/releases/download/{python_uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
    binary_name="uvx",
    checksum=python_uvx_checksum,
    strip_components=1,
    _if=enabled,
)
