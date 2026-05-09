# GitHub Actions Runners

This directory bootstraps self-hosted GitHub Actions runners with GitHub's official Actions Runner Controller (ARC) Helm charts.

Why this lives outside the main `agenticrag` chart:

- GitHub recommends running the ARC controller and runner pods in dedicated namespaces.
- GitHub Actions jobs execute arbitrary workflow code, so isolating runners from the application release is the safer default.
- The official ARC charts already manage the custom resources, listeners, and ephemeral runner lifecycle cleanly.

This setup uses GitHub-hosted OCI charts and the official runner image from GitHub Container Registry:

- Controller chart: `oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller`
- Runner chart: `oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set`
- Runner image: `ghcr.io/actions/actions-runner:latest`

## Files

- `runner-scale-set-values.yaml`: baseline values for the official `gha-runner-scale-set` chart

## Install

1. Install the ARC controller into a dedicated namespace:

```bash
helm install arc \
  --namespace arc-systems \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
```

2. Create a GitHub auth secret in the runner namespace.

GitHub recommends GitHub App auth for repository- or organization-level runners. Example:

```bash
kubectl create namespace arc-runners

kubectl create secret generic arc-github-auth \
  --namespace arc-runners \
  --from-literal=github_app_id=123456 \
  --from-literal=github_app_installation_id=654321 \
  --from-file=github_app_private_key=private-key.pem
```

3. Update `/Users/pragadeesh/Developer/AgenticRag/helm/github-runners/runner-scale-set-values.yaml`:

- Set `githubConfigUrl` to the repository or organization that should own the runners.
- Keep `githubConfigSecret` aligned with the secret you created.
- Adjust `runnerScaleSetName`, `minRunners`, and `maxRunners` for expected load.

4. Install the runner scale set:

```bash
helm install agenticrag-runners \
  --namespace arc-runners \
  --create-namespace \
  -f /Users/pragadeesh/Developer/AgenticRag/helm/github-runners/runner-scale-set-values.yaml \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

## Workflow target

Use the runner scale set name in GitHub Actions workflows:

```yaml
runs-on: agenticrag-runners
```

## Notes

- The baseline config uses `containerMode.type: dind`, which is the simplest starting point for mixed Docker-based CI jobs.
- If you need custom runner pod spec changes, GitHub's docs recommend replacing `containerMode` with an explicit `template.spec` block instead of mixing both.
- For production, pin chart versions with `--version` and consider pinning the runner image by digest after initial validation.
