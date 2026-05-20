from operations.github_release_binary import github_release_binary

# renovate: datasource=github-releases depName=astral-sh/uv
python_uv_version = "0.6.0"
python_uv_checksum = "becf19e97d1fd659d2ad44c3e753ab5f3dd6551de64e39241170ae883ce570a2"
python_uvx_checksum = "80ad7e812aac189dedf7451e1680640a013adaebece2844489b8b5321ed3f27f"

github_release_binary(
    url=f"https://releases.astral.sh/github/uv/releases/download/{python_uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
    binary_name="uv",
    checksum=python_uv_checksum,
    strip_components=1,
)


github_release_binary(
    url=f"https://releases.astral.sh/github/uv/releases/download/{python_uv_version}/uv-x86_64-unknown-linux-gnu.tar.gz",
    binary_name="uvx",
    checksum=python_uvx_checksum,
    strip_components=1,
)
