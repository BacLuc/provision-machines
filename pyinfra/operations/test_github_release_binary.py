import testinfra


def test_docker_file(helpers):
    def check(host: testinfra.host.Host):
        host.run_test("test -f /testfile")

    helpers.run_container_test_host(
        "ubuntu:22.04",
        "files.file path=/testfile mode=755 user=nobody",
        check,
    )
