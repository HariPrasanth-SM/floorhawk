"""Download a revision-pinned checkpoint, verifying bytes before installation."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent


def verify(path, spec):
    if path.stat().st_size != spec['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != spec['sha256']:
        raise ValueError('Checkpoint size/SHA256 mismatch')


def main():
    spec = json.loads((ROOT / 'model.json').read_text())
    target = ROOT / 'weights' / spec['filename']
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        verify(target, spec)
    else:
        url = f"https://huggingface.co/{spec['repository']}/resolve/{spec['revision']}/{spec['filename']}"
        temporary = target.with_suffix('.part')
        try:
            with urllib.request.urlopen(url, timeout=30) as source, temporary.open('wb') as dest:
                while chunk := source.read(1024 * 1024):
                    dest.write(chunk)
            verify(temporary, spec)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    print(target)


if __name__ == '__main__':
    main()
