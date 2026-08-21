from pyinfra import host

from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=astral-sh/uv
python_uv_version = "0.12.5"
python_uv_checksum = "b65f23a420c4acc96427efb30e5ed9bc0f7e25d2d712000f6ede77c1a0de5f46"
python_uvx_checksum = "ddad2a0e3ac263c86d578c0840d04325ee662ce406f45a09ed938433f11dd628"

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
