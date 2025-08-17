# Startup commands on Windows (run only once)

## From repo root

```powershell
# optional local venv:
.\scripts\setup_venv.ps1

# test:
.\scripts\run_now.ps1

# (optional) schedule daily run:
.\scripts\register_task.ps1 -Time 15:00
```

## Advanced

Use a custom venv location:

```powershell
.\scripts\setup_venv.ps1 -VenvPath "$env:USERPROFILE\project_envs\python_envs\el-price-alert\venv"
```