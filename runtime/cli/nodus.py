import sys

def main():
    print("NODUS CLI v0.1")
    if len(sys.argv) < 2:
        print("Usage: nodus <command> [args]")
        return
    print(f"Executing command: {sys.argv[1]}")

if __name__ == "__main__":
    main()
