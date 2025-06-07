#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web Interface for Wiki RAG System
Created on Thu Jun  5 15:31:49 2025
@author: zsolt
"""
import warnings
import os
from pathlib import Path
import logging

warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

from rag_system import RAGSystem, RAGInitializationError, RAGQueryError
from flask import Flask, request, render_template, jsonify


# Logging beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Globális RAG rendszer instance
rag_system = RAGSystem()


def initialize_app():
    """Alkalmazás inicializálása"""
    try:
        logger.info("🌐 Flask alkalmazás inicializálása...")
        if not rag_system.initialize():
            logger.error("❌ RAG rendszer inicializálása sikertelen!")
            raise RAGInitializationError("System initialization failed")
    except Exception as error:
        logger.error(f"❌ Alkalmazás inicializálási hiba: {error}")
        raise


@app.route('/', methods=['GET', 'POST'])
def index():
    """Főoldal - kérdés-válasz felület"""
    try:
        # Lazy initialization - első használatkor inicializálás
        if not rag_system.is_initialized:
            logger.info("🔄 RAG rendszer inicializálása...")
            initialize_app()

        # Változók inicializálása
        question = ""
        clean_answer = ""
        error = False

        if request.method == 'POST':
            question = request.form.get('question', '').strip()

            if question:
                try:
                    clean_answer = rag_system.process_question(question)
                except RAGQueryError as rag_error:
                    logger.error(f"❌ RAG hiba: {rag_error}")
                    clean_answer = f"❌ Hiba történt: {str(rag_error)}"
                    error = True
                except Exception as general_error:
                    logger.error(f"❌ Általános hiba: {general_error}")
                    clean_answer = f"❌ Váratlan hiba: {str(general_error)}"
                    error = True
            else:
                clean_answer = "Kérlek, adj meg egy kérdést!"

        return render_template('index.html',
                               question=question,
                               clean_answer=clean_answer,
                               error=error)

    except Exception as error:
        logger.error(f"❌ Route hiba: {error}")
        return render_template('index.html',
                               question="",
                               clean_answer=f"❌ Rendszerhiba: {str(error)}",
                               error=True)


@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Manuális adatfrissítés végpont"""
    try:
        logger.info("🔄 Manuális adatfrissítés kezdeményezve...")

        if rag_system.refresh_data():
            logger.info("✅ Adatfrissítés sikeres")
            return jsonify({
                "status": "success",
                "message": "Adatok sikeresen frissítve!"
            })
        else:
            logger.error("❌ Adatfrissítés sikertelen")
            return jsonify({
                "status": "error",
                "message": "Adatok frissítése sikertelen!"
            }), 500

    except Exception as error:
        logger.error(f"❌ Refresh hiba: {error}")
        return jsonify({
            "status": "error",
            "message": f"Hiba történt: {str(error)}"
        }), 500


@app.route('/api/ask', methods=['POST'])
def api_ask():
    """REST API végpont kérdések feldolgozásához"""
    try:
        # Lazy initialization
        if not rag_system.is_initialized:
            initialize_app()

        # JSON kérés ellenőrzése
        if not request.is_json:
            return jsonify(
                {"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "Nincs kérdés megadva"}), 400

        # Kérdés feldolgozása
        answer = rag_system.process_question(question)

        return jsonify({
            "question": question,
            "answer": answer,
            "status": "success"
        })

    except RAGQueryError as rag_error:
        logger.error(f"❌ API RAG hiba: {rag_error}")
        return jsonify({
            "error": str(rag_error),
            "status": "rag_error"
        }), 500

    except Exception as error:
        logger.error(f"❌ API általános hiba: {error}")
        return jsonify({
            "error": f"Váratlan hiba: {str(error)}",
            "status": "error"
        }), 500


@app.route('/api/health')
def health_check():
    """Egészségügyi ellenőrzés végpont"""
    try:
        # Lazy initialization
        if not rag_system.is_initialized:
            initialize_app()

        system_info = rag_system.get_system_info()

        return jsonify({
            "status": "healthy" if system_info["initialized"] else "initializing",
            "system_info": system_info,
            "timestamp": Path(__file__).stat().st_mtime
        })

    except Exception as error:
        logger.error(f"❌ Health check hiba: {error}")
        return jsonify({
            "status": "unhealthy",
            "error": str(error)
        }), 500


@app.route('/api/status')
def system_status():
    """Részletes rendszer státusz"""
    try:
        # Lazy initialization
        if not rag_system.is_initialized:
            initialize_app()

        info = rag_system.get_system_info()

        return jsonify({
            "initialized": info["initialized"],
            "documents_count": info["documents_loaded"],
            "embedder_ready": info["embedder_ready"],
            "index_exists": info["index_exists"],
            "wiki_file_exists": info["wiki_file_exists"],
            # Max 10 cím
            "document_titles": info.get("document_titles", [])[:10]
        })

    except Exception as error:
        logger.error(f"❌ Status check hiba: {error}")
        return jsonify({"error": str(error)}), 500


@app.errorhandler(404)
def not_found(error):
    """404 hiba kezelés"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 hiba kezelés"""
    logger.error(f"❌ 500 hiba: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Környezeti változók beolvasása
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    logger.info(f"🌐 Flask szerver indítása: {host}:{port} (debug={debug})")

    app.run(debug=debug, host=host, port=port)
