from pyinfra.operations import npm

# Install devcontainer-cli via npm
npm.packages(
    name="Install devcontainer-cli via npm",
    packages=["@devcontainers/cli"],
    global=True,
)