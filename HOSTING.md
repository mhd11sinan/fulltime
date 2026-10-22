# Hosting Fulltime on GitHub Pages

Fulltime is a single static `index.html`, so GitHub Pages can host it for free.
Your site will be at `https://<your-username>.github.io/fulltime/`.

> Accounts and public profiles need a Supabase project; see [SUPABASE.md](SUPABASE.md).
> Until `config.js` is filled in, ratings are saved only in each visitor's browser.

## Option A: upload in the browser (no Git needed)

1. Sign in at https://github.com and click **New** (or go to https://github.com/new).
2. Repository name: `fulltime`. Choose **Public**. GitHub Pages on the free plan needs a public repo.
   Leave "Add a README" unticked. Click **Create repository**.
3. On the empty repo page, click **uploading an existing file**.
4. Drag in everything from this folder: `index.html`, `README.md`, `CLAUDE.md`, `HOSTING.md`, `.nojekyll`.
   (Windows Explorer hides files that start with a dot. Turn on View > Show > Hidden items to see `.nojekyll`.
   The site still works without it.)
5. Click **Commit changes**.
6. Go to **Settings > Pages**. Under **Build and deployment**, set Source to **Deploy from a branch**,
   Branch to **main** and folder to **/ (root)**, then click **Save**.
7. Wait 1 to 2 minutes and refresh the Pages settings. The live URL appears at the top.

To update the site later, open `index.html` on GitHub, click the pencil icon (or **Add file > Upload files**),
and commit. Pages redeploys automatically.

## Option B: Git on the command line

1. Install Git: `winget install --id Git.Git -e`, then open a new terminal.
2. Set your identity once:

       git config --global user.name "Your Name"
       git config --global user.email "you@example.com"

3. Create an empty repo named `fulltime` on GitHub (steps 1 and 2 of Option A).
4. In this folder, run:

       git init -b main
       git add .
       git commit -m "Initial commit"
       git remote add origin https://github.com/<your-username>/fulltime.git
       git push -u origin main

   The first push opens a browser window to sign in to GitHub.
5. Turn on Pages as in step 6 of Option A.

To update later: `git add .`, then `git commit -m "Describe the change"`, then `git push`.

## Optional: GitHub CLI

With the GitHub CLI (`winget install --id GitHub.cli -e`, then `gh auth login`), steps 3 to 4 of Option B
become a single command run in this folder after `git init` and the first commit:

    gh repo create fulltime --public --source . --push

## Automatic match updates

`.github/workflows/update-matches.yml` runs every Friday at 06:00 UTC (11:30 IST). It fetches finished
Champions League matches from football-data.org, appends any new ones to `index.html`, commits and pushes,
and GitHub Pages redeploys. One-time setup:

1. Register for a free API key at https://www.football-data.org/client/register. The key arrives by email.
2. In the repo, go to **Settings > Secrets and variables > Actions > New repository secret**.
   Name: `FOOTBALL_DATA_TOKEN`. Secret: your key. Click **Add secret**.
3. To run it right away, go to **Actions > Update matches > Run workflow**.

If a run fails with "Unrecognised club names", add the name to `ALIASES` in `scripts/update_matches.py`.
GitHub emails you when a scheduled run fails.

## Checking it works

- Open the Pages URL. The Matches tab should list 36 results.
- Rate a match, reload the page, and confirm the rating is still there.
- Until Supabase is set up, the People tab says accounts aren't set up yet. This is expected.
