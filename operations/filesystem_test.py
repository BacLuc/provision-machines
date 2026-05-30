from tempfile import NamedTemporaryFile

from filesystem import dirname_of


def test_dirname_of() -> None:
    with NamedTemporaryFile() as temp_file:
        assert dirname_of(temp_file.name) == temp_file.name.rsplit("/", 1)[0]
