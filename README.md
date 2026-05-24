# polyglot-devops-microservices
Django rest framework + FastAPI + Go + | Docker | CI/CD | Kubernetes | AWS

## CI/CD flow

GitHub Actions workflow: `.github/workflows/ci-cd.yml`

- Pull requests into `main`, `staging`, or `prod` run lint, tests, build checks, and a Trivy security scan.
- Pushes to `main` run the same checks, detect which Dockerized service changed, then build and push only those images.
- Docker images are pushed to one DockerHub repository as:
  - `DOCKERHUB_USER_NAME/polyglot-devops-microservices:<service>-<git-sha>`
  - `DOCKERHUB_USER_NAME/polyglot-devops-microservices:<service>-main`

Required GitHub repository secrets:

- `DOCKERHUB_USER_NAME`
- `DOCKERHUB_ACCESS_TOKEN`

Optional SonarQube/SonarCloud secrets:

- `SONAR_TOKEN`
- `SONAR_HOST_URL`
