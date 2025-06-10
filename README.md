# KZSfluxus - Wiki_RAG_System 🔍📚

Retrieval-Augmented Generation rendszer MediaWiki-oldalak feldolgozásához, lokális LLM (Mistral via Ollama), FAISS indexelés és Flask-alapú keresőfelület.

A Wiki RAG (retrieval-augmented generation) program egy intelligens információkinyerő és -feldolgozó rendszer, amely MediaWiki-alapú tartalmakból képes releváns válaszokat generálni természetes nyelven. Hasznos eszköz lehet magánszemélyeknek, akik személyes tudásbázist szeretnének építeni vagy gyorsan szeretnének eligazodni nagy mennyiségű wiki-alapú dokumentációban. Vállalkozások számára különösen előnyös, ha belső tudástárral rendelkeznek, és szeretnék azt kereshetővé, interaktívvá és könnyen hozzáférhetővé tenni munkatársaik számára, esetleg egy részét a klienseikkel. A rendszer gépi tanulást és nyelvi modelleket használ a pontosabb és kontextusfüggő válaszok érdekében. Alkalmazható ügyfélszolgálati rendszerekhez, belső keresők fejlesztéséhez vagy akár oktatási célokra is.

## ✨ Főbb jellemzők

- 🕸️ MediaWiki-oldalak lekérdezése `mwclient` használatával
- 🧠 Embedding generálás `paraphrase-multilingual-mpnet-base-v2` modellel 
- ⚡ FAISS-alapú keresés
- 🌐 Flask-alapú webes keresőfelület 

---

## 🧰 Követelmények

- Python 3.10+
- [Ollama](https://ollama.com/) (telepített és futó `mistral` modell)
- `venv` (vagy `virtualenv`) a környezet izolálásához

### Minimum hardverkövetelmények (CPU-only)

| Komponens | Specifikáció |
|----------|--------------|
| CPU | 8 magos processzor vagy több (pl. Intel i7 vagy AMD Ryzen 7) |
| RAM | 16 GB vagy több |
| Tárhely | Nagy sebességű SSD, legalább 50 GB szabad hely |
| Operációs rendszer | Linux (ajánlott) vagy Windows 10/11 |

### Minimum hardverkövetelmények (GPU)

| Komponens | Specifikáció |
|-----------|--------------|
| CPU | 4 magos processzor (pl. Intel i5 vagy AMD Ryzen 5) |
| RAM | 16 GB |
| GPU | NVIDIA GPU 8 GB VRAM-mel (pl. GTX 1080) |
| Tárhely | SSD, legalább 50 GB szabad hely |
| Operációs rendszer | Linux vagy Windows 10/11 |

### Optimális hardverkövetelmények (GPU)

| Komponens | Specifikáció |
|-----------|--------------|
| CPU | 8 magos processzor vagy több (pl. Intel i7/i9 vagy AMD Ryzen 7/9) |
| RAM | 32 GB vagy több |
| GPU | NVIDIA GPU 24 GB VRAM-mel (pl. RTX 3090 vagy A100) |
| Tárhely | Nagy sebességű SSD, legalább 100 GB szabad hely |
| Operációs rendszer | Linux (ajánlott) vagy Windows 10/11 |

## Telepítés:

```bash
git clone https://github.com/kzsfluxus/Wiki_RAG
cd Wiki_RAG
python3 -m venv .venv
pip3 install -r requirements-cpu.txt # CPU-only gépeken
pip3 install -r requirements-gpu.txt # NVIDIA GPU-t és CUDA-t használó gépeken
```
## Használat:

CLI:
```bash
./cli_start
```

WEB:
```bash
./web_start
```
A Flask-alapú RAG rendszer a következő címen érhető el:

http://localhost:5000
Főbb funkciók

A rendszer az alábbi HTTP végpontokat biztosítja:

- `/` Főoldal kérdés-válasz felülettel. A felhasználó szöveges kérdést adhat meg, amelyre a rendszer a háttérben betöltött wiki alapú tudásból generál választ. Hiba esetén részletes üzenetet jelenít meg.

- `/refresh` Manuális adatfrissítést végző POST végpont. Újra betölti a tudásbázist, új indexet épít, és frissíti az embeddingeket.

- `/api/ask` REST API POST végpont kérdések gépi feldolgozásához. A JSON törzsben question mezőt vár, és JSON válaszban adja vissza a választ.

- `/api/health` Egyszerű egészségügyi ellenőrző GET végpont, amely visszajelzést ad a rendszer inicializációs állapotáról és alapinformációkat nyújt.

- `/api/status` Részletes státusz-lekérdező GET végpont. Visszaadja, hogy a rendszer be van-e töltve, hány dokumentumot lát, az embedding modul működik-e, és néhány dokumentumcímet is felsorol.

## Konfiguráció

wiki_rag.conf

```conf
[wiki]
url = hu.wikipedia.org  # A mediawiki url-je
path = /w/              # Prefix, többnyire /w/ vagy /wiki/
username =              # Felhasználónév, amennyiben szükséges
password =              # Jelszó

[selected]
pages = Spanyolország   # Letöltendő oldal(ak)

[related]
root = Madrid           # További Madriddal kapcsolatos oldalak
limit = 50              # Letöltött oldalak maximális száma
```
## Képernyőképek

![config](images/config.png)
![loading](images/cli_load.png)
![web](images/web.png)