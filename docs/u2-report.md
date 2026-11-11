# U2 ataskaita

## Architektūra

### CI/CD
`.github/workflows/ci-cd.yaml`, paleidžiamas `git push` į `main` metu:
1. `test` (`ubuntu-24.04`) – `ruff` + `pytest`
2. `train` (self-hosted) – port-forward į MLflow, `fetch_data`, `dvc repro`, run'as log'inamas į klasterio MLflow, tada kokybės patikra `src/gate.py`: kiekviena `metrics.json` metrika turi būti >= slenkstis iš `params.yaml` (`gate`). Nepraėjus – job'as raudonas, toliau niekas nevyksta
3. `release` (`ubuntu-24.04`) – vaizdo build (amd64 + arm64) ir push į `ghcr.io/yasns/mlops-individual:sha-<commit>`, `k8s/*.yaml` atnaujinami nauju tag'u ir kartu su `dvc.lock`, `metrics.json`, `models/run_id.txt` commit'inami (`deploy sha-...`)
4. `deploy` (self-hosted) – `src/promote.py` (nauja versija -> `@champion`), `kubectl apply` + `rollout restart`, `/health` patikra

`train` ir `deploy` vyksta self-hosted runner'yje šiame kompiuteryje, nes klasteris ir MLflow lokalūs, o GitHub debesies runner'iai jų nepasiekia. Runner'iui reikia `kubectl` prieigos prie `kind-mlops` ir `python3.12`.

### Klasteris
kind klasteris `mlops`, namespace `mlops`:
- `mlflow` – Deployment + PVC + Service (U1): tracking serveris ir modelių registras
- `spotify-api` – Deployment + Service: `uvicorn src.serve:app`, `MODEL_URI=models:/spotify-hits@champion`. Alias'as nuskaitomas Pod'o paleidimo metu
- `train` – Job: hiperparametrai iš ConfigMap `train-params`, MLflow URI iš Secret `mlflow-credentials` (sukuriama per CLI lokaliai).

## Matavimai

| Metrika | Reikšmė | Šaltinis |
|---|---|---|
| p50 / p95 / p99 | 37,4 / 146,3 / 156,3 ms | `docs/load-test.json` (200 užklausų, 10 lygiagrečių, 1 replika, per port-forward) |
| Pralaidumas | 217,8 RPS | `docs/load-test.json` |
| Modelis | 12 KB | `du -k models/model.pkl` |
| Vaizdas | 1,06 GB (228 MB suspaustas) | `docs/image-size.txt` |
| Rollback | 13,8 s | žemiau |
| CRITICAL pažeidžiamumai (NFR-05) | 1: `mlflow 3.15.2`, CVE-2026-116692, pataisyta 3.17.0. **Neįvykdyta** | `docs/trivy-scan.txt` (`sha-0c456de`) |
| TPR skirtumas tarp žanrų (NFR-08) | 100 %, 45 iš 70 žanrų TPR = 0. **Neįvykdyta** | `docs/fairness-report.json` |

## Mokymo Job įrodymas

```text
((.venv) ) jsn@Matass-MacBook-Air mlops-individual % kubectl delete job train -n mlops --ignore-not-found && kubectl apply -f k8s/train-job.yaml
job.batch/train created
((.venv) ) jsn@Matass-MacBook-Air mlops-individual % kubectl wait --for=condition=complete job/train -n mlops --timeout=600s && kubectl get job train -n mlops
job.batch/train condition met
NAME    STATUS     COMPLETIONS   DURATION   AGE
train   Complete   1/1           60s        60s
```

## CI/CD įrodymas

| Paleidimas | Commit'as | Rezultatas |
|---|---|---|
| [Žalias](https://github.com/yasns/mlops-individual/actions/runs/43090339631) | `0c456de` | `test` → `train` (vartas praėjo) → `release` → `deploy`: vaizdas `sha-0c456de`, commit'as `deploy sha-0c456de`, `@champion` -> v2 |
| [Raudonas](https://github.com/yasns/mlops-individual/actions/runs/43093840652) | `3b6d4c6` | `train` krenta ties vartu: `GATE FAIL: recall=0.0000 < 0.3; precision=0.0000 < 0.6`. `release` ir `deploy` praleisti, API liko su v2 |

Raudonas commit'as atšauktas (`088d076`).

## Rollback įrodymas

```text
((.venv) ) jsn@Matass-MacBook-Air mlops-individual % curl -s localhost:8000/health
{"status":"ok","model_uri":"models:/spotify-hits@champion","version":"2","run_id":"f4c134c7abd740b884be8af18d0ca78f"}%                                                                                          ((.venv) ) jsn@Matass-MacBook-Air mlops-individual % time (python src/promote.py rollback \
  && kubectl rollout restart deployment/spotify-api -n mlops \
  && kubectl rollout status deployment/spotify-api -n mlops)
spotify-hits @champion: v2 -> v1
deployment.apps/spotify-api restarted
Waiting for deployment spec update to be observed...
Waiting for deployment "spotify-api" rollout to finish: 0 out of 1 new replicas have been updated...
Waiting for deployment "spotify-api" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "spotify-api" rollout to finish: 1 old replicas are pending termination...
deployment "spotify-api" successfully rolled out
( python3 src/promote.py rollback && kubectl rollout restart  -n mlops &&    )  0.05s user 0.02s system 0% cpu 13.841 total
((.venv) ) jsn@Matass-MacBook-Air mlops-individual % curl -s localhost:8000/health
{"status":"ok","model_uri":"models:/spotify-hits@champion","version":"1","run_id":"778f3f73ab6a413c9dca7ba2406df794"}%
```

Rollback'as perkelia tik alias'ą registre. API pod'ą reikia perkrauti, nes `@champion` nuskaitomas paleidimo metu.
