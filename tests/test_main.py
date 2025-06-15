#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for main.py CLI Interface
Created on Sun Jun  8 12:05:42 2025
@author: zsolt

Teljes körű tesztek a main.py CLI interfészhez, amely lefedi:
- Alapfunkciókat (banner, help, status)
- Interaktív módot és parancsok kezelését
- Hibakezelést és kivételeket
- Edge case-eket és különleges helyzeteket
- Context manager működést
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock, call
from io import StringIO
import builtins

# Import the module under test
import main
from rag_system import RAGInitializationError, RAGQueryError


@pytest.fixture
def mock_rag_system():
    """Mock RAGSystem instance standard működéssel"""
    mock = MagicMock()
    mock.is_initialized = True
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    mock.get_system_info.return_value = {
        'initialized': True,
        'documents_loaded': 10,
        'embedder_ready': True,
        'index_exists': True,
        'wiki_file_exists': True,
        'document_titles': ['Page1', 'Page2', 'Page3', 'Page4', 'Page5', 'Page6']
    }
    mock.process_question.return_value = "Ez egy teszt válasz."
    mock.refresh_data.return_value = True
    return mock


@pytest.fixture
def mock_rag_system_uninitialized():
    """Mock RAGSystem instance inicializálatlan állapotban"""
    mock = MagicMock()
    mock.is_initialized = False
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock


@pytest.fixture
def mock_rag_system_minimal():
    """Mock RAGSystem instance minimális adatokkal"""
    mock = MagicMock()
    mock.is_initialized = True
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    mock.get_system_info.return_value = {
        'initialized': True,
        'documents_loaded': 2,
        'embedder_ready': True,
        'index_exists': True,
        'wiki_file_exists': True,
        'document_titles': ['Page1', 'Page2']
    }
    mock.process_question.return_value = "Minimális válasz."
    mock.refresh_data.return_value = True
    return mock


class TestBannerAndHelp:
    """Banner és help funkciók tesztje"""
    
    def test_print_banner(self, capsys):
        """Banner kiírás tesztje"""
        main.print_banner()
        captured = capsys.readouterr()
        
        assert "Wiki RAG CLI" in captured.out
        assert "🚀" in captured.out
        assert "=" * 60 in captured.out
    
    def test_print_help(self, capsys):
        """Help kiírás tesztje"""
        main.print_help()
        captured = capsys.readouterr()
        
        assert "Elérhető parancsok" in captured.out
        assert "help" in captured.out
        assert "status" in captured.out
        assert "refresh" in captured.out
        assert "quit" in captured.out


class TestStatusFunctionality:
    """Status funkciók tesztje"""
    
    def test_print_status_full_info(self, capsys, mock_rag_system):
        """Teljes status információ megjelenítése"""
        main.print_status(mock_rag_system)
        captured = capsys.readouterr()
        
        assert "Rendszer státusz" in captured.out
        assert "Inicializálva: Igen" in captured.out
        assert "Dokumentumok: 10 db" in captured.out
        assert "Embedder kész: Igen" in captured.out
        assert "Index létezik: Igen" in captured.out
        assert "Wiki fájl: Igen" in captured.out
        assert "Page1" in captured.out
        assert "még 1 oldal" in captured.out  # 6 title esetén 5-öt mutat + 1 többit
    
    def test_print_status_minimal_info(self, capsys, mock_rag_system_minimal):
        """Minimális status információ megjelenítése"""
        main.print_status(mock_rag_system_minimal)
        captured = capsys.readouterr()
        
        assert "Dokumentumok: 2 db" in captured.out
        assert "Page1" in captured.out
        assert "Page2" in captured.out
        assert "még" not in captured.out  # Kevés oldal esetén nincs "még X oldal"
    
    def test_print_status_error_handling(self, capsys):
        """Status lekérdezési hiba kezelése"""
        mock_rag = MagicMock()
        mock_rag.get_system_info.side_effect = Exception("Test error")
        
        main.print_status(mock_rag)
        captured = capsys.readouterr()
        
        assert "Státusz lekérdezési hiba" in captured.out
        assert "Test error" in captured.out
    
    def test_print_status_no_document_titles(self, capsys, mock_rag_system):
        """Document titles nélküli status"""
        mock_rag_system.get_system_info.return_value = {
            'initialized': True,
            'documents_loaded': 0,
            'embedder_ready': False,
            'index_exists': False,
            'wiki_file_exists': False
        }
        
        main.print_status(mock_rag_system)
        captured = capsys.readouterr()
        
        assert "Inicializálva: Igen" in captured.out
        assert "Dokumentumok: 0 db" in captured.out
        assert "Embedder kész: Nem" in captured.out


class TestRefreshFunctionality:
    """Refresh funkciók tesztje"""
    
    def test_handle_refresh_success(self, capsys, mock_rag_system):
        """Sikeres adatok frissítése"""
        result = main.handle_refresh(mock_rag_system)
        captured = capsys.readouterr()
        
        assert result is True
        assert "Adatok frissítése" in captured.out
        assert "sikeresen frissítve" in captured.out
        mock_rag_system.refresh_data.assert_called_once()
    
    def test_handle_refresh_failure(self, capsys, mock_rag_system):
        """Sikertelen adatok frissítése"""
        mock_rag_system.refresh_data.return_value = False
        
        result = main.handle_refresh(mock_rag_system)
        captured = capsys.readouterr()
        
        assert result is False
        assert "Adatok frissítése sikertelen" in captured.out
    
    def test_handle_refresh_exception(self, capsys, mock_rag_system):
        """Refresh során fellépő kivétel kezelése"""
        mock_rag_system.refresh_data.side_effect = Exception("Refresh error")
        
        result = main.handle_refresh(mock_rag_system)
        captured = capsys.readouterr()
        
        assert result is False
        assert "Frissítési hiba" in captured.out
        assert "Refresh error" in captured.out


class TestInteractiveMode:
    """Interaktív mód tesztje"""
    
    def test_interactive_mode_help_command(self, mock_rag_system):
        """Help parancs kezelése interaktív módban"""
        with patch.object(builtins, 'input', side_effect=["help", "exit"]), \
             patch.object(main, 'print_help') as mock_help:
            main.interactive_mode(mock_rag_system)
            mock_help.assert_called_once()
    
    def test_interactive_mode_status_command(self, mock_rag_system):
        """Status parancs kezelése interaktív módban"""
        with patch.object(builtins, 'input', side_effect=["status", "exit"]), \
             patch.object(main, 'print_status') as mock_status:
            main.interactive_mode(mock_rag_system)
            mock_status.assert_called_once_with(mock_rag_system)
    
    def test_interactive_mode_refresh_command(self, mock_rag_system):
        """Refresh parancs kezelése interaktív módban"""
        with patch.object(builtins, 'input', side_effect=["refresh", "exit"]), \
             patch.object(main, 'handle_refresh') as mock_refresh:
            main.interactive_mode(mock_rag_system)
            mock_refresh.assert_called_once_with(mock_rag_system)
    
    def test_interactive_mode_clear_command(self, mock_rag_system):
        """Clear parancs kezelése"""
        with patch.object(builtins, 'input', side_effect=["clear", "exit"]), \
             patch.object(os, 'system') as mock_system, \
             patch.object(main, 'print_banner') as mock_banner, \
             patch('os.name', 'posix'):
            main.interactive_mode(mock_rag_system)
            mock_system.assert_called_once_with('clear')
            mock_banner.assert_called_once()
    
    def test_interactive_mode_question_processing(self, capsys, mock_rag_system):
        """Kérdés feldolgozása"""
        with patch.object(builtins, 'input', side_effect=["Mi a teszt?", "exit"]):
            main.interactive_mode(mock_rag_system)
            
        captured = capsys.readouterr()
        assert "Keresés és válasz generálása" in captured.out
        assert "Ez egy teszt válasz" in captured.out
        mock_rag_system.process_question.assert_called_once_with("Mi a teszt?")
    
    def test_interactive_mode_multiple_questions(self, capsys, mock_rag_system):
        """Több kérdés feldolgozása"""
        with patch.object(builtins, 'input', side_effect=["Kérdés 1", "Kérdés 2", "exit"]):
            main.interactive_mode(mock_rag_system)
        
        assert mock_rag_system.process_question.call_count == 2
        mock_rag_system.process_question.assert_has_calls([
            call("Kérdés 1"),
            call("Kérdés 2")
        ])
    
    def test_interactive_mode_rag_query_error(self, capsys, mock_rag_system):
        """RAGQueryError kezelése"""
        mock_rag_system.process_question.side_effect = RAGQueryError("Query error")
        
        with patch.object(builtins, 'input', side_effect=["test kérdés", "exit"]):
            main.interactive_mode(mock_rag_system)
        
        captured = capsys.readouterr()
        assert "RAG hiba" in captured.out
        assert "Query error" in captured.out
    
    def test_interactive_mode_general_exception(self, capsys, mock_rag_system):
        """Általános kivétel kezelése kérdés feldolgozáskor"""
        mock_rag_system.process_question.side_effect = Exception("General error")
        
        with patch.object(builtins, 'input', side_effect=["test kérdés", "exit"]):
            main.interactive_mode(mock_rag_system)
        
        captured = capsys.readouterr()
        assert "Kérdés feldolgozási hiba" in captured.out
        assert "General error" in captured.out
    
    def test_interactive_mode_keyboard_interrupt(self, capsys, mock_rag_system):
        """Keyboard interrupt (Ctrl+C) kezelése"""
        with patch.object(builtins, 'input', side_effect=[KeyboardInterrupt]):
            main.interactive_mode(mock_rag_system)
        
        captured = capsys.readouterr()
        assert "Kilépés (Ctrl+C)" in captured.out
    
    def test_interactive_mode_eof_error(self, capsys, mock_rag_system):
        """EOF error kezelése"""
        with patch.object(builtins, 'input', side_effect=[EOFError]):
            main.interactive_mode(mock_rag_system)
        
        captured = capsys.readouterr()
        assert "Kilépés (EOF)" in captured.out
    
    def test_interactive_mode_unexpected_error_in_loop(self, capsys, mock_rag_system):
        """Váratlan hiba kezelése a ciklusban"""
        # Mock input hogy dobjon kivételt, majd egy normális kilépést
        def input_side_effect(prompt=""):
            if input_side_effect.call_count == 0:
                input_side_effect.call_count = 1
                raise Exception("Unexpected error")
            else:
                return "exit"
        input_side_effect.call_count = 0
        
        with patch.object(builtins, 'input', side_effect=input_side_effect):
            main.interactive_mode(mock_rag_system)
        
        captured = capsys.readouterr()
        assert "Váratlan hiba" in captured.out or "Unexpected error" in captured.out
    
    @pytest.mark.parametrize("exit_command", ["", "quit", "exit", "bye"])
    def test_interactive_mode_exit_commands(self, exit_command, mock_rag_system):
        """Különböző kilépési parancsok tesztje"""
        with patch.object(builtins, 'input', return_value=exit_command):
            main.interactive_mode(mock_rag_system)
        # Ha eljut ide, akkor sikeresen kilépett
        assert True
    
    @pytest.mark.parametrize("help_command", ["help", "?", "h"])
    def test_interactive_mode_help_variants(self, help_command, mock_rag_system):
        """Help parancs változatok tesztje"""
        with patch.object(builtins, 'input', side_effect=[help_command, "exit"]), \
             patch.object(main, 'print_help') as mock_help:
            main.interactive_mode(mock_rag_system)
            mock_help.assert_called_once()
    
    @pytest.mark.parametrize("status_command", ["status", "stat", "s"])
    def test_interactive_mode_status_variants(self, status_command, mock_rag_system):
        """Status parancs változatok tesztje"""
        with patch.object(builtins, 'input', side_effect=[status_command, "exit"]), \
             patch.object(main, 'print_status') as mock_status:
            main.interactive_mode(mock_rag_system)
            mock_status.assert_called_once()
    
    @pytest.mark.parametrize("refresh_command", ["refresh", "reload", "r"])
    def test_interactive_mode_refresh_variants(self, refresh_command, mock_rag_system):
        """Refresh parancs változatok tesztje"""
        with patch.object(builtins, 'input', side_effect=[refresh_command, "exit"]), \
             patch.object(main, 'handle_refresh') as mock_refresh:
            main.interactive_mode(mock_rag_system)
            mock_refresh.assert_called_once()


class TestMainFunction:
    """Main funkció tesztje"""
    
    def test_main_success(self, mock_rag_system):
        """Sikeres main futás"""
        with patch.object(main, 'RAGSystem', return_value=mock_rag_system), \
             patch.object(main, 'interactive_mode') as mock_interactive, \
             patch.object(main, 'print_status') as mock_status, \
             patch.object(main, 'print_banner') as mock_banner:
            
            result = main.main()
            
            assert result == 0
            mock_banner.assert_called_once()
            mock_status.assert_called_once_with(mock_rag_system)
            mock_interactive.assert_called_once_with(mock_rag_system)
    
    def test_main_initialization_failure(self, mock_rag_system_uninitialized, capsys):
        """Inicializálási hiba kezelése"""
        with patch.object(main, 'RAGSystem', return_value=mock_rag_system_uninitialized):
            result = main.main()
            
            assert result == 1
            captured = capsys.readouterr()
            assert "inicializálása sikertelen" in captured.out
    
    def test_main_rag_initialization_error(self, capsys):
        """RAGInitializationError kezelése"""
        with patch.object(main, 'RAGSystem', side_effect=RAGInitializationError("Init error")):
            result = main.main()
            
            assert result == 1
            captured = capsys.readouterr()
            assert "Inicializálási hiba" in captured.out
            assert "Init error" in captured.out
            assert "Ellenőrizd a konfigurációt" in captured.out
    
    def test_main_keyboard_interrupt(self, capsys):
        """Keyboard interrupt a main-ben"""
        with patch.object(main, 'RAGSystem', side_effect=KeyboardInterrupt):
            result = main.main()
            
            assert result == 0
            captured = capsys.readouterr()
            assert "megszakítva (Ctrl+C)" in captured.out
    
    def test_main_general_exception(self, capsys):
        """Általános kivétel a main-ben"""
        with patch.object(main, 'RAGSystem', side_effect=Exception("Critical error")), \
             patch.object(main.logger, 'exception') as mock_log:
            
            result = main.main()
            
            assert result == 1
            captured = capsys.readouterr()
            assert "Kritikus hiba" in captured.out
            assert "Critical error" in captured.out
            mock_log.assert_called_once()
    
    def test_main_context_manager_usage(self, mock_rag_system):
        """Context manager helyes használata"""
        with patch.object(main, 'RAGSystem', return_value=mock_rag_system), \
             patch.object(main, 'interactive_mode'), \
             patch.object(main, 'print_status'), \
             patch.object(main, 'print_banner'):
            
            main.main()
            
            # Ellenőrizzük, hogy a context manager metódusai meghívásra kerültek
            mock_rag_system.__enter__.assert_called_once()
            mock_rag_system.__exit__.assert_called_once()


class TestEdgeCases:
    """Edge case-ek és speciális helyzetek tesztje"""
    
    def test_empty_input_handling(self, mock_rag_system):
        """Üres input kezelése"""
        with patch.object(builtins, 'input', side_effect=["", "exit"]):
            main.interactive_mode(mock_rag_system)
        assert True
    
    def test_whitespace_only_input(self, mock_rag_system):
        """Csak whitespace input kezelése"""
        with patch.object(builtins, 'input', side_effect=["   \t\n", "exit"]):
            main.interactive_mode(mock_rag_system)
        assert True
    
    def test_case_insensitive_commands(self, mock_rag_system):
        """Case insensitive parancsok"""
        with patch.object(builtins, 'input', side_effect=["HELP", "exit"]), \
             patch.object(main, 'print_help') as mock_help:
            main.interactive_mode(mock_rag_system)
            mock_help.assert_called_once()
    
    def test_very_long_question(self, mock_rag_system, capsys):
        """Nagyon hosszú kérdés kezelése"""
        long_question = "Ez egy nagyon hosszú kérdés" * 10  # Nincs szóköz a végén
    
        with patch.object(builtins, 'input', side_effect=[long_question, "exit"]):
            main.interactive_mode(mock_rag_system)
    
        mock_rag_system.process_question.assert_called_once_with(long_question)

    
    def test_unicode_characters(self, mock_rag_system):
        """Unicode karakterek kezelése"""
        unicode_question = "Mi ez: 🤔 árvíztűrő tükörfúrógép ÁRVÍZTŰRŐ TÜKÖRFÚRÓGÉP?"
        
        with patch.object(builtins, 'input', side_effect=[unicode_question, "exit"]):
            main.interactive_mode(mock_rag_system)
        
        mock_rag_system.process_question.assert_called_once_with(unicode_question)


class TestSystemIntegration:
    """Rendszer integráció tesztek"""
    
    def test_os_environment_variables(self):
        """OS környezeti változók beállítása"""
        # Ezt már a main.py betöltésekor beállítja
        assert os.environ.get('PYTHONWARNINGS') == 'ignore::DeprecationWarning'
    
    def test_logging_configuration(self):
        """Logging konfiguráció ellenőrzése"""
        import logging
        logger = logging.getLogger('main')
        # Basic check that logger exists and has reasonable level
        assert isinstance(logger.level, int)
    
    def test_imports_work(self):
        """Importok működésének ellenőrzése"""
        # Ha eljutunk ide, akkor az importok működnek
        assert hasattr(main, 'print_banner')
        assert hasattr(main, 'main')
        assert callable(main.print_banner)
        assert callable(main.main)


if __name__ == '__main__':
    # Tesztek futtatása pytest-tel
    pytest.main([__file__, '-v', '--cov=main', '--cov-report=term-missing'])