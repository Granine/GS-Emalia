import pytest
import sys
sys.path.append(f"{__file__}/../../../emalia_src")
import emalia_main as emalia

def test_emalia_basic():
    emanager = emalia.EmailManager()
    assert emanager