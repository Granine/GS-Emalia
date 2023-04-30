import os
"""Functions to perform file operation
"""

def check_path_in_range(target_path:str, check_path:str, layer:int=1) -> bool:
    """Check target_path inside the layer count of check_path, use parent directory instead of actual file
    @param `target_path:str` target to check
    @param `check_path:str`  path to check
    @param `layer:int` range of directory layers to check
    @return `:bool` True if in range, False otherwise
    Example: if file a/b/c1.txt
        layer 1: same parent folder so a/b, a/b/c2.txt == True but not a or a/b/c/d.txt
        layer 2: parent folder and all content in one level child folder so a/b1.txt or a/b/c/d1.txt == True
        different parent: if file have different parents, calculate the path size example a/B/C1.txt have 3 layers 
    """
    # Get directory of target_path if it's a file
    if not os.path.isdir(target_path):
        target_path = os.path.dirname(target_path)
    if not os.path.isdir(check_path):
        check_path = os.path.dirname(check_path)
    # if path DNE
    if not os.path.isdir(target_path) or not os.path.isdir(check_path):
        return False

    # Normalize paths and split into components
    target_path_splitted = os.path.normpath(target_path).split(os.sep)
    check_path_splitted = os.path.normpath(check_path).split(os.sep)

    # Calculate depth difference between target_path and check_path 
    diff_layer = 0  
    for i in range(min(len(target_path_splitted), len(check_path_splitted))):
        # if difference is found in path, calculate number of directory differs
        if target_path_splitted[i] != check_path_splitted[i]:
            break
    else: # if ended without break, [i] is good, move to next index
        i = i + 1
    diff_layer = len(check_path_splitted[i:]) + len(target_path_splitted[i:])
            
    return diff_layer < layer
