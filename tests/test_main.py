#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 12:05:42 2025

@author: zsolt
"""

import pytest
from unittest.mock import patch, MagicMock
import builtins
import main


@pytest.fixture
def mock_rag_system():
    mock = MagicMock()
    mock.is_initialized = True
    mock.get_system_info.return_value = {
        'initialized': True,
        'documents_loaded': 10,
        'embedder_ready': True,
        'index_exists': True,
        'wiki_file_exists': True,
        'document_titles': ['Page1', 'Page2', 'Page3']
    }
    mock.process_question.return_value = "Ez egy teszt válasz."
    mock.refresh_data.return_value = True
    return mock


def test_print_status(capsys, mock_rag_system):
    main.print_status(mock_rag_system)
    output = capsys.readouterr().out
    assert "Inicializálva" in output
    assert "Dokumentumok" in output
    assert "Embedder kész" in output


def test_handle_refresh_success(capsys, mock_rag_system):
    success = main.handle_refresh(mock_rag_system)
    output = capsys.readouterr().out
    assert success is True
    assert "sikeresen frissítve" in output


def test_interactive_mode_help_command(mock_rag_system):
    with patch.object(builtins, 'input', side_effect=["help", "exit"]), \
         patch.object(main, 'print_help') as mock_help:
        main.interactive_mode(mock_rag_system)
        mock_help.assert_called_once()


def test_interactive_mode_status_command(mock_rag_system):
    with patch.object(builtins, 'input', side_effect=["status", "exit"]), \
         patch.object(main, 'print_status') as mock_status:
        main.interactive_mode(mock_rag_system)
        mock_status.assert_called_once_with(mock_rag_system)


def test_interactive_mode_question_response(capsys, mock_rag_system):
    with patch.object(builtins, 'input', side_effect=["Mi a teszt?", "exit"]):
        main.interactive_mode(mock_rag_system)
        output = capsys.readouterr().out
        assert "válasz" in output.lower()


def test_main_success(monkeypatch, mock_rag_system):
    monkeypatch.setattr(main, 'RAGSystem', lambda: mock_rag_system)
    monkeypatch.setattr(main, 'interactive_mode', lambda rs: None)
    monkeypatch.setattr(main, 'print_status', lambda rs: None)

    result = main.main()
    assert result == 0


def test_main_initialization_fail(monkeypatch):
    mock = MagicMock()
    mock.__enter__.return_value.is_initialized = False
    monkeypatch.setattr(main, 'RAGSystem', lambda: mock)

    result = main.main()
    assert result == 1


def test_main_rag_initialization_error(monkeypatch):
    def raise_error():
        raise
