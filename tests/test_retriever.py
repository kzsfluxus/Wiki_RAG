#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:55:47 2025

@author: zsolt
"""

import pytest
import json
from unittest import mock
from pathlib import Path

import retriever


def test_save_pages(tmp_path):
    pages = [{'title': 'Test', 'text': 'Some content'}]
    output_file = tmp_path / 'test_pages.json'

    retriever.save_pages(pages, output_file)

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    assert saved_data == pages


def test_load_config(tmp_path):
    config_file = tmp_path / 'wiki_rag.conf'
    config_file.write_text('[wiki]\nurl = example.org\n', encoding='utf-8')

    config = retriever.load_config(config_file)

    assert config.has_section('wiki')
    assert config.get('wiki', 'url') == 'example.org'


@mock.patch('retriever.mwclient.Site')
def test_connect_without_login(mock_site):
    mock_instance = mock_site.return_value
    site = retriever.connect('example.org', '/w/')
    mock_site.assert_called_with('example.org', path='/w/')
    assert site == mock_instance


@mock.patch('retriever.mwclient.Site')
def test_connect_with_login(mock_site):
    mock_instance = mock_site.return_value
    retriever.connect('example.org', '/w/', username='user', password='pass')
    mock_instance.login.assert_called_once_with('user', 'pass')


@mock.patch('retriever.connect')
def test_fetch_wiki_pages(mock_connect, tmp_path):
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
def test_fetch_related_pages_return(mock_site_class):
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


@mock.patch('retriever.os.path.exists')
@mock.patch('retriever.configparser.ConfigParser')
@mock.patch('retriever.fetch_selected_pages_return')
@mock.patch('retriever.fetch_related_pages_return')
def test_auto_fetch_from_config(mock_related, mock_selected, mock_config_parser, mock_exists):
    mock_exists.return_value = True
    mock_config = mock.Mock()
    mock_config.get.side_effect = lambda s, k, fallback=None: {
        ('wiki', 'url'): 'example.org',
        ('wiki', 'path'): '/w/',
        ('wiki', 'username'): '',
        ('wiki', 'password'): '',
        ('selected', 'pages'): 'Page1,Page2',
        ('related', 'root'): 'Python',
        ('related', 'limit'): '5'
    }.get((s, k), fallback)
    mock_config.has_section.side_effect = lambda s: s in ['wiki', 'selected', 'related']
    mock_config_parser.return_value = mock_config

    retriever.auto_fetch_from_config('dummy.conf')

    mock_selected.assert_called_once()
    mock_related.assert_called_once()
