"""Pure archive protocol checks shared by the launcher and shell wrapper."""
import ast
import posixpath
import re
import subprocess
import sys
import tarfile

APP_UPDATE_PROTOCOL = 2

def validate_update_package(archive_path):
    try:
        required = {'upgrade/launcher.py': None, 'upgrade/update.sh': None,
                    'upgrade/update_package.py': None}
        with tarfile.open(archive_path, 'r:*') as archive:
            for member in archive.getmembers():
                name = member.name
                while name.startswith('./'):
                    name = name[2:]
                if name.startswith('/') or '..' in name.split('/'):
                    raise ValueError('Unsafe archive path')
                name = posixpath.normpath(name)
                if not (member.isfile() or member.isdir()):
                    raise ValueError('Unsupported archive member: ' + name)
                if name == 'upgrade' and not member.isdir():
                    raise ValueError('Invalid upgrade directory')
                if name in required:
                    if required[name] is not None or not member.isfile():
                        raise ValueError('Duplicate or non-regular protocol member')
                    required[name] = archive.extractfile(member).read().decode('utf-8')
        launcher, wrapper = required['upgrade/launcher.py'], required['upgrade/update.sh']
        if launcher is None or wrapper is None:
            raise ValueError('Missing update protocol members')
        for name in ('upgrade/launcher.py', 'upgrade/update_package.py'):
            source = required[name]
            if source is None:
                raise ValueError('Missing update protocol member: ' + name)
            tree = ast.parse(source)
            compile(tree, name, 'exec')
            declarations = [node.value for node in tree.body
                            if isinstance(node, ast.Assign) and any(
                                isinstance(target, ast.Name) and target.id == 'APP_UPDATE_PROTOCOL'
                                for target in node.targets)]
            if len(declarations) != 1 or ast.literal_eval(declarations[0]) != 2:
                raise ValueError('Incompatible update protocol: ' + name)
        if not re.search(r'^APP_UPDATE_PROTOCOL=2$', wrapper, re.M):
            raise ValueError('Incompatible wrapper update protocol')
        if subprocess.run(['bash', '-n'], input=wrapper, universal_newlines=True, timeout=10).returncode:
            raise ValueError('Invalid replacement wrapper')
    except Exception as error:
        raise ValueError(str(error)) from error


if __name__ == '__main__':
    try:
        validate_update_package(sys.argv[1])
    except (ValueError, IndexError) as error:
        print('Application package rejected: ' + str(error), file=sys.stderr)
        sys.exit(1)
