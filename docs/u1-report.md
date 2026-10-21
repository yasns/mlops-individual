# U1 ataskaita

**Duomenys:** `maharshipandya/spotify-tracks-dataset` (Hugging Face, revizija `635b034`).
**Modelis:** `LogisticRegression` + `StandardScaler` (C=0.01).

## Kas padaryta

| Reikalavimas | Kur |
|---|---|
| R1 Repo ir reikalavimai | README, `docs/requirements.md` v1.2 |
| R2 Pipeline'as | `dvc.yaml`, `params.yaml`, `dvc.lock`, `.dvc/config` (remote `~/dvcstore`), `reproduce.py` (~17 s) |
| R3 Docker vaizdas | `docker/Dockerfile`, `ghcr.io/yasns/u1-train:sha-7983c97`, `docs/image-size.txt`, `docs/trivy-scan.txt` |
| R4 Klasteris ir MLflow | `k8s/kind-config.yaml`, `k8s/namespace.yaml`, `k8s/mlflow.yaml` |
| E2 Mokymas kaip Kubernetes Job | `k8s/train-job.yaml` |

## Kas neveikė
- MLflow Pod'o statusas OOMKilled su 1 GiB limitu (4 worker'iai). Limitas padidintas iki 2 GiB.
- GHCR push'o metu sulaukiau `error from registry: denied`, nors token'as turėjo `write:packages`. Pavyko pakartojus.
- Žanras galimai iš dalies atsitiktinis. Po deduplikacijos pagal `track_id` daina gauna abėcėlėje pirmą žanrą.
- NFR-08 neįvykdytas. TPR skirtumas tarp žanrų 100%, 45 iš 70 žanrų TPR = 0. Panašu, jog modelis hitus spėja pagal žanrą.
- Seni RandomForest modelio run'ai nebeatkuriami dabartiniu `reproduce.py`, nes pasikeitė hiperparametrai.
- MLflow atmetė užklausas iš klasterio (`403 Invalid Host header`). Pridėjau `--allowed-hosts` whitelist'ą.
- Job run'ai neturėjo `git_commit` (vaizde nėra `.git`), todėl `reproduce.py` jų negalėtų atkurti. Pridėjau `GIT_COMMIT` env.

## Laikas

| Reikalavimas | Laikas |
|---|---|
| R1 Repo ir reikalavimai | 3 h 43 min |
| R2 Pipeline'as | 2 h 40 min |
| R3 Docker vaizdas | 18 min |
| R4 Klasteris ir MLflow | 22 min |
| E2 Mokymas kaip Kubernetes Job | 41 min |
| **Iš viso** | **7 h 44 min** |
