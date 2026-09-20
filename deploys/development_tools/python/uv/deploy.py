from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=astral-sh/uv
python_uv_version = "0.12.10"
python_uv_checksum = "173d95a0c32d18c896c46ba6fafbf3cf9c14ab74b033f81b76c883ef492a976b"
python_uvx_checksum = "848d0e261119e5b8f35db10164635e46a48bec29ceb1f8ec14a6fc76004973ee"

enabled = host.data.python["uv"]["enabled"]

github_release_binary(
    url=f"https://releases.astral.sh/github/uv/releases/download/{python_uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
    binary_name="uv",
    checksum=python_uv_checksum,
    strip_components=1,
    _if=enabled,
)


github_release_binary(
    url=f"https://releases.astral.sh/github/uv/releases/download/{python_uv_version}/uv-x86_64-unknown-linux-musl.tar.gz",
    binary_name="uvx",
    checksum=python_uvx_checksum,
    strip_components=1,
    _if=enabled,
)
