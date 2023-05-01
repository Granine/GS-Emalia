import tempfile
from pathlib import Path
import pytest
import sys
sys.path.append(f"{__file__}/../../../emalia_src")
import FileManager

def test_check_path_in_range_1_layer():
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        check_path = base_dir / "a/b/c/d"
        check_path.mkdir(parents=True, exist_ok=True)
        target_file = base_dir / "a/b/emlia_main.py"
        target_file.touch()

        #same layer
        check_path = base_dir / "a/b"
        assert FileManager.check_path_in_range(target_file, check_path, 1) == True
        
        #same layer file
        check_path = base_dir / "a/b/c1.txt"
        check_path.touch()
        assert FileManager.check_path_in_range(target_file, check_path, 1) == True
        
        # Layer above false
        check_path = base_dir / "a"
        assert FileManager.check_path_in_range(target_file, check_path, 1) == False
        
        # Layer above false file
        check_path = base_dir / "a/b1.txt"
        check_path.touch()
        assert FileManager.check_path_in_range(target_file, check_path, 1) == False
        
        #layer below False
        check_path = base_dir / "a/b/c"
        check_path.parent.mkdir(parents=True, exist_ok=True)
        assert FileManager.check_path_in_range(target_file, check_path, 1) == False

        #layer below False file
        check_path = base_dir / "a/b/c/text.txt"
        check_path.parent.mkdir(parents=True, exist_ok=True)
        check_path.touch()
        assert FileManager.check_path_in_range(target_file, check_path, 1) == False
        
def test_check_path_in_range_multi_layer():
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        check_path = base_dir / "a/b/c/d"
        check_path.mkdir(parents=True, exist_ok=True)
        target_file = base_dir / "a/b/emlia_main.py"
        target_file.touch()
        
        
        #layer above true
        check_path = base_dir / "a"
        assert FileManager.check_path_in_range(target_file, check_path, 2) == True
        
        #layer below True
        check_path = base_dir / "a/b/c/text.txt"
        check_path.touch()
        assert FileManager.check_path_in_range(target_file, check_path, 2) == True

        check_path = base_dir / "a/b/c/d"
        assert FileManager.check_path_in_range(target_file, check_path, 2) == False

        check_path = base_dir / "a/b/c/d/text.txt"
        check_path.touch()
        assert FileManager.check_path_in_range(target_file, check_path, 2) == False
        
def test_check_path_in_range_diverge_layer():
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        check_path = base_dir / "a/b/c/d"
        check_path.mkdir(parents=True, exist_ok=True)
        check_path = base_dir / "A/B/C/D"
        check_path.mkdir(parents=True, exist_ok=True)
        target_file = base_dir / "a/b/emlia_main.py"
        target_file.touch()
        
        # diverge path simple 
        check_path = base_dir / "A"
        assert FileManager.check_path_in_range(target_file, check_path, 4) == True
        
        # diverge path False
        check_path = base_dir / "A/B"
        assert FileManager.check_path_in_range(target_file, check_path, 4) == False
        
        # diverge path True
        check_path = base_dir / "A/B"
        check_path.touch()
        assert FileManager.check_path_in_range(target_file, check_path, 5) == True