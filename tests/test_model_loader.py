#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 14 09:37:22 2025

@author: zsolt
"""

import pytest
import configparser
from unittest.mock import patch, mock_open
from model_loader import get_model

def test_get_model_valid_config():
    content = "[models]\nlanguage_model = mistral\n"
    with patch("builtins.open", mock_open(read_data=content)):
        model = get_model(path="dummy.ini")
        assert model == "mistral"

def test_get_model_empty_model_name():
    content = "[models]\nlanguage_model =   \n"
    with patch("builtins.open", mock_open(read_data=content)):
        model = get_model(path="dummy.ini", default_model="defaultmodel")
        assert model == "defaultmodel"

def test_get_model_long_model_name():
    long_name = "a" * 101
    content = f"[models]\nlanguage_model = {long_name}\n"
    with patch("builtins.open", mock_open(read_data=content)):
        model = get_model(path="dummy.ini", default_model="defaultmodel")
        assert model == "defaultmodel"

def test_get_model_file_not_exist():
    # Olyan fájlt adunk meg, ami nem létezik => fallback default
    model = get_model(path="nonexistent.ini", default_model="defaultmodel")
    assert model == "defaultmodel"

def test_get_model_configparser_error():
    # Szimuláljuk configparser.Error dobását a read() metódusnál
    with patch("configparser.ConfigParser.read", side_effect=configparser.Error("fail")):
        model = get_model(path="dummy.ini", default_model="defaultmodel")
        assert model == "defaultmodel"
