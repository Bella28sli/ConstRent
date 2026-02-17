# Runner for existing GitLab (`8999:80`)

This setup does **not** start a new GitLab instance.  
It starts only `gitlab-runner` and registers it in your existing GitLab.

## 1) Configure

```powershell
cd infra/gitlab
copy .env.example .env
```

Set values in `.env`:

- `GITLAB_URL=http://host.docker.internal:8999`
- `GITLAB_CLONE_URL=http://host.docker.internal:8999`
- `GITLAB_RUNNER_TOKEN=<your_project_or_group_runner_token>`

## 2) Start runner

```powershell
docker compose -f docker-compose.gitlab.yml --env-file .env up -d
```

## 3) Re-register runner (if token changed)

```powershell
docker compose -f docker-compose.gitlab.yml --env-file .env down
docker volume rm runner_config
docker compose -f docker-compose.gitlab.yml --env-file .env up -d
```

## 4) About artifacts and 500 errors

If your existing GitLab stores artifacts in a bind mount and returns `500`,
switch artifacts path to a Docker volume in that GitLab deployment.

For Omnibus GitLab the target path is:

- `/var/opt/gitlab/gitlab-rails/shared/artifacts`

Migrate old artifacts once from bind mount to volume, then restart GitLab.

