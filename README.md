# 📚 Complete Project Documentation: Fast Search for Saúde Caixa Accredited Network

**Author:** Nathan Dias Irigoyen  
**Base Folder:** DadosSaudeCaixa 
**Creation/Last Revision Date:** January/March 2026

## ⚠️ IMPORTANT LEGAL DISCLAIMER
This is an **independent project** and has **no official affiliation** with Caixa Econômica Federal or the Saúde Caixa health plan. The sole purpose is to optimize the visualization and search of data, which is extracted from public sources. To access the official portal, use the link: [https://saude.caixa.gov.br/RedeAtendimento/](https://saude.caixa.gov.br/RedeAtendimento/).

---

## 🎯 Project Overview and Architecture

The project consists of a three-stage solution for the ingestion, processing, and high-performance, secure delivery of accredited network data for web queries.

| Phase | Main Objective | Key Tools | Related Files |
| :---|:---|:---|:---|
| **1. Extraction (Scraping)** | Obtain raw data from the official website. | Python, Selenium, ChromeDriverManager. | `scraper_sc_html.py` |
| **2. Processing and Optimization** | Clean, structure, and shard the data for search. | Python, BeautifulSoup, Regex. | `Processa_html_para_json.py`, `sharding.py`, `rede_credenciada_final.zip` |
| **3. Deployment and Web Search** | Make data available on a web frontend, with a secure and fast backend. | JavaScript, Cloudflare Worker (`worker.js`), Cloudflare R2, R2 SDK (`upload.js`). | `index.html`, `ShardedProviderService.js`, `worker.js`, `upload.js` |

---

## 📂 Detailed File Structure

| File | Type | Full Description |
| :---|:---|:---|
| `Projeto_rede_credenciada.md` | Documentation | Project development log, detailing the scraper construction, cleaning utilities, and anti-scraping defense strategies. |
| `scraper_sc_html.py` | Python Script | Contains the navigation and HTML page extraction logic from the official website, including pagination handling. |
| `Processa_html_para_json.py`| Python Script | Performs the conversion of raw HTML files into a structured JSON file, cleaning texts and identifying key fields (Name, Council, CNPJ). |
| `rede_credenciada_final.json`| Data (JSON) | Consolidated file (example) containing all provider records, before sharding. Includes Individuals and Legal Entities (Pessoa Física and Pessoa Jurídica). |
| `sharding.py` | Python Script | Implements JSON sharding by State, City, or Specialty. Essential to optimize loading and searching in the web environment. |
| `index.html` | Frontend (HTML/JS) | User interface for the search. Presents the search form and cascading selection logic (State → City → Specialty). |
| `ShardedProviderService.js` | JS (API Client) | Module that encapsulates communication with the Backend (Cloudflare Worker), sending search filters and managing local cache. |
| `worker.js` | JS (Cloudflare Worker) | Backend logic. Validates the token, queries the file map to fetch the correct *shard* from R2, and executes the final filtering of results. |
| `upload.js` | JS (Deploy/R2) | Utility script to perform batch uploads of processed and static files to Cloudflare R2 storage (compatible with AWS S3 SDK). |

---

## ⚙️ Key Details and Mechanisms

### 1. Sharding and Search Optimization
The main performance strategy is data fragmentation (*sharding*):

* **Purpose:** Instead of loading a 200MB JSON file in the browser (slow and costly), the data is pre-divided (e.g., by State).
* **Logic:** `sharding.py` creates `mapa_arquivos.json`, which `worker.js` uses to fetch from Cloudflare R2 **only** the necessary data file (shard) for the selected State/City/Specialty.

### 2. Semi-Structured Data Handling
`Processa_html_para_json.py` handles data variability:

* **Identification:** Uses Regex to extract `Name` and `Professional Council` (CRM/CRO/CREFITO etc.) from the first line of each provider block.
* **Specialties:** `sharding.py` prioritizes the specialty in `ODONTOLOGIA` when the field is filled, falling back to `Especialidade(s)` in other cases, and to `Geral` (General) as a fallback.

### 3. Security (Backend)
The Cloudflare Worker/R2 architecture enhances security:

* **Database Protection:** Data *shards* are in R2, without direct public access.
* **Access Control:** `worker.js` requires an `X-Auth-Token` (defined in `ShardedProviderService.js` and `worker.js`) to process requests, preventing third parties from using the API without permission.

---

## 🛠️ Next Steps
1.  **Run `scraper_sc_html.py`** to obtain the updated raw HTML.
2.  **Run `Processa_html_para_json.py`** followed by **`sharding.py`** to generate the optimized JSON files and the map.
3.  **Update credentials** in the `upload.js`, `ShardedProviderService.js`, and `worker.js` files.
4.  **Run `upload.js`** to deploy the files to Cloudflare R2.
5.  **Configure the Worker** in Cloudflare to point to the R2 bucket.
