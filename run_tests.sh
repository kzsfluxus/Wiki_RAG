#!/bin/bash

# A projekt gyökérkönyvtár beállítása
export PYTHONPATH=$(pwd)

echo "PYTHONPATH beállítva erre: $PYTHONPATH"

# Pytest lefedettség mérés futtatása a tests könyvtárral
pytest --cov=. tests/ --cov-report=term-missing

# Siker esetén kilépési kód 0
exit $?

