# InsightIQ CI/CD: Jenkins + Docker + Ansible

Git push -> Jenkins -> pytest inside Docker -> build image -> push to Docker Hub -> Ansible starts MySQL + InsightIQ containers -> smoke test.

## What was added to InsightIQ
| File | Purpose |
|---|---|
| `Dockerfile` | Stage 1 runs `pytest`; stage 2 is the slim production image (Python 3.12, non-root user, healthcheck) |
| `Jenkinsfile` | Checkout, Test, Build Image, Push Image, Deploy with Ansible, Smoke Test |
| `ansible/deploy.yml` | Creates a Docker network, runs MySQL 8 (persistent volume), then the app (uploads volume), waits for `/health` |
| `tests/` + `pytest.ini` | 8 tests using a throwaway SQLite DB, so CI needs no MySQL |
| `requirements.txt` | Fixed: it listed `google-genai` but the code imports `groq`, so the image would have crashed at startup |
| `.env.example` | Template. The real `.env` is NOT included and must never be committed |
| `sample_data/sales_data.csv` | CSV to upload in the deployed app for your screenshots |
| `scripts/setup-ubuntu.sh` | Installs Docker, Jenkins, Ansible on an Ubuntu VM |


## No Jenkins or Ansible installed? Run Jenkins in Docker (easiest on Windows)
You only need **Docker Desktop** (with the WSL2 backend). Jenkins, Docker CLI and Ansible all run inside one container.
```bash
cd jenkins-docker
docker compose up -d --build
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
Open `http://localhost:8080`, enter that password, install suggested plugins, then continue from **Step 2** below (skip Step 1 and the setup script).
Notes:
- The app is deployed to your PC's Docker and opens at `http://localhost:8000`.
- The compose file sets `APP_HOST=host.docker.internal` so the health checks inside Jenkins can reach the app.
- Use a **public** GitHub repo and a **public** Docker Hub repo so Jenkins and Ansible can pull without extra login.
- Docker Desktop must stay running while you demo.

## Step 1: Prepare a machine (skip if using Jenkins in Docker)
Ubuntu 22.04/24.04 VM (VirtualBox/VMware = non-cloud; EC2/Azure VM = cloud), 2 CPU / 4 GB RAM minimum.
```bash
bash scripts/setup-ubuntu.sh
```
Open `http://<vm-ip>:8080`, enter the printed admin password, install suggested plugins, create your admin user. Cloud VM: open ports 8080 (Jenkins) and 8000 (app).

## Step 2: Push to GitHub
```bash
git init && git add . && git commit -m "InsightIQ CI/CD"
git branch -M main
git remote add origin https://github.com/<you>/insightiq-cicd.git
git push -u origin main
```
Check `git status` first: `.env` must not appear (it is in `.gitignore`).

## Step 3: Configure
1. Replace `your-dockerhub-username` in `Jenkinsfile` (`DOCKERHUB_USER`) and `ansible/deploy.yml` (`image_name`). Commit and push.
2. Create a Docker Hub access token (Account Settings > Security).
3. Jenkins > Manage Jenkins > Credentials > Global > Add credentials:

| ID (exact) | Kind | Value |
|---|---|---|
| `dockerhub-creds` | Username with password | Docker Hub username + token |
| `insightiq-db-password` | Secret text | A MySQL password for the app (letters and digits only) |
| `groq-api-key` | Secret text | Your Groq API key |
| `app-secret-key` | Secret text | Any long random string |

## Step 4: Create the pipeline job
Jenkins > New Item > **Pipeline** > Pipeline script from SCM > Git > repo URL, branch `*/main`, script path `Jenkinsfile`.
Trigger: **Poll SCM** `* * * * *` (works on a private VM) or a GitHub webhook to `http://<jenkins-ip>:8080/github-webhook/` (needs a public IP).

## Step 5: Run and verify
Click **Build Now**. When green:
```bash
docker ps                          # insightiq-app and insightiq-db running
curl http://localhost:8000/health  # {"status":"ok",...}
```
Open `http://<vm-ip>:8000`, go to Upload, upload `sample_data/sales_data.csv`, then view Dashboard, Analytics and AI Insights (Groq).
Live demo: edit a visible text in `frontend/templates/dashboard.html`, push, and watch Jenkins redeploy automatically.

## Remote server instead of the same VM
In `ansible/inventory.ini` replace the `localhost` line with the remote host line. On the Jenkins VM run `sudo -u jenkins ssh-keygen`, then `ssh-copy-id` to the target. The target needs Docker and `python3-docker`. Change the smoke-test URLs in `Jenkinsfile` to the server IP.

## Screenshots for the submission
1. Jenkins stage view, all green
2. Console output ending in `Finished: SUCCESS` (secrets appear as `****`)
3. Docker Hub repo with the pushed tags
4. Ansible stage output (`ok` / `changed`)
5. `docker ps` showing both containers
6. InsightIQ dashboard in the browser after uploading the sample CSV
7. AI Insights page
8. A second build after a code change

## Troubleshooting
| Problem | Fix |
|---|---|
| `permission denied ... docker.sock` | `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins` |
| `ansible-playbook: not found` | `sudo apt install ansible` |
| `community.docker` not found | `sudo ansible-galaxy collection install community.docker -p /usr/share/ansible/collections` |
| App container restarting | `docker logs insightiq-app` (usually DB still starting; it retries automatically) |
| AI Insights shows "unavailable" | `groq-api-key` credential missing or wrong; re-run the build |
| Credentials not found | IDs must match the table exactly |
