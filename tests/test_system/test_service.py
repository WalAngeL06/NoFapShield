from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from shield.system.service import NSSMService


@pytest.fixture
def mock_subprocess():
    with patch("shield.system.service.subprocess.run") as mock_run:
        yield mock_run


class TestNSSMServiceInstall:
    def test_install_calls_nssm(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        svc = NSSMService(nssm_path="nssm")
        result = svc.install("/path/to/python", "/path/to/script.py")
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "install" in call_args
        assert NSSMService.SERVICE_NAME in call_args

    def test_install_passes_python_and_script_paths(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        svc = NSSMService(nssm_path="nssm")
        svc.install("/usr/bin/python3", "/app/main.py")
        call_args = mock_subprocess.call_args[0][0]
        assert "/usr/bin/python3" in call_args
        assert "/app/main.py" in call_args

    def test_install_returns_false_on_nonzero_returncode(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 1
        svc = NSSMService(nssm_path="nssm")
        result = svc.install("/path/to/python", "/path/to/script.py")
        assert result is False

    def test_install_uses_custom_nssm_path(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        svc = NSSMService(nssm_path="/custom/nssm.exe")
        svc.install("/python", "/script.py")
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "/custom/nssm.exe"


class TestNSSMServiceUninstall:
    def test_uninstall_calls_nssm_remove(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        svc = NSSMService(nssm_path="nssm")
        result = svc.uninstall()
        assert result is True
        call_args = mock_subprocess.call_args[0][0]
        assert "remove" in call_args
        assert NSSMService.SERVICE_NAME in call_args
        assert "confirm" in call_args

    def test_uninstall_returns_false_on_failure(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 1
        svc = NSSMService(nssm_path="nssm")
        result = svc.uninstall()
        assert result is False


class TestNSSMServiceStatus:
    def test_status_returns_stdout_stripped(self, mock_subprocess):
        mock_run = MagicMock()
        mock_run.stdout = b"SERVICE_RUNNING\r\n"
        mock_subprocess.return_value = mock_run
        svc = NSSMService(nssm_path="nssm")
        assert svc.status() == "SERVICE_RUNNING"

    def test_status_calls_nssm_status(self, mock_subprocess):
        mock_run = MagicMock()
        mock_run.stdout = b"SERVICE_STOPPED"
        mock_subprocess.return_value = mock_run
        svc = NSSMService(nssm_path="nssm")
        svc.status()
        call_args = mock_subprocess.call_args[0][0]
        assert "status" in call_args
        assert NSSMService.SERVICE_NAME in call_args

    def test_status_returns_unknown_on_exception(self, mock_subprocess):
        mock_subprocess.side_effect = Exception("nssm not found")
        svc = NSSMService(nssm_path="nssm")
        assert svc.status() == "UNKNOWN"

    def test_status_returns_unknown_on_timeout(self, mock_subprocess):
        import subprocess
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="nssm", timeout=10)
        svc = NSSMService(nssm_path="nssm")
        assert svc.status() == "UNKNOWN"


class TestNSSMServiceRun:
    def test_run_passes_capture_output_and_timeout(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        svc = NSSMService(nssm_path="nssm")
        svc._run("status", "ShieldProtection")
        _, kwargs = mock_subprocess.call_args
        assert kwargs.get("capture_output") is True
        assert kwargs.get("timeout") == 10

    def test_run_prefixes_nssm_path(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        svc = NSSMService(nssm_path="/opt/nssm")
        svc._run("status", "ShieldProtection")
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "/opt/nssm"
        assert call_args[1] == "status"
        assert call_args[2] == "ShieldProtection"
