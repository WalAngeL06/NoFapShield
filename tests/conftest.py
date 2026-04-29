import os
import sys
from pathlib import Path


_original_mkdir = os.mkdir


def _is_project_pytest_tmp_path(path) -> bool:
    try:
        return any(part.startswith(".pytest_tmp") for part in Path(os.fspath(path)).parts)
    except TypeError:
        return False


def _mkdir_with_readable_windows_acl(path, mode=0o777, *, dir_fd=None):
    # Test-only Windows workaround: Python 3.14 can apply mode 0o700 ACLs to
    # pytest basetemp/tmp_path directories in this sandbox such that the same
    # process cannot read them back. Limit the inherited-ACL fallback to
    # project-local .pytest_tmp* paths that pytest creates with mode 0o700.
    # This monkeypatch is global for the test process, but it does not affect
    # product runtime and avoids changing unrelated directory creation modes.
    if sys.platform == "win32" and mode == 0o700 and _is_project_pytest_tmp_path(path):
        mode = 0o777
    if dir_fd is None:
        return _original_mkdir(path, mode)
    return _original_mkdir(path, mode, dir_fd=dir_fd)


os.mkdir = _mkdir_with_readable_windows_acl


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
