#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 11:48:35 2025

@author: zsolt
"""

import subprocess
from unittest import mock
import pytest
import ollama_runner


@mock.patch('subprocess.run')
def test_run_ollama_model_success(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=['ollama', 'run', 'mistral'],
        returncode=0,
        stdout=b'Model response here.',
        stderr=b''
    )

    result = ollama_runner.run_ollama_model("Hello", model_name="mistral")
    assert result == 'Model response here.'


@mock.patch('subprocess.run')
def test_run_ollama_model_failure(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=['ollama', 'run', 'mistral'],
        returncode=1,
        stdout=b'',
        stderr=b'Error: something went wrong'
    )

    result = ollama_runner.run_ollama_model("Hello", model_name="mistral")
    assert "Hiba történt" in result


@mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='ollama', timeout=600))
def test_run_ollama_model_timeout(mock_run):
    result = ollama_runner.run_ollama_model("Hello", model_name="mistral")
    assert "túl sokáig" in result


@mock.patch('subprocess.run', side_effect=Exception("unexpected error"))
def test_run_ollama_model_exception(mock_run):
    result = ollama_runner.run_ollama_model("Hello", model_name="mistral")
    assert "Hiba történt" in result


@mock.patch('subprocess.run')
def test_stop_ollama_model_success(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=['ollama', 'stop', 'mistral'],
        returncode=0,
        stdout=b'Stopped successfully.',
        stderr=b''
    )

    result = ollama_runner.stop_ollama_model(model_name="mistral")
    assert result == 'Stopped successfully.'


@mock.patch('subprocess.run')
def test_stop_ollama_model_failure(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=['ollama', 'stop', 'mistral'],
        returncode=1,
        stdout=b'',
        stderr=b'Stop failed.'
    )

    result = ollama_runner.stop_ollama_model(model_name="mistral")
    assert "Hiba történt" in result


@mock.patch('subprocess.run', side_effect=Exception("subprocess error"))
def test_stop_ollama_model_exception(mock_run):
    result = ollama_runner.stop_ollama_model(model_name="mistral")
    assert "Hiba történt" in result
