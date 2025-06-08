#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Interface for Wiki RAG System
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""
import logging
import sys
from rag_system import RAGSystem, RAGInitializationError, RAGQueryError
import warnings
import os
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'

warnings.filterwarnings("ignore", category=DeprecationWarning)


# Logging beállítása CLI módhoz
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Egyszerűbb formátum a CLI-hez
)
logger = logging.getLogger(__name__)


def print_banner():
    """Alkalmazás banner kiírása"""
    print("=" * 60)
    print("🚀 Wiki RAG CLI - Interaktív Kérdés-Válasz Rendszer")
    print("=" * 60)


def print_help():
    """Súgó kiírása"""
    print("\n📋 Elérhető parancsok:")
    print("  - Írj be egy kérdést a válasz eléréséhez")
    print("  - 'help' vagy '?' - ez a súgó")
    print("  - 'status' - rendszer státusz")
    print("  - 'refresh' - adatok frissítése")
    print("  - 'quit', 'exit' vagy üres sor - kilépés")
    print()


def print_status(rag_system: RAGSystem):
    """Rendszer státusz kiírása"""
    try:
        info = rag_system.get_system_info()

        print("\n📊 Rendszer státusz:")
        print(f"  ✅ Inicializálva: {'Igen' if info['initialized'] else 'Nem'}")
        print(f"  📚 Dokumentumok: {info['documents_loaded']} db")
        print(
            f"  🔍 Embedder kész: {'Igen' if info['embedder_ready'] else 'Nem'}")
        print(
            f"  💾 Index létezik: {'Igen' if info['index_exists'] else 'Nem'}")
        print(
            f"  📄 Wiki fájl: {'Igen' if info['wiki_file_exists'] else 'Nem'}")

        if info.get('document_titles'):
            titles = info['document_titles'][:5]  # Max 5 cím
            print(f"  📋 Oldalak: {', '.join(titles)}")
            if len(info['document_titles']) > 5:
                print(
                    f"       ... és még {len(info['document_titles']) - 5} oldal")
        print()

    except Exception as error:
        print(f"❌ Státusz lekérdezési hiba: {error}")


def handle_refresh(rag_system: RAGSystem) -> bool:
    """Adatok frissítésének kezelése"""
    try:
        print("🔄 Adatok frissítése...")
        if rag_system.refresh_data():
            print("✅ Adatok sikeresen frissítve!")
            return True
        else:
            print("❌ Adatok frissítése sikertelen!")
            return False
    except Exception as error:
        print(f"❌ Frissítési hiba: {error}")
        return False


def interactive_mode(rag_system: RAGSystem):
    """Interaktív mód - fő ciklus"""
    print("🎯 RAG rendszer kész! Tedd fel a kérdéseidet.")
    print("Írd be 'help'-et a parancsok listájáért.")

    question_count = 0

    while True:
        try:
            # Kérdés bekérése
            prompt = f"\n📌 Kérdés #{question_count + 1} (üres = kilépés): "
            user_input = input(prompt).strip()

            # Kilépés kezelése
            if not user_input or user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Kilépés...")
                break

            # Parancsok kezelése
            if user_input.lower() in ['help', '?', 'h']:
                print_help()
                continue
            elif user_input.lower() in ['status', 'stat', 's']:
                print_status(rag_system)
                continue
            elif user_input.lower() in ['refresh', 'reload', 'r']:
                handle_refresh(rag_system)
                continue
            elif user_input.lower() in ['clear', 'cls']:
                os.system('clear' if os.name == 'posix' else 'cls')
                print_banner()
                continue

            # Kérdés feldolgozása
            try:
                print("🔍 Keresés és válasz generálása...")
                answer = rag_system.process_question(user_input)
                print(f"\n💬 Válasz:\n{answer}\n")
                print("-" * 60)
                question_count += 1

            except RAGQueryError as rag_error:
                print(f"❌ RAG hiba: {rag_error}")
            except Exception as query_error:
                print(f"❌ Kérdés feldolgozási hiba: {query_error}")

        except KeyboardInterrupt:
            print("\n\n👋 Kilépés (Ctrl+C)...")
            break
        except EOFError:
            print("\n\n👋 Kilépés (EOF)...")
            break
        except Exception as error:
            print(f"❌ Váratlan hiba: {error}")


def main():
    """Főprogram"""
    try:
        print_banner()

        # RAG rendszer létrehozása és inicializálása
        print("🚀 RAG rendszer inicializálása...")

        with RAGSystem() as rag_system:
            # Státusz ellenőrzése
            if not rag_system.is_initialized:
                print("❌ RAG rendszer inicializálása sikertelen!")
                return 1

            # Kezdeti státusz kiírása
            print_status(rag_system)

            # Interaktív mód indítása
            interactive_mode(rag_system)

        print("✅ Program befejezve.")
        return 0

    except RAGInitializationError as init_error:
        print(f"❌ Inicializálási hiba: {init_error}")
        print("💡 Ellenőrizd a konfigurációt és próbáld újra!")
        return 1

    except KeyboardInterrupt:
        print("\n\n👋 Program megszakítva (Ctrl+C)")
        return 0

    except Exception as error:
        print(f"❌ Kritikus hiba: {error}")
        logger.exception("Részletes hiba információ:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
