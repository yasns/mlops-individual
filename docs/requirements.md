# Projekto reikalavimai
Versija: 1.6  
Data: 2026-11-11  
Autoriai: Matas Jasiūnas (@yasns)  

## 1. Problemos aprašymas
Sistema prognozuoja, ar Spotify kūrinys yra "hitas" (`popularity >= 50`) arba "ne hitas" (`popularity < 50`), pagal jo garso požymius (`danceability`, `energy`, `tempo`, ir pan.), `explicit` žymą ir žanrą. 

## 2. Funkciniai reikalavimai (FR)
| ID | Reikalavimas | Prioritetas |
|-------|-------------------------------------|-------------|
| FR-01 | Sistema priima Parquet duomenų rinkinį ir viena komanda (`dvc repro`) grąžina train/test skaidymą, modelį ir `metrics.json` | Must |
| FR-02 | Kiekvienas mokymo run'as į klasterio MLflow log'ina parametrus, metrikas per žingsnius, sistemos metrikas, duomenų rinkinį (`log_input`), `git_commit`, `dvc_raw_md5` ir `seed` žymas bei modelį su aplinka | Must |
| FR-03 | Bet kuris istorinis run'as atkuriamas pagal run ID (`python reproduce.py <id>`) | Must |
| FR-04 | Hiperparametrų paieška (Optuna, >= 5 bandymai) log'inama kaip įdėtiniai run'ai klasterio MLflow | Must |
| FR-05 | Inferencijos API klasteryje (`/health`, `/predict`) modelį ima iš registro pagal alias'ą: `models:/spotify-hits@champion` | Must |
| FR-06 | CD grandinė: testai -> `dvc repro` -> kokybės vartas (NFR-01) -> vaizdo build/push -> manifesto atnaujinimas -> deploy. Vartui nepraėjus, deploy neįvyksta | Must |
| FR-07 | `@champion` grąžinamas į ankstesnę modelio versiją viena komanda (`python src/promote.py rollback`) | Must |

## 3. Nefunkciniai reikalavimai (NFR)
| ID | Kategorija | Reikalavimas | Metrika/KPI |
|--------|---------------|---------------------------|--------------------|
| NFR-01 | Kokybė | Modelis randa didelę dalį hitų, pažymėtų sąrašas lieka naudingas | Recall >= 0,30; Precision >= 0,60 |
| NFR-02 | Atkartojamumas | Istorinis run'as atkuriamas greitai ir tiksliai | Atkūrimo trukmė <= 120 s; Δ accuracy <= 0,005 |
| NFR-03 | Atsekamumas | Kiekvienas run'as susietas su kodu ir duomenimis | Run'ų su `git_commit` ir `dvc_raw_md5` žymomis = 100 % |
| NFR-04 | Patvarumas | MLflow duomenys išlieka perkūrus Pod'ą | Prarastų run'ų = 0 |
| NFR-05 | Saugumas | Docker vaizde nėra kritinių pažeidžiamumų | CRITICAL pažeidžiamumų (Trivy) = 0 |
| NFR-06 | Versijavimas | Docker vaizdai žymimi commit'u, ne `latest` | Tag'ų `sha-<commit>` formatu = 100 % |
| NFR-07 | Našumas | Pipeline'as įvykdomas greitai | `dvc repro -f` trukmė <= 120 s |
| NFR-08 | Sąžiningumas | Hitai aptinkami vienodai visuose žanruose | TPR skirtumas tarp žanrų <= 20 % |
| NFR-09 | Našumas | `/predict` vėlinimas (1 eilutė, 10 lygiagrečių užklausų, 1 replika, per port-forward) | p95 <= 200 ms; išmatuota: 146,3 ms (200 užklausų, `docs/load-test.json`) |
| NFR-10 | Pralaidumas | API aptarnauja apkrovą su 1 replika | >= 50 RPS; išmatuota: 217,8 RPS (200 užklausų, `docs/load-test.json`) |
| NFR-11 | Dydis | Modelio artefaktas ir vaizdas racionalaus dydžio | Modelis <= 1 MB, vaizdas <= 1,2 GB; išmatuota: 12 KB, 1,06 GB (228 MB suspaustas, `docs/image-size.txt`) |
| NFR-12 | Patikimumas | Rollback į ankstesnę modelio versiją pakankamai greitas | <= 120 s; išmatuota: 13,8 s (`docs/u2-report.md`) |

## 4. Keitimo istorija
| Versija | Data | Autorius | Pakeitimai |
|---------|------------|----------|--------------------|
| 1.0 | 2026-10-21 | M. Jasiūnas | Pradinis dokumentas. Problemos aprašymas, FR-01..03, NFR-01..07 |
| 1.1 | 2026-10-21 | M. Jasiūnas | Sąžiningumas. NFR-08 |
| 1.2 | 2026-10-21 | M. Jasiūnas | Modelis pakeistas į LogisticRegression. Atnaujintas NFR-01 |
| 1.3 | 2026-11-11 | M. Jasiūnas | Pilnas tracking'as: išplėstas FR-02. Optuna: FR-04 |
| 1.4 | 2026-11-11 | M. Jasiūnas | Registras ir inferencijos API: FR-05, NFR-09..11 |
| 1.5 | 2026-11-11 | M. Jasiūnas | CD su kokybės patikra: FR-06 |
| 1.6 | 2026-11-11 | M. Jasiūnas | Rollback: FR-07, NFR-12 |
