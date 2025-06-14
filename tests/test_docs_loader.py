#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:45:25 2025

@author: zsolt
"""
import os
import json
import shutil
import pytest
import configparser
from pathlib import Path
from unittest import mock

import docs_loader


@pytest.fixture
def setup_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "dummy.txt").write_text("content")
    return data_dir


def test_clear_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(docs_loader, 'Path', lambda *_: tmp_path / "data")
    os.makedirs(tmp_path / "data", exist_ok=True)
    (tmp_path / "data" / "test.txt").write_text("something")

    assert (tmp_path / "data").exists()
    result = docs_loader.clear_cache()
    assert result is True
    assert not (tmp_path / "data").exists()


def test_should_refresh_data_no_wiki(monkeypatch):
    monkeypatch.setattr(docs_loader, 'WIKI_FILE', Path('nonexistent_wiki.json'))
    monkeypatch.setattr(docs_loader, 'CONFIG_FILE', Path('nonexistent_config.conf'))

    assert docs_loader.should_refresh_data() is True


def test_should_refresh_data_no_config(tmp_path, monkeypatch):
    wiki_file = tmp_path / "wiki_pages.json"
    wiki_file.write_text("[]")

    monkeypatch.setattr(docs_loader, 'WIKI_FILE', wiki_file)
    monkeypatch.setattr(docs_loader, 'CONFIG_FILE', tmp_path / "missing.conf")

    assert docs_loader.should_refresh_data() is False


def test_should_refresh_data_config_newer(tmp_path, monkeypatch):
    wiki_file = tmp_path / "wiki_pages.json"
    wiki_file.write_text("[]")
    config_file = tmp_path / "wiki_rag.ini"
    config_file.write_text("[selected]\npages =")

    # Config később lett módosítva
    os.utime(wiki_file, (1, 1))
    os.utime(config_file, (2, 2))

    monkeypatch.setattr(docs_loader, 'WIKI_FILE', wiki_file)
    monkeypatch.setattr(docs_loader, 'CONFIG_FILE', config_file)

    assert docs_loader.should_refresh_data() is True


def test_should_refresh_data_missing_expected_page(tmp_path, monkeypatch):
    wiki_file = tmp_path / "wiki_pages.json"
    config_file = tmp_path / "wiki_rag.ini"

    # A wiki fájl nem tartalmazza az elvárt oldalt
    wiki_file.write_text(json.dumps([{"title": "Existing Page"}], ensure_ascii=False))
    config_file.write_text("[selected]\npages = Missing Page")

    monkeypatch.setattr(docs_loader, 'WIKI_FILE', wiki_file)
    monkeypatch.setattr(docs_loader, 'CONFIG_FILE', config_file)

    assert docs_loader.should_refresh_data() is True


def test_should_refresh_data_all_good(tmp_path, monkeypatch):
    wiki_file = tmp_path / "wiki_pages.json"
    config_file = tmp_path / "wiki_rag.ini"

    # A wiki fájl tartalmazza a configban elvárt oldalt
    wiki_file.write_text(json.dumps([{"title": "Expected Page"}], ensure_ascii=False))
    config_file.write_text("[selected]\npages = expected page")

    monkeypatch.setattr(docs_loader, 'WIKI_FILE', wiki_file)
    monkeypatch.setattr(docs_loader, 'CONFIG_FILE', config_file)

    assert docs_loader.should_refresh_data() is False


def test_load_docs_success(tmp_path, monkeypatch):
    wiki_file = tmp_path / "wiki_pages.json"
    sample_data = [{"title": "Page 1"}, {"title": "Page 2"}]
    wiki_file.write_text(json.dumps(sample_data, ensure_ascii=False))

    monkeypatch.setattr(docs_loader, 'WIKI_FILE', wiki_file)
    data = docs_loader.load_docs()
    assert isinstance(data, list)
    assert data == sample_data


def test_load_docs_failure(monkeypatch):
    monkeypatch.setattr(docs_loader, 'WIKI_FILE', Path('nonexistent.json'))
    with pytest.raises(Exception):
        docs_loader.load_docs()


# Új tesztek a _parse_selected_pages függvényhez
def test_parse_selected_pages_no_section():
    """Teszt: nincs selected szekció"""
    config = configparser.ConfigParser()
    result = docs_loader._parse_selected_pages(config)
    assert result == []


def test_parse_selected_pages_empty_section():
    """Teszt: üres selected szekció"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    result = docs_loader._parse_selected_pages(config)
    assert result == []


def test_parse_selected_pages_simple_format():
    """Teszt: egyszerű pages formátum"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages', 'Page1, Page2, Page3')
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1', 'Page2', 'Page3']


def test_parse_selected_pages_simple_format_with_spaces():
    """Teszt: egyszerű pages formátum szóközökkel"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages', '  Page1  ,  Page2  ,  Page3  ')
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1', 'Page2', 'Page3']


def test_parse_selected_pages_numbered_format():
    """Teszt: számozott pages.N formátum"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages.1', 'Page1, Page2')
    config.set('selected', 'pages.2', 'Page3, Page4')
    config.set('selected', 'pages.3', 'Page5')
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1', 'Page2', 'Page3', 'Page4', 'Page5']


def test_parse_selected_pages_numbered_format_with_spaces():
    """Teszt: számozott pages.N formátum szóközökkel"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages.1', '  Page1  ,  Page2  ')
    config.set('selected', 'pages.2', '  Page3  ')
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1', 'Page2', 'Page3']


def test_parse_selected_pages_mixed_format_error():
    """Teszt: keveredő formátumok hibája"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages', 'Page1, Page2')
    config.set('selected', 'pages.1', 'Page3, Page4')
    
    with pytest.raises(ValueError, match="Hiba: A 'pages' és 'pages.N' formátumok nem keveredhetnek"):
        docs_loader._parse_selected_pages(config)


def test_parse_selected_pages_empty_values():
    """Teszt: üres értékek kiszűrése"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages', 'Page1, , Page2, ,')
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1', 'Page2']


def test_parse_selected_pages_numbered_empty_values():
    """Teszt: üres értékek kiszűrése számozott formátumban"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages.1', 'Page1, , Page2')
    config.set('selected', 'pages.2', ' , ')
    config.set('selected', 'pages.3', 'Page3')
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1', 'Page2', 'Page3']


def test_parse_selected_pages_numbered_non_numeric():
    """Teszt: nem numerikus végződésű kulcsok figyelmen kívül hagyása"""
    config = configparser.ConfigParser()
    config.add_section('selected')
    config.set('selected', 'pages.1', 'Page1')
    config.set('selected', 'pages.abc', 'PageABC')  # Ez nem számjegy
    config.set('selected', 'pages.comment', 'PageComment')  # Ez sem
    
    result = docs_loader._parse_selected_pages(config)
    assert result == ['Page1']


def test_should_refresh_data_parse_error(tmp_path, monkeypatch):
    """Teszt: parse error esetén refresh szükséges"""
    wiki_file = tmp_path / "wiki_pages.json"
    config_file = tmp_path / "wiki_rag.ini"

    wiki_file.write_text(json.dumps([{"title": "Some Page"}], ensure_ascii=False))
    # Keveredő formátum a config fájlban
    config_file.write_text("[selected]\npages = Page1\npages.1 = Page2")

    monkeypatch.setattr(docs_loader, 'WIKI_FILE', wiki_file)
    monkeypatch.setattr(docs_loader, 'CONFIG_FILE', config_file)

    assert docs_loader.should_refresh_data() is True