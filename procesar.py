#!/usr/bin/env python3
"""
Script de entrada para procesar múltiples CURPs desde CSV
Uso: python procesar.py <archivo.csv> [nombre_salida]
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src" / "scripts"))
from procesar_curps import main

if __name__ == "__main__":
    main()
