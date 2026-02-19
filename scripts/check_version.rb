tag = ENV["GITHUB_REF_NAME"] || `git describe --tags --exact-match 2>/dev/null`.chomp
ver = tag.delete_prefix("v")
version = File.read("pyproject.toml")[/^version\s*=\s*"(.+?)"/, 1]
abort "tag '#{tag}' does not match pyproject.toml version #{version}" if ver != version
