# pyinfrincus

A small package linking [pyinfra](https://pyinfra.com) and [incus](https://linuxcontainers.org/incus/)

### The `incus` connector

The most useful part of this package is the connector. It is both an `inventory` and `executing` connectorl. Once you have added this package to your pyproject or requirements.txt, you may do things like `pyinfra @incus/my-instance-name-1 fact server.LinuxName` (you may also omit the container name to run against ALL containers).

For now, the available options are just as follows.

| connector string | meaning            |
| ---------------- | ------------------ |
| `@incus`         | All instances      |
| `@incus/NAME`    | Run against `NAME` |
