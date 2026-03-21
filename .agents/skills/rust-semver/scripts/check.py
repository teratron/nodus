import subprocess
import sys
import shutil


def check_cargo_semver():
    print("Checking for cargo-semver-checks...")

    if not shutil.which("cargo-semver-checks"):
        print("cargo-semver-checks not found. Attempting to install...")
        try:
            subprocess.run(["cargo", "install", "cargo-semver-checks"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to install cargo-semver-checks: {e}")
            sys.exit(1)

    print("Running SemVer compatibility checks...")
    try:
        # Use shell=True specifically if we were on Windows and needed to handle some path issues,
        # but for direct cargo commands it's usually fine without.
        result = subprocess.run(["cargo", "semver-checks"], check=False)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"An error occurred while running checks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_cargo_semver()
