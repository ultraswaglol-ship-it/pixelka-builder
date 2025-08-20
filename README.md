# One-click APK build for Flet (GitHub Actions)

## How to use
1. Copy the `.github/workflows/build-apk.yml` file from this folder into your project repository (same level as your Python files like `dashboard_flet.py`).
2. Commit and push to `main`.
3. In GitHub: **Actions → Build Flet APK → Run workflow** (or push again to trigger).
4. When the job finishes, go to the run page → **Artifacts** → download `app-apk`. Inside you’ll find the compiled `.apk`.

### Notes
- `--module-name` is set to `dashboard_flet` (your entry file should be `dashboard_flet.py`). Change it if your entry point is different.
- If you have Python deps, add a `requirements.txt` at repo root.
- This APK is signed with a debug key. For Google Play release, create a keystore and set up release signing (ask if you want a ready workflow).