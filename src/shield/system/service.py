from __future__ import annotations

import subprocess


class NSSMService:
    SERVICE_NAME = "ShieldProtection"

    def __init__(self, nssm_path: str = "nssm") -> None:
        self._nssm = nssm_path

    def install(self, python_path: str, script_path: str) -> bool:
        """Runs: nssm install ShieldProtection <python_path> <script_path>
        Returns True on success (returncode == 0), False otherwise.
        """
        result = self._run("install", self.SERVICE_NAME, python_path, script_path)
        return result.returncode == 0

    def uninstall(self) -> bool:
        """Runs: nssm remove ShieldProtection confirm
        Returns True on success, False otherwise.
        """
        result = self._run("remove", self.SERVICE_NAME, "confirm")
        return result.returncode == 0

    def status(self) -> str:
        """Runs: nssm status ShieldProtection
        Returns stdout stripped, e.g. 'SERVICE_RUNNING', 'SERVICE_STOPPED'.
        Returns 'UNKNOWN' on any error.
        """
        try:
            result = self._run("status", self.SERVICE_NAME)
            return result.stdout.decode(errors="replace").strip()
        except Exception:
            return "UNKNOWN"

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        """Runs nssm with given args, capture_output=True, timeout=10"""
        return subprocess.run(
            [self._nssm, *args],
            capture_output=True,
            timeout=10,
        )
