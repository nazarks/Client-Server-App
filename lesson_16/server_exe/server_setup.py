import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["app_utils", "log", "server", "sqlite3"],
}
setup(
    name="message_server",
    version="0.0.1",
    description="Message server",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "server.py",
            # base='Win32GUI',
            targetName="server.exe",
        )
    ],
)
