import os
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
    directory_path = 'C:\\Solutions\\Python\\drawio_c4_lint\\c4_github_examples'  # Update this path to your specific top level directory
    lint_drawio_files(directory_path)
