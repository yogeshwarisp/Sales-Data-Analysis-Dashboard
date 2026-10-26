# Uploading the Project to GitHub (from VS Code, on Windows)

## 1. One-time Git setup

Open the VS Code terminal and run (use your own name and email):

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 2. Before you commit: safety check

- `.gitignore` already excludes `venv/`, `__pycache__/`, `.env` and `data/sales.db`.
- This project needs **no passwords or API keys**. Never commit files that contain them.
- Decide about the dataset: the Superstore CSV comes from Kaggle, so check the dataset's licence/terms. If unsure, keep `data/sales_data.csv` out of the repo
  (add `data/sales_data.csv` to `.gitignore`) and tell readers in the README where to download it. The cleaned CSV is derived data and the pipeline recreates it.

## 3. Create the local repository

From the project root:

```powershell
git init
git add .
git status
git commit -m "Initial commit: sales data analysis dashboard"
git branch -M main
```

`git status` shows what will be committed. Check that `venv/` is **not** listed.

## 4. Create the GitHub repository

1. Sign in at github.com → **New repository**.
2. Name: `Sales-Data-Analysis-Dashboard`. Leave it **empty** (do not tick "Add a README").
3. Copy the repository URL.

## 5. Connect and push

```powershell
git remote add origin https://github.com/YOUR-USERNAME/Sales-Data-Analysis-Dashboard.git
git push -u origin main
```

The first push opens a browser window to sign in. Success looks like: `Branch 'main' set up to track 'origin/main'.`

**Common errors**
- `remote origin already exists` → `git remote set-url origin <URL>`
- `failed to push some refs` (README created on GitHub) → `git pull origin main --allow-unrelated-histories`, then push again.
- Large file warning → the `.pbix` is normally small (a few MB). GitHub rejects files above 100 MB.

## 6. Later changes

```powershell
git add .
git commit -m "Describe what you changed"
git push
```

Or use the VS Code **Source Control** panel (the branch icon): type a message, click **Commit**, then **Sync Changes**.

## 7. Make the repository look professional

- Add a short repository description and topics: `data-analysis`, `python`, `sql`, `power-bi`, `pandas`.
- Check that the README screenshots display (`images/dashboard_overview.png`).
- Pin the repository on your GitHub profile.
- Commit in small steps with clear messages (e.g. "Add SQL analysis queries").
