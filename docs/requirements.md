# Projekto reikalavimai
Versija: 1.2  
Data: 2026-10-21  
Autoriai: Matas Jasiūnas (@yasns)  

## 1. Problemos aprašymas
Sistema prognozuoja, ar Spotify kūrinys yra "hitas" (`popularity >= 50`) arba "ne hitas" (`popularity < 50`), pagal jo garso požymius (`danceability`, `energy`, `tempo`, ir pan.), `explicit` žymą ir žanrą. 

## 2. Funkciniai reikalavimai (FR)
| ID | Reikalavimas | Prioritetas |
|-------|-------------------------------------|-------------|
| FR-01 | Sistema priima Parquet duomenų rinkinį ir viena komanda (`dvc repro`) grąžina train/test skaidymą, modelį ir `metrics.json` | Must |
| FR-02 | Kiekvienas mokymo run'as į klasterio MLflow log'ina parametrus, metrikas, `git_commit` ir `dvc_raw_md5` žymas bei modelį | Must |
| FR-03 | Bet kuris istorinis run'as atkuriamas pagal run ID (`python reproduce.py <id>`) | Must |

## 3. Nefunkciniai reikalavimai (NFR)
| ID | Kategorija | Reikalavimas | Metrika/KPI |
|--------|---------------|---------------------------|--------------------|
| NFR-01 | Kokybė | Modelis randa didelę dalį hitų, pažymėtų sąrašas lieka naudingas | Recall ≥ 0,30; Precision ≥ 0,60 |
| NFR-02 | Atkartojamumas | Istorinis run'as atkuriamas greitai ir tiksliai | Atkūrimo trukmė ≤ 120 s; Δ accuracy ≤ 0,005 |
| NFR-03 | Atsekamumas | Kiekvienas run'as susietas su kodu ir duomenimis | Run'ų su `git_commit` ir `dvc_raw_md5` žymomis = 100 % |
| NFR-04 | Patvarumas | MLflow duomenys išlieka perkūrus Pod'ą | Prarastų run'ų = 0 |
| NFR-05 | Saugumas | Docker vaizde nėra kritinių pažeidžiamumų | CRITICAL pažeidžiamumų (Trivy) = 0 |
| NFR-06 | Versijavimas | Docker vaizdai žymimi commit'u, ne `latest` | Tag'ų `sha-<commit>` formatu = 100 % |
| NFR-07 | Našumas | Pipeline'as įvykdomas greitai | `dvc repro -f` trukmė ≤ 120 s |
| NFR-08 | Sąžiningumas | Hitai aptinkami vienodai visuose žanruose | TPR skirtumas tarp žanrų ≤ 20%. |

## 4. Keitimo istorija
| Versija | Data | Autorius | Pakeitimai |
|---------|------------|----------|--------------------|
| 1.0 | 2026-10-21 | M. Jasiūnas | Pradinis dokumentas. Problemos aprašymas, FR-01..03, NFR-01..07 |
| 1.1 | 2026-10-21 | M. Jasiūnas | Sąžiningumas. NFR-08 |
| 1.2 | 2026-10-21 | M. Jasiūnas | Modelis pakeistas į LogisticRegression. Atnaujintas NFR-01 |
