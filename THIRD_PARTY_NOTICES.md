# Third-Party Notices

Montage Maker uses or interacts with third-party software and tools. This file is
a practical notice file for the GitHub repository and release bundle. It is not a
complete legal audit. Before a major public release, regenerate dependency
licenses from the exact virtual environment used to build the app.

## Direct tools and dependencies

| Component | License / terms | How Montage Maker uses it | Bundled? |
|---|---|---|---|
| ImageMagick | ImageMagick License | Performs the actual montage generation through the `montage` command. | No. Users install it separately and keep it on PATH. |
| NiceGUI | MIT License | Provides the desktop GUI framework used by `app.py`. | Yes, when running from Python source or building a standalone executable. |
| FastAPI | MIT License | Used by the NiceGUI app for serving local output image previews. | Yes, as a Python dependency. |
| pywebview | BSD 3-Clause License | Provides the native desktop window layer used by the GUI stack. | Yes, as a Python dependency when installed. |
| PyInstaller | GPL 2.0 with bootloader exception / PyInstaller exception | Used by `build.py` to create standalone executables. | Build tool only; generated executable may include PyInstaller bootloader components. |
| Python | Python Software Foundation License Version 2 | Runtime used to run Montage Maker. A frozen executable may include parts of the Python runtime. | Yes, in standalone builds; otherwise installed separately by the user. |
| Microsoft Edge WebView2 Runtime | Microsoft WebView2 Runtime terms | Required by the Windows native webview layer on systems where it is not already installed. | No. Users install it separately if missing. |

## Notes

- ImageMagick is a separate system dependency. Montage Maker does not replace or
  relicense ImageMagick.
- ImageMagick requires acknowledgement when used or redistributed. Montage Maker
  acknowledges ImageMagick in the README, user guide, and this notice file.
- NiceGUI, FastAPI, pywebview, PyInstaller, Python, and their transitive
  dependencies remain under their own licenses.
- If you distribute a standalone executable, include this file and the LICENSE
  file in the release bundle.
- For a more complete dependency inventory, generate a license report from the
  exact virtual environment used to build the app.

## Suggested dependency report command

From an activated Montage Maker virtual environment:

```bash
python -m pip install pip-licenses
pip-licenses --format=markdown --with-urls --with-authors --output-file THIRD_PARTY_PYTHON_PACKAGES.md
```

For a more conservative release bundle, also include license text where available:

```bash
pip-licenses --format=plain-vertical --with-license-file --output-file THIRD_PARTY_PYTHON_LICENSE_TEXTS.txt
```

## Upstream links

- ImageMagick: https://imagemagick.org/
- ImageMagick License: https://imagemagick.org/license/
- NiceGUI: https://nicegui.io/
- NiceGUI License: https://github.com/zauberzeug/nicegui/blob/main/LICENSE
- FastAPI: https://github.com/fastapi/fastapi
- pywebview: https://github.com/r0x0r/pywebview
- PyInstaller license: https://pyinstaller.org/en/stable/license.html
- Python license: https://docs.python.org/3/license.html
- Microsoft WebView2 distribution info: https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
