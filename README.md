# KZSfluxusu - Wiki_RAG_System 🔍📚

Retrieval-Augmented Generation rendszer MediaWiki-oldalak feldolgozásához, lokális LLM (Mistral via Ollama), FAISS indexelés és Flask-alapú keresőfelület.

A Wiki RAG (retrieval-augmented generation) program egy intelligens információkinyerő és -feldolgozó rendszer, amely MediaWiki-alapú tartalmakból képes releváns válaszokat generálni természetes nyelven. Hasznos eszköz lehet magánszemélyeknek, akik személyes tudásbázist szeretnének építeni vagy gyorsan szeretnének eligazodni nagy mennyiségű wiki-alapú dokumentációban. Vállalkozások számára különösen előnyös, ha belső tudástárral rendelkeznek, és szeretnék azt kereshetővé, interaktívvá és könnyen hozzáférhetővé tenni munkatársaik számára, esetleg egy részét a klienseikkel. A rendszer gépi tanulást és nyelvi modelleket használ a pontosabb és kontextusfüggő válaszok érdekében. Alkalmazható ügyfélszolgálati rendszerekhez, belső keresők fejlesztéséhez vagy akár oktatási célokra is.

## ✨ Főbb jellemzők

- 🕸️ MediaWiki-oldalak lekérdezése `mwclient` használatával
- 🧠 Embedding generálás `paraphrase-multilingual-MiniLM-L12-v2` modellel 
- ⚡ FAISS-alapú keresés
- 🌐 Flask-alapú webes keresőfelület 

---

## 🧰 Követelmények

- Python 3.10+
- [Ollama](https://ollama.com/) (telepített és futó `mistral` modell)
- `venv` (vagy `virtualenv`) a környezet izolálásához


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