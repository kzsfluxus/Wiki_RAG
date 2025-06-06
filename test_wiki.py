#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""

# Teszt script a wiki letöltés ellenőrzéséhez
import os
from pathlib import Path

# Ellenőrizzük a fájlokat
print("🔍 Fájlok ellenőrzése...")
print(f"Jelenlegi könyvtár: {os.getcwd()}")

# Konfig fájl
config_file = "wiki_rag.conf"
if Path(config_file).exists():
    print(f"✅ Konfig fájl megtalálva: {config_file}")
    with open(config_file, 'r') as f:
        print("📄 Konfig tartalom:")
        print(f.read())
else:
    print(f"❌ Konfig fájl hiányzik: {config_file}")
    print("📝 Hozd létre a következő tartalommal:")
    print("""
[wiki]
url = hu.wikipedia.org
path = /w/
username = 
password = 

[selected]
pages = Magyarország, Budapest, Debrecen

[related]
root = 
limit = 50
    """)

# Data könyvtár
data_dir = Path("data")
if data_dir.exists():
    print(f"✅ Data könyvtár létezik: {data_dir}")
    files = list(data_dir.glob("*"))
    if files:
        print("📁 Data könyvtár tartalma:")
        for f in files:
            print(f"  - {f.name}")
    else:
        print("📁 Data könyvtár üres")
else:
    print(f"❌ Data könyvtár hiányzik: {data_dir}")

# Wiki fájl
wiki_file = "data/wiki_pages.json"
if Path(wiki_file).exists():
    print(f"✅ Wiki fájl létezik: {wiki_file}")
    import json
    with open(wiki_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📊 Dokumentumok száma: {len(data)}")
else:
    print(f"❌ Wiki fájl hiányzik: {wiki_file}")

# Most próbáljuk meg a letöltést
print("\n🔄 Wiki letöltés próbálkozás...")
try:
    from retriever import auto_fetch_from_config
    print("✅ Retriever modul betöltve")
    auto_fetch_from_config()
    print("✅ Wiki letöltés befejezve")
except ImportError as e:
    print(f"❌ Retriever modul import hiba: {e}")
except Exception as e:
    print(f"❌ Wiki letöltés hiba: {e}")
    import traceback
    traceback.print_exc()

# Ellenőrizzük újra a fájlt
if Path(wiki_file).exists():
    print(f"✅ Wiki fájl most már létezik: {wiki_file}")
else:
    print(f"❌ Wiki fájl még mindig hiányzik: {wiki_file}")# -*- coding: utf-8 -*-
