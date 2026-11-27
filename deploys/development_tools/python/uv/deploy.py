from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=astral-sh/uv
python_uv_version = "0.13.10"
python_uv_checksum = "bfe31619b549d39d9031cb2cadc5a95d1258efcad746628a3a6212da4ae5dfbf"
python_uvx_checksum = "844e0e7d7fc19c187ba4e23b256c1b9ae1e72ce02974e719979906d6fe0a76ad"

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
