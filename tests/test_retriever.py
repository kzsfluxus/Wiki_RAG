#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:55:47 2025

@author: zsolt
"""

import pytest
import json
import os
from unittest import mock
from pathlib import Path
import configparser

import retriever


def test_save_pages(tmp_path):
    """Teszteli a save_pages függvényt."""
    pages = [{'title': 'Test', 'text': 'Some content'}]
    output_file = tmp_path / 'test_pages.json'

    retriever.save_pages(pages, output_file)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    assert saved_data == pages


def test_load_config(tmp_path):
    """Teszteli a load_config függvényt."""
    config_file = tmp_path / 'wiki_rag.ini'
    config_file.write_text('[wiki]\nurl = example.org\n', encoding='utf-8')

    config = retriever.load_config(config_file)

    assert config.has_section('wiki')
    assert config.get('wiki', 'url') == 'example.org'


class TestParseSelectedPages:
    """Tesztek a _parse_selected_pages függvényhez."""
    
    def test_empty_config(self):
        """Teszteli üres konfigurációval."""
        config = configparser.ConfigParser()
        result = retriever._parse_selected_pages(config)
        assert result == []

    def test_no_selected_section(self):
        """Teszteli hiányzó selected szekcióval."""
        config = configparser.ConfigParser()
        config.add_section('wiki')
        result = retriever._parse_selected_pages(config)
        assert result == []

    def test_simple_pages_format(self):
        """Teszteli az egyszerű pages formátumot."""
        config = configparser.ConfigParser()
        config.add_section('selected')
        config.set('selected', 'pages', 'Page1, Page2, Page3')
        
        result = retriever._parse_selected_pages(config)
        assert result == ['Page1', 'Page2', 'Page3']

    def test_numbered_pages_format(self):
        """Teszteli a számozott pages formátumot."""
        config = configparser.ConfigParser()
        config.add_section('selected')
        config.set('selected', 'pages.1', 'Page1, Page2')
        config.set('selected', 'pages.2', 'Page3, Page4')
        
        result = retriever._parse_selected_pages(config)
        assert set(result) == {'Page1', 'Page2', 'Page3', 'Page4'}

    def test_mixed_format_raises_error(self):
        """Teszteli, hogy a kevert formátum hibát dob."""
        config = configparser.ConfigParser()
        config.add_section('selected')
        config.set('selected', 'pages', 'Page1')
        config.set('selected', 'pages.1', 'Page2')
        
        with pytest.raises(ValueError, match="A 'pages' és 'pages.N' formátumok nem keveredhetnek"):
            retriever._parse_selected_pages(config)

    def test_empty_pages_values(self):
        """Teszteli üres pages értékekkel."""
        config = configparser.ConfigParser()
        config.add_section('selected')
        config.set('selected', 'pages', '')
        config.set('selected', 'pages.1', '  ')
        
        result = retriever._parse_selected_pages(config)
        assert result == []


@mock.patch('retriever.mwclient.Site')
def test_connect_without_login(mock_site):
    """Teszteli a connect függvényt bejelentkezés nélkül."""
    mock_instance = mock_site.return_value
    site = retriever.connect('example.org', '/w/')
    mock_site.assert_called_with('example.org', path='/w/')
    assert site == mock_instance


@mock.patch('retriever.mwclient.Site')
def test_connect_with_login(mock_site):
    """Teszteli a connect függvényt bejelentkezéssel."""
    mock_instance = mock_site.return_value
    retriever.connect('example.org', '/w/', username='user', password='pass')
    mock_instance.login.assert_called_once_with('user', 'pass')


@mock.patch('retriever.connect')
def test_fetch_wiki_pages(mock_connect, tmp_path):
    """Teszteli a fetch_wiki_pages függvényt."""
    mock_page = mock.Mock()
    mock_page.name = 'Test'
    mock_page.text.return_value = 'Content'
    mock_connect.return_value.allpages.return_value = [mock_page] * 2

    out_file = tmp_path / 'output.json'
    retriever.fetch_wiki_pages('example.org', limit=2, output_path=out_file)

    assert out_file.exists()
    with open(out_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]['title'] == 'Test'
    assert data[0]['text'] == 'Content'


@mock.patch('retriever.mwclient.Site')
def test_fetch_selected_pages_return(mock_site_class):
    """Teszteli a fetch_selected_pages_return függvényt."""
    mock_site = mock_site_class.return_value
    page_mock = mock.Mock()
    page_mock.exists = True
    page_mock.text.return_value = "Sample Text"
    mock_site.pages = {'TestPage': page_mock}

    pages = retriever.fetch_selected_pages_return('example.org', ['TestPage'])
    assert len(pages) == 1
    assert pages[0]['title'] == 'TestPage'
    assert pages[0]['text'] == 'Sample Text'


@mock.patch('retriever.mwclient.Site')
def test_fetch_selected_pages_return_nonexistent_page(mock_site_class):
    """Teszteli nem létező oldallal."""
    mock_site = mock_site_class.return_value
    page_mock = mock.Mock()
    page_mock.exists = False
    mock_site.pages = {'NonExistent': page_mock}

    pages = retriever.fetch_selected_pages_return('example.org', ['NonExistent'])
    assert len(pages) == 0


@mock.patch('retriever.mwclient.Site')
def test_fetch_related_pages_return(mock_site_class):
    """Teszteli a fetch_related_pages_return függvényt."""
    mock_site = mock_site_class.return_value
    mock_site.api.return_value = {
        'query': {
            'prefixsearch': [{'title': 'PrefixTest'}]
        }
    }

    page_mock = mock.Mock()
    page_mock.exists = True
    page_mock.text.return_value = "Prefix Page Text"
    mock_site.pages = {'PrefixTest': page_mock}

    results = retriever.fetch_related_pages_return('example.org', 'Prefix')
    assert len(results) == 1
    assert results[0]['title'] == 'PrefixTest'


@mock.patch('retriever.mwclient.Site')
def test_fetch_related_pages_return_no_results(mock_site_class):
    """Teszteli a fetch_related_pages_return függvényt üres eredménnyel."""
    mock_site = mock_site_class.return_value
    mock_site.api.return_value = {
        'query': {
            'prefixsearch': []
        }
    }

    results = retriever.fetch_related_pages_return('example.org', 'NonExistent')
    assert len(results) == 0


class TestAutoFetchFromConfig:
    """Tesztek az auto_fetch_from_config függvényhez."""

    @mock.patch('retriever.os.path.exists')
    def test_missing_config_file(self, mock_exists):
        """Teszteli hiányzó konfigurációs fájl esetét."""
        mock_exists.return_value = False
        
        # Nem dob hibát, csak log üzenetet ír
        retriever.auto_fetch_from_config('missing.ini')
        
        mock_exists.assert_called_once_with('missing.ini')

    @mock.patch('retriever.os.path.exists')
    @mock.patch('retriever.configparser.ConfigParser')
    def test_missing_wiki_section(self, mock_config_parser, mock_exists):
        """Teszteli hiányzó wiki szekció esetét."""
        mock_exists.return_value = True
        mock_config = mock.Mock()
        mock_config.has_section.return_value = False
        mock_config.get.return_value = ''
        mock_config_parser.return_value = mock_config

        retriever.auto_fetch_from_config('test.ini')

    @mock.patch('retriever.os.path.exists')
    @mock.patch('retriever.configparser.ConfigParser')
    @mock.patch('retriever.fetch_wiki_pages')
    def test_empty_selected_and_related(self, mock_fetch_wiki, mock_config_parser, mock_exists):
        """Teszteli üres selected és related szekciók esetét."""
        mock_exists.return_value = True
        mock_config = mock.Mock()
        
        # Wiki szekció beállítása
        mock_config.has_section.side_effect = lambda s: s == 'wiki'
        mock_config.get.side_effect = lambda s, k, fallback=None: {
            ('wiki', 'url'): 'example.org',
            ('wiki', 'path'): '/w/',
            ('wiki', 'username'): None,
            ('wiki', 'password'): None,
            ('wiki', 'limit'): '50',
            ('selected', 'pages'): '',
            ('related', 'root'): ''
        }.get((s, k), fallback)
        
        mock_config_parser.return_value = mock_config

        with mock.patch('retriever._parse_selected_pages', return_value=[]):
            retriever.auto_fetch_from_config('test.ini')

        mock_fetch_wiki.assert_called_once()

    @mock.patch('retriever.os.path.exists')
    @mock.patch('retriever.configparser.ConfigParser')
    @mock.patch('retriever.fetch_selected_pages_return')
    @mock.patch('retriever.os.makedirs')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.dump')
    def test_selected_pages_only(self, mock_json_dump, mock_open, mock_makedirs, 
                                mock_selected, mock_config_parser, mock_exists):
        """Teszteli csak selected pages esetét."""
        mock_exists.return_value = True
        mock_config = mock.Mock()
        
        mock_config.has_section.side_effect = lambda s: s in ['wiki', 'selected']
        mock_config.get.side_effect = lambda s, k, fallback=None: {
            ('wiki', 'url'): 'example.org',
            ('wiki', 'path'): '/w/',
            ('wiki', 'username'): None,
            ('wiki', 'password'): None,
            ('wiki', 'limit'): '100',
            ('related', 'root'): ''
        }.get((s, k), fallback)
        
        mock_config_parser.return_value = mock_config
        mock_selected.return_value = [{'title': 'Test', 'text': 'Content'}]

        with mock.patch('retriever._parse_selected_pages', return_value=['TestPage']):
            retriever.auto_fetch_from_config('test.ini')

        mock_selected.assert_called_once()
        mock_json_dump.assert_called_once()

    @mock.patch('retriever.os.path.exists')
    @mock.patch('retriever.configparser.ConfigParser')
    @mock.patch('retriever._parse_selected_pages')
    def test_parse_selected_pages_error(self, mock_parse, mock_config_parser, mock_exists):
        """Teszteli a _parse_selected_pages hiba esetét."""
        mock_exists.return_value = True
        mock_config = mock.Mock()
        mock_config.has_section.return_value = True
        mock_config.get.return_value = 'example.org'
        mock_config_parser.return_value = mock_config
        
        mock_parse.side_effect = ValueError("Test error")

        retriever.auto_fetch_from_config('test.ini')
        
        mock_parse.assert_called_once()

    @mock.patch('retriever.os.path.exists')
    @mock.patch('retriever.configparser.ConfigParser')
    @mock.patch('retriever.fetch_selected_pages_return')
    @mock.patch('retriever.fetch_related_pages_return')
    @mock.patch('retriever.os.makedirs')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.dump')
    def test_selected_and_related_pages(self, mock_json_dump, mock_open, mock_makedirs,
                                      mock_related, mock_selected, mock_config_parser, mock_exists):
        """Teszteli selected és related pages kombinációját."""
        mock_exists.return_value = True
        mock_config = mock.Mock()
        
        mock_config.has_section.side_effect = lambda s: s in ['wiki', 'selected', 'related']
        mock_config.get.side_effect = lambda s, k, fallback=None: {
            ('wiki', 'url'): 'example.org',
            ('wiki', 'path'): '/w/',
            ('wiki', 'username'): None,
            ('wiki', 'password'): None,
            ('wiki', 'limit'): '100',
            ('related', 'root'): 'Python',
            ('related', 'limit'): '50'
        }.get((s, k), fallback)
        
        mock_config_parser.return_value = mock_config
        mock_selected.return_value = [{'title': 'Selected', 'text': 'Content'}]
        mock_related.return_value = [{'title': 'Related', 'text': 'Content'}]

        with mock.patch('retriever._parse_selected_pages', return_value=['SelectedPage']):
            retriever.auto_fetch_from_config('test.ini')

        mock_selected.assert_called_once()
        mock_related.assert_called_once()
        mock_json_dump.assert_called_once()

    @mock.patch('retriever.os.path.exists')
    @mock.patch('retriever.configparser.ConfigParser')
    @mock.patch('retriever.fetch_selected_pages_return')
    @mock.patch('retriever.os.makedirs')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    @mock.patch('json.dump')
    def test_limit_exceeded_selected_pages(self, mock_json_dump, mock_open, mock_makedirs,
                                         mock_selected, mock_config_parser, mock_exists):
        """Teszteli a limit túllépését selected pages esetén."""
        mock_exists.return_value = True
        mock_config = mock.Mock()
        
        mock_config.has_section.side_effect = lambda s: s in ['wiki', 'selected']
        mock_config.get.side_effect = lambda s, k, fallback=None: {
            ('wiki', 'url'): 'example.org',
            ('wiki', 'path'): '/w/',
            ('wiki', 'username'): None,
            ('wiki', 'password'): None,
            ('wiki', 'limit'): '2',  # Alacsony limit
            ('related', 'root'): ''
        }.get((s, k), fallback)
        
        mock_config_parser.return_value = mock_config
        mock_selected.return_value = [
            {'title': 'Page1', 'text': 'Content1'},
            {'title': 'Page2', 'text': 'Content2'}
        ]

        # 5 oldal van kiválasztva, de limit csak 2
        with mock.patch('retriever._parse_selected_pages', return_value=['P1', 'P2', 'P3', 'P4', 'P5']):
            retriever.auto_fetch_from_config('test.ini')

        # A mock_selected csak 2 oldallal lett meghívva (limit miatt)
        call_args = mock_selected.call_args[0]
        assert len(call_args[1]) == 2  # titles lista csak 2 elemet tartalmaz


if __name__ == "__main__":
    pytest.main([__file__])