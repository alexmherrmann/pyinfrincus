import subprocess
from random import randbytes

import pytest


@pytest.fixture(scope="module")
def container():
    name = f"pyinfrincus-{randbytes(4).hex()}"
    subprocess.run(["incus", "launch", "images:debian/13", name], check=True)
    yield name
    subprocess.run(["incus", "delete", "--force", name], check=True)


def test_container_exists(container):
    result = subprocess.run(
        ["incus", "info", container],
        capture_output=True,
    )
    assert result.returncode == 0
