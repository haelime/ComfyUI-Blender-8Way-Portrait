"""Dependency-free Windows Common Item Dialog integration."""

from __future__ import annotations

import ctypes
import os
import uuid
from ctypes import wintypes
from pathlib import Path

try:
    from .model_files import SUPPORTED_MODEL_EXTENSIONS, resolve_model_path
except ImportError:  # Direct module import in lightweight test environments.
    from model_files import SUPPORTED_MODEL_EXTENSIONS, resolve_model_path


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class COMDLG_FILTERSPEC(ctypes.Structure):
    _fields_ = [("pszName", wintypes.LPCWSTR), ("pszSpec", wintypes.LPCWSTR)]


def _guid(value: str) -> GUID:
    parsed = uuid.UUID(value)
    return GUID(
        parsed.time_low,
        parsed.time_mid,
        parsed.time_hi_version,
        (ctypes.c_ubyte * 8)(*parsed.bytes[8:]),
    )


def _method(interface, index, result_type, *argument_types):
    table = ctypes.cast(
        interface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
    ).contents
    return ctypes.WINFUNCTYPE(
        result_type, ctypes.c_void_p, *argument_types
    )(table[index])


def _check(result: int, operation: str) -> None:
    if result < 0:
        raise OSError(f"{operation} failed: HRESULT 0x{result & 0xFFFFFFFF:08X}")


def _initial_directory(value: str | None) -> Path:
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_file():
            return candidate.parent.resolve()
        if candidate.is_dir():
            return candidate.resolve()
    return Path.home()


def pick_model_file(initial_path: str | None = None) -> str | None:
    """Open the modern Explorer IFileOpenDialog and return a validated path."""
    if os.name != "nt":
        raise NotImplementedError("The native 3D model picker is available on Windows only.")

    ole32 = ctypes.windll.ole32
    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32

    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(GUID),
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(GUID),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    ole32.CoCreateInstance.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None
    shell32.SHCreateItemFromParsingName.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        ctypes.POINTER(GUID),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    shell32.SHCreateItemFromParsingName.restype = ctypes.c_long
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

    clsid_file_open_dialog = _guid("DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7")
    iid_file_open_dialog = _guid("D57C7288-D4AD-4768-BE02-9D969532D960")
    iid_shell_item = _guid("43826D1E-E718-42EE-BC55-A1E261C37BFE")
    clsctx_inproc_server = 0x1
    coinit_apartment_threaded = 0x2
    fos_forcefilesystem = 0x40
    fos_filemustexist = 0x1000
    fos_pathmustexist = 0x800
    fos_nochangedir = 0x8
    sigdn_filesyspath = 0x80058000
    cancelled_hresult = ctypes.c_long(0x800704C7).value

    initialized_result = ole32.CoInitializeEx(None, coinit_apartment_threaded)
    initialized = initialized_result in (0, 1)
    if not initialized:
        _check(initialized_result, "COM initialization")

    dialog = ctypes.c_void_p()
    selected_item = ctypes.c_void_p()
    initial_item = ctypes.c_void_p()
    path_pointer = ctypes.c_void_p()
    try:
        _check(
            ole32.CoCreateInstance(
                ctypes.byref(clsid_file_open_dialog),
                None,
                clsctx_inproc_server,
                ctypes.byref(iid_file_open_dialog),
                ctypes.byref(dialog),
            ),
            "IFileOpenDialog creation",
        )

        set_file_types = _method(
            dialog, 4, ctypes.c_long, ctypes.c_uint, ctypes.POINTER(COMDLG_FILTERSPEC)
        )
        get_options = _method(dialog, 10, ctypes.c_long, ctypes.POINTER(wintypes.DWORD))
        set_options = _method(dialog, 9, ctypes.c_long, wintypes.DWORD)
        set_folder = _method(dialog, 12, ctypes.c_long, ctypes.c_void_p)
        set_title = _method(dialog, 17, ctypes.c_long, wintypes.LPCWSTR)
        show = _method(dialog, 3, ctypes.c_long, wintypes.HWND)
        get_result = _method(dialog, 20, ctypes.c_long, ctypes.POINTER(ctypes.c_void_p))

        extension_pattern = ";".join(f"*{suffix}" for suffix in SUPPORTED_MODEL_EXTENSIONS)
        filters = (COMDLG_FILTERSPEC * 2)(
            COMDLG_FILTERSPEC("3D model files", extension_pattern),
            COMDLG_FILTERSPEC("All files", "*.*"),
        )
        _check(set_file_types(dialog, len(filters), filters), "file type filter setup")

        options = wintypes.DWORD()
        _check(get_options(dialog, ctypes.byref(options)), "dialog option read")
        _check(
            set_options(
                dialog,
                options.value
                | fos_forcefilesystem
                | fos_filemustexist
                | fos_pathmustexist
                | fos_nochangedir,
            ),
            "dialog option setup",
        )
        _check(set_title(dialog, "Choose a 3D model for Blender 8-way rendering"), "dialog title setup")

        initial_directory = _initial_directory(initial_path)
        create_result = shell32.SHCreateItemFromParsingName(
            str(initial_directory),
            None,
            ctypes.byref(iid_shell_item),
            ctypes.byref(initial_item),
        )
        if create_result >= 0 and initial_item:
            _check(set_folder(dialog, initial_item), "initial folder setup")

        show_result = show(dialog, user32.GetForegroundWindow())
        if show_result == cancelled_hresult:
            return None
        _check(show_result, "dialog display")
        _check(get_result(dialog, ctypes.byref(selected_item)), "selected item read")

        get_display_name = _method(
            selected_item, 5, ctypes.c_long, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)
        )
        _check(
            get_display_name(selected_item, sigdn_filesyspath, ctypes.byref(path_pointer)),
            "selected path conversion",
        )
        return str(resolve_model_path(ctypes.wstring_at(path_pointer.value)))
    finally:
        if path_pointer:
            ole32.CoTaskMemFree(path_pointer)
        for interface in (initial_item, selected_item, dialog):
            if interface:
                release = _method(interface, 2, ctypes.c_ulong)
                release(interface)
        if initialized:
            ole32.CoUninitialize()
