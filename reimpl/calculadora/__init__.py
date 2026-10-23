"""Reimplementação da Calculadora do Windows 11.2607.0.0 (modos Padrão, Científico e Programador, histórico e
memória) feita só a partir de `relatorio/` (Fase 5, escopo 3a–3d)."""
from .viewmodel import Calculadora
from .teclas import pressionar

__all__ = ['Calculadora', 'pressionar']
