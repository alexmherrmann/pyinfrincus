version = File.read("pyproject.toml")[/^version\s*=\s*"(.+?)"/, 1]
exec "git tag -a v#{version} -m 'Release version #{version}'"
