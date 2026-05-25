# polyglot-devops-microservices
Django rest framework + FastAPI + Go + | Docker | CI/CD | Kubernetes | AWS

## CI/CD flow

GitHub Actions workflow: `.github/workflows/ci-cd.yml`

- Pull requests into `main`, `staging`, or `prod` run lint, tests, build checks, and Trivy security scans.
- Pushes to `staging` run lint, tests, build checks, and blocking Trivy security scans.
- Pushes to `prod` run the same checks, build and push application images to DockerHub, then deploy them on EC2.
- `prod` pushes are accepted only when the pushed commit already exists in `staging`.
- Docker images are pushed to one DockerHub repository as:
  - `DOCKERHUB_USER_NAME/polyglot-devops-microservices:<service>-<git-sha>`
  - `DOCKERHUB_USER_NAME/polyglot-devops-microservices:<service>-prod`

Required GitHub repository secrets:

- `DOCKERHUB_USER_NAME`
- `DOCKERHUB_ACCESS_TOKEN`
- `PROD_EC2_HOST`
- `PROD_EC2_USER`
- `PROD_EC2_SSH_KEY`
- `PROD_DEPLOY_PATH`

Optional SonarQube/SonarCloud secrets:

- `SONAR_TOKEN`
- `SONAR_HOST_URL`
