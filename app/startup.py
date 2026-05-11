"""Windows startup registry helpers."""
import sys
import winreg
from pathlib import Path

_REG_PATH  = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_NAME  = "EODTracker"


def _startup_cmd() -> str:
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    main_py = str(Path(__file__).parent.parent / "main.py")
    return f'"{sys.executable}" "{main_py}"'


def get_startup_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, _REG_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_startup_enabled(enable: bool):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        if enable:
            winreg.SetValueEx(key, _REG_NAME, 0, winreg.REG_SZ, _startup_cmd())
        else:
            try:
                winreg.DeleteValue(key, _REG_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass
