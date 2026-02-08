import json
import shlex
import subprocess
import tempfile
from io import IOBase
from typing import Tuple

from pyinfra.api.command import StringCommand
from pyinfra.api.exceptions import ConnectError
from pyinfra.connectors.base import BaseConnector
from pyinfra.connectors.util import (
    CommandOutput,
    make_unix_command_for_host,
    run_local_process,
)

# if TYPE_CHECKING:
#     from pyinfra.api.arguments import ConnectorArguments
#     from pyinfra.api.command import StringCommand


class Incus(BaseConnector):
    handles_execution = True

    @staticmethod
    def make_names_data(name=None):
        """
        Generate inventory targets from incus list.

        Args:
            name: If a string, filter to just that one container name.

        Yields:
            tuple: (name, data, groups)
        """
        result = subprocess.run(
            ["incus", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        containers = json.loads(result.stdout)
        names = [c["name"] for c in containers]

        if isinstance(name, str):
            # Filter to specific container
            if name not in names:
                raise ValueError(f"Container '{name}' not found in incus list")
            yield name, {}, []
        else:
            # Yield all containers
            for name in names:
                yield name, {}, []

    def run_shell_command(
        self,
        command: StringCommand,
        print_output: bool = False,
        print_input: bool = False,
        **arguments,
    ) -> Tuple[bool, CommandOutput]:
        """
        Execute a command on the container via incus exec.
        """
        container_name = self.host.name
        full_command = make_unix_command_for_host(self.state, self.host, command)

        # Build the incus exec command as a shell string
        shell_cmd = f"incus exec {shlex.quote(container_name)} -- {full_command}"

        print_prefix = f"{container_name}>>> " if print_output else ""

        if print_input:
            print(f"{container_name}>>> {full_command}")

        returncode, output = run_local_process(
            shell_cmd,
            print_output=print_output,
            print_prefix=print_prefix,
        )

        return returncode == 0, output

    def put_file(
        self,
        filename_or_io,
        remote_filename,
        remote_temp_filename=None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments,
    ) -> bool:
        """
        Upload a file to the container via incus file push.
        """
        container_name = self.host.name

        if isinstance(filename_or_io, IOBase):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(filename_or_io.read())
                tmp.flush()
                local_path = tmp.name
        else:
            local_path = filename_or_io

        target = f"{container_name}{remote_filename}"
        shell_cmd = f"incus file push {shlex.quote(local_path)} {shlex.quote(target)}"

        if print_input:
            print(f"{container_name}>>> pushing {local_path} to {remote_filename}")

        print_prefix = f"{container_name}>>> " if print_output else ""

        returncode, _ = run_local_process(
            shell_cmd,
            print_output=print_output,
            print_prefix=print_prefix,
        )

        return returncode == 0

    def get_file(
        self,
        remote_filename,
        filename_or_io,
        remote_temp_filename=None,
        print_output: bool = False,
        print_input: bool = False,
        **arguments,
    ) -> bool:
        """
        Download a file from the container via incus file pull.
        """
        container_name = self.host.name
        source = f"{container_name}{remote_filename}"

        if isinstance(filename_or_io, IOBase):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                local_path = tmp.name
        else:
            local_path = filename_or_io

        shell_cmd = f"incus file pull {shlex.quote(source)} {shlex.quote(local_path)}"

        if print_input:
            print(f"{container_name}>>> pulling {remote_filename} to {local_path}")

        print_prefix = f"{container_name}>>> " if print_output else ""

        returncode, _ = run_local_process(
            shell_cmd,
            print_output=print_output,
            print_prefix=print_prefix,
        )

        if isinstance(filename_or_io, IOBase):
            with open(local_path, "rb") as f:
                filename_or_io.write(f.read())

        return returncode == 0

    def connect(self) -> None:
        """
        Verify the container exists and is running.
        """
        container_name = self.host.name
        result = subprocess.run(
            ["incus", "list", "--format", "json", container_name],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise ConnectError(f"Failed to query container '{container_name}'")

        containers = json.loads(result.stdout)
        if not containers:
            raise ConnectError(f"Container '{container_name}' not found")

        status = containers[0].get("status", "").lower()
        if status != "running":
            raise ConnectError(
                f"Container '{container_name}' is not running (status: {status})"
            )

    def disconnect(self) -> None:
        """
        No-op for incus containers.
        """
        pass
