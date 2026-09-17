import os
import sys
from drawio_c4_lint.c4_lint import C4Lint

def lint_drawio_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.drawio'):
                file_path = os.path.join(root, file)
                try:
                    lint = C4Lint(file_path)
                    if lint.is_c4():
                        print(lint)
                except Exception as e:
                    print(f"Failed to initialize C4Lint for {file_path}: {e}")

if __name__ == "__main__":
    # diagram names are often non-ASCII; do not die on a legacy console codepage
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 2:
        sys.exit("usage: c4_lint_on_directory.py <directory of .drawio files>")
    lint_drawio_files(sys.argv[1])
