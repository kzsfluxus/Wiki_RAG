#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:33:22 2025

@author: zsolt
"""

import subprocess

def run_ollama_model(prompt, model_name="mistral"):
    try:
        result = subprocess.run(
            ['ollama', 'run', model_name],
            input=prompt.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=480  # 8 perc az első betöltéshez
        )
        if result.returncode == 0:
            return result.stdout.decode()
        else:
            print(f"Ollama hiba: {result.stderr.decode()}")
            return "Hiba történt a modell futtatásakor."
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - próbáld újra, a modell most már be van töltve")
        return "A modell túl sokáig nem válaszolt, próbáld újra."
    except Exception as error:
        print(f"Subprocess hiba: {error}")
        return "Hiba történt a modell hívásakor."