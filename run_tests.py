import os
import sys
import subprocess


def main() -> int:
    args = [sys.executable, '-m', 'pytest', '-q']
    if not os.getenv('SLOW'):
        # Exclude slow tests by default
        args += ['-m', 'not slow']
    # Run backend tests by default; extend to frontend when added
    cmd = args + ['backend']
    print('Running:', ' '.join(cmd))
    return subprocess.call(cmd)


if __name__ == '__main__':
    raise SystemExit(main())


