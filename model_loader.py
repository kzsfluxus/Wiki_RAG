#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 03:21:15 2025

@author: zsolt
"""
import configparser
from pathlib import Path
import logging

MODEL_PATH=Path('models/models.ini')

def get_model(path=MODEL_PATH):
    """
    Betölti a nyelvi modell nevét a konfigurációs fájlból.
   
    A függvény egy konfigurációs fájlból olvassa ki a használandó nyelvi modell 
    nevét. Ha a fájl nem létezik, nem olvasható, vagy nem tartalmazza a szükséges 
    beállításokat, akkor egy alapértelmezett modellt ad vissza.
   
    Args:
        path (str, optional): A konfigurációs fájl elérési útja. 
            Alapértelmezett: MODEL_PATH globális változó értéke.
   
    Returns:
        str: A nyelvi modell neve. Ha nem sikerül betölteni a konfigurációból,
            akkor 'mistral' alapértelmezett értéket ad vissza.
    """
    DEFAULT_MODEL = 'mistral'
    config = configparser.ConfigParser()
    try:
        config.read(path, encoding='utf-8')
        if 'models' in config and 'language_model' in config['models']:
            model_name = config['models']['language_model'].strip()
                        
            if model_name and len(model_name) <= 100:
                return model_name
                logging.info("%s modell sikeresen betöltve", model_name)
        return DEFAULT_MODEL
        logging.info("%s modell sikeresen betöltve", DEFAULT_MODEL)
    except (configparser.Error) as error:
        logging.warning
        ("Hiba a model.ini fájlban: %s, a RAG Rendszer az alapértelmezett modellt használja: %s", error ,DEFAULT_MODEL)
        return DEFAULT_MODEL