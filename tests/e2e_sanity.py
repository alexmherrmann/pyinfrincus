import os
import subprocess
import tempfile
import time
from random import randbytes

import pytest


@pytest.fixture(scope="module")
def container():
    name = f"pyinfrincus-{randbytes(4).hex()}"
    subprocess.run(["incus", "launch", "images:debian/13", name], check=True)

    # Wait for container to be RUNNING
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["incus", "list", name, "-f", "csv"],
            capture_output=True,
            text=True,
        )
        if "(eth0)" in result.stdout:
            break
        time.sleep(0.5)
    else:
        raise TimeoutError(f"Container {name} not RUNNING after 20s")

    yield name
    subprocess.run(["incus", "delete", "--force", name], check=True)


def run_pyinfra(container, *args):
    return subprocess.run(
        ["pyinfra", "-y", f"@incus/{container}", *args],
        capture_output=True,
        text=True,
    )


def test_container_exists(container):
    result = subprocess.run(
        ["incus", "info", container],
        capture_output=True,
    )
    assert result.returncode == 0


def test_linux_distribution_fact(container):
    result = run_pyinfra(container, "fact", "server.LinuxDistribution")
    assert result.returncode == 0, f"pyinfra failed:\n{result.stderr}"
    assert "Debian" in result.stderr, f"Expected 'Debian' in output:\n{result.stderr}"


def test_file_lifecycle(container):
    remote_path = "/tmp/pyinfrincus-test"

    with tempfile.TemporaryDirectory() as tmpdir:
        upload_path = os.path.join(tmpdir, "upload.txt")
        download_path = os.path.join(tmpdir, "download.txt")

        # Create a local file with "Hello"
        with open(upload_path, "w") as f:
            f.write("Hello")

        # Upload it
        result = run_pyinfra(container, "files.put", f"src={upload_path}", f"dest={remote_path}")
        assert result.returncode == 0, f"files.put failed:\n{result.stderr}"

        # Append " World"
        result = run_pyinfra(
            container, "exec", "--",
            f"echo -n ' World' >> {remote_path}",
        )
        assert result.returncode == 0, f"exec failed:\n{result.stderr}"

        # Download and verify
        result = run_pyinfra(container, "files.get", f"src={remote_path}", f"dest={download_path}")
        assert result.returncode == 0, f"files.get failed:\n{result.stderr}"

        contents = open(download_path).read()
        assert contents == "Hello World", f"Expected 'Hello World', got: {contents!r}"
