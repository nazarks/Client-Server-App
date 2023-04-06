import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["app_utils", "log", "client", "sqlite3"],
}
setup(
    name="message_client",
    version="0.0.1",
    description="Message client",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "client.py",
            # base='Win32GUI',
            targetName="client.exe",
        )
    ],
)
