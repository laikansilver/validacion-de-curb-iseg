#!/usr/bin/env python3
"""
Script de entrada principal para validar CURPs contra RENAPO
Uso: python validar.py <CURP>
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "scripts"))
from validar_curp_simple import main

if __name__ == "__main__":
    main()
