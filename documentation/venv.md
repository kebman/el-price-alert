# Virtual environment

Recommended: keep a local `.venv` in the repo.

```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The public scripts prefer `.venv` automatically; no need for `.venv_path`.