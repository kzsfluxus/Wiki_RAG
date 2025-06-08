#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:33:22 2025
@author: zsolt
"""
import subprocess
import logging

logger = logging.getLogger(__name__)


def stop_ollama_model(model_name="mistral"):
    """
    Ollama model leállítása
    """
    try:
        result = subprocess.run(
            ['ollama', 'stop', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            logger.info(
                "A %s modell futtatása sikeresen leállítva",
                model_name)
            return result.stdout.decode()
        else:
            logger.error("Ollama hiba: %s", result.stderr.decode())
            return "Hiba történt a modell leállításakor."
    except Exception as error:
        logger.error("Subprocess hiba: %s", error)
        return "Hiba történt a modell leállításakor."


def run_ollama_model(prompt, model_name="mistral"):
    """
    Ollama model indítása
    """
    try:
        logger.debug("Ollama modell indítása: %s", model_name)
        result = subprocess.run(
            ['ollama', 'run', model_name],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600  # 10 perc az első betöltéshez
        )
        if result.returncode == 0:
            logger.info("Ollama modell sikeresen lefutott: %s", model_name)
            return result.stdout.decode()
        else:
            logger.error("Ollama hiba: %s", result.stderr.decode())
            return "Hiba történt a modell futtatásakor."
    except subprocess.TimeoutExpired:
        logger.warning(
            "Timeout - a modell túl sokáig nem válaszolt (%s)",
            model_name)
        return "A modell túl sokáig nem válaszolt, próbáld újra."
    except Exception as error:
        logger.error("Subprocess hiba: %s", error)
        return "Hiba történt a modell hívásakor."
