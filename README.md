# Spotify hitų prognozavimo platforma

Sistema prognozuoja, ar Spotify kūrinys yra "hitas" (`popularity >= 50`) arba "ne hitas" (`popularity < 50`), pagal jo garso požymius (`danceability`, `energy`, `tempo`, ir pan.), `explicit` žymą ir žanrą. 

## Reikalavimai
Docker, kind, kubectl, Python 3.11+, git. Apie 2 GB laisvo RAM.

## Paleidimas nuo nulio

### 1. Repo ir Python aplinka
```bash
git clone https://github.com/yasns/mlops-individual && cd mlops-individual
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Duomenys
Jei DVC remote (`~/dvcstore`) yra šiame kompiuteryje:
```bash
dvc pull
```
Jei ne (pvz., kitas kompiuteris) – atsisiųsti tą pačią rinkinio reviziją iš Hugging Face:
```bash
python src/fetch_data.py
```

### 3. Klasteris ir MLflow
```bash
kind create cluster --config k8s/kind-config.yaml
kubectl apply -f k8s/namespace.yaml -f k8s/mlflow.yaml
kubectl rollout status deployment/mlflow -n mlops
```
Pirmą kartą užtrunka kelias minutes, kol atsisiunčiamas MLflow vaizdas.

### 4. Prieiga prie MLflow
Atskirame terminale (palikti veikti):
```bash
kubectl port-forward -n mlops svc/mlflow 5000:5000
```
MLflow UI: http://127.0.0.1:5000

### 5. Pipeline'as
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000 # Jei turite direnv, galite šią komandą praleisti
dvc repro
```
Jei niekas nepasikeitė, `dvc repro` praleidžia visus etapus. Naujam run'ui su tais pačiais parametrais – `dvc repro -f`.

### 6. Hiperparametrų paieška (Optuna)
```bash
python src/tune.py              # 10 bandymų
N_TRIALS=20 python src/tune.py
```
Geriausią `C` įrašyti į `params.yaml` (`train.C`) ir paleisti `dvc repro`.

### 7. Istorinio run'o atkūrimas
Run ID nukopijuoti iš MLflow UI (run'o puslapio antraštė). Darbinis medis turi būti švarus (`git status`).
```bash
time python reproduce.py <run_id>
```
Atkuria to run'o kodą (git), duomenis (DVC) ir parametrus, perleidžia pipeline'ą ir palygina metrikas. UI atsiranda naujas run'as su žyma `reproduces=<run_id>`.

### 8. Mokymas klasteryje naudojant Kubernetes Job
Reikia sukurti secret'ą (vieną kartą) per CLI:
```bash
kubectl create secret generic mlflow-credentials -n mlops \
  --from-literal=MLFLOW_TRACKING_URI=http://mlflow.mlops.svc.cluster.local:5000
```
Hiperparametrai ConfigMap'e `k8s/train-config.yaml`. Pakeitus reikia vėl pritaikyti:
```bash
kubectl apply -f k8s/train-config.yaml
kubectl delete job train -n mlops --ignore-not-found
kubectl apply -f k8s/train-job.yaml
kubectl wait --for=condition=complete job/train -n mlops --timeout=600s
kubectl logs -n mlops job/train
```
Pod'as iš `ghcr.io/yasns/mlops-individual` vaizdo atsisiunčia duomenis, paleidžia `prepare` -> `train` ir log'ina run'ą į klasterio MLflow.

### 9. Modelio registras
```bash
python src/promote.py           # registruoja naują run'ą iš models/run_id.txt ir suteikia @champion aliasą
python src/promote.py <run_id>  # konkrečiam run'ui
```
Modelis `spotify-hits` matomas MLflow UI skiltyje Models.

### 10. Prognozių API
API modelį nuskaito iš registro Pod'o paleidimo metu.
```bash
kubectl apply -f k8s/api.yaml
kubectl rollout status deployment/spotify-api -n mlops
kubectl port-forward -n mlops svc/spotify-api 8000:80   # atskirame terminale
```
Health check ir pavyzdys: įvertinkime pirmas 2 eilutes iš test.csv:
```bash
curl -s localhost:8000/health
python -c "import pandas as pd; print(pd.read_csv('data/processed/test.csv').drop(columns='target').head(2).to_json(orient='records'))" \
  | curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' -d @-
```

### 11. Rollback
```bash
python src/promote.py rollback   # @champion -> ankstesnė versija
kubectl rollout restart deployment/spotify-api -n mlops
kubectl rollout status deployment/spotify-api -n mlops
curl -s localhost:8000/health    # "version" turi sumažėti
```

## Rezultatai
| Kas | Kur |
|-----|-----|
| MLflow UI (run'ai, parametrai, metrikos, modeliai) | http://127.0.0.1:5000, eksperimentas `spotify-hits`, be prisijungimo |
| Hiperparametrų paieška | MLflow UI: run'as `optuna-C` su įdėtiniais `trial-N` |
| Modelio registras | MLflow UI, skiltis Models: `spotify-hits@champion` |
| Pipeline'o metrikos | `metrics.json`, `dvc metrics show` |
| Vėlinimas, pralaidumas | `docs/load-test.json` (`python scripts/loadtest.py http://127.0.0.1:8000 200 10`) |
| CI/CD paleidimai | [GitHub Actions](https://github.com/yasns/mlops-individual/actions) |
| Reikalavimai (FR, NFR, KPI) | `docs/requirements.md` |
| Docker vaizdai | [`ghcr.io/yasns/mlops-individual`](https://github.com/users/yasns/packages/container/package/mlops-individual) (U2), [`ghcr.io/yasns/u1-train`](https://github.com/users/yasns/packages/container/package/u1-train) (U1) |
| Vaizdo dydis, Trivy skenavimas | `docs/image-size.txt`, `docs/trivy-scan.txt` |

## Išjungimas
Dėmesio: ištrina ir visus MLflow run'us (PVC).
```bash
kind delete cluster --name mlops
```
