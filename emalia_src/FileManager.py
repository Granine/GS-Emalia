import os
import mimetypes
"""Functions to perform file operation
"""

def check_path_in_range(target_path:str, check_path:str, layer:int=1) -> bool:
    """Check target_path inside the layer count of check_path, use parent directory instead of actual file
    @param `target_path:str` target to check
    @param `check_path:str`  path to check
    @param `layer:int` range of directory layers to check, if == 0 return tru if exact match, <0 always false
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

def walk_all(path, target_type="all")->str:
    """
    [generator] get all files in current directory and all levels below
    @param `path:string` path to search
    @param `target_type:string` "all", "directory"/"dir" (only return directories) or "file" (only return files)
    @return `:str` each time return the full path to a file in path
    """
    if target_type not in ("all", "dir", "directory", "file"):
        raise ValueError("Unknown target_type")
    for root, dirs, files in os.walk(os.path.realpath(path)):
        if (target_type == "directory") or (target_type == "dir") or (target_type == "all"):
            for dir_name in dirs:
                yield os.path.join(root, dir_name)
        if (target_type == "file") or (target_type == "all"):
            for file_name in files:
                yield os.path.join(root, file_name)
            

def search_all(search_string:str, path:str=os.curdir, only_base_name:bool=True, target_type:str="all", min_size:float=-1.0, max_size:float=-1, black_list:list=[], exception:bool=True)->list:
    """
    search for file or directory based on file name, walk all sub dirs, case sensitive
    @param `search_string:str` name of file to start searching
    @param `path:str` path to search
    @param `only_file_name:bool` if True, will only search for file_name in base path name, not whole path
    @param `target_type:str` all, directory/dir or file
    @param `min_size:float` minimal size of target, in bytes, -1 for no boundary
    @param `max_size:float` maximum size of target, in bytes, -1 for no boundary
    @param `exception:bool` if True raise FileNotFoundError if not found, else just return empty
    @param `black_list:list of str` key word to ignore in search, will check full path for such words
    @return `:list` return any file where file_name is part of base name
    @
    """
    found = False
    found_files = []
    for file in walk_all(path, target_type):
        # if name in base = good, else if user wants, check whole path for file_name, also check no black_listed word is present
        if ((search_string in os.path.basename(file)) or ((not only_base_name) and (search_string in file))) and (not any([b_word in file for b_word in black_list])):
            # if found, then check file size to + performance
            size = os.path.getsize(file)
            if (min_size <= size) or min_size<0:
                if (size <= max_size) or max_size<0:
                    found = True
                    found_files.append(file)
    if not found:
        raise FileNotFoundError(f"File \"{search_string}\" not found in: {os.path.realpath(path)}")
    return found_files

def search_exact(search_string:str, path=os.curdir, target_type="all", ignore_type:bool=True, exception:bool=True)->str:
    """
    search all. but return the only exact match result that is right aligned
    @param `search_string:str` name of file to start searching
    @param `path:str` path to search
    @param `target_type:str` all, directory(or dir) or file
    @param `min_size:float` minimal size of target, in bytes
    @param `max_size:float` maximum size of target, in bytes
    @param `ignore_type:bool` if True, will only attempt to match the path before "." in found files and file_name
    @param `exception:bool` if True raise FileNotFoundError if not found, else just return empty ""
    @return `:str` one path if exact match is made with last part of found path and the match is unique (no other file can be matched)
    @raise FileNotFoundError if not found
    Example: "a/b/c1.txt" is found "c1.txt", "b/c1.txt", "1.txt" but not with "a/b/c" or "c.txt"
    """
    matches = []
    for file in search_all(search_string, path, target_type=target_type, exception=exception):
        # check file_name matches the last section of file
        if ignore_type:
            # remove part of path after . from filename and file
            search_string = search_string.rsplit(".", 1)[0]
            file_ignored_type = file.rsplit(".", 1)[0]
            if search_string == file_ignored_type[-len(str(search_string)):]:
                matches.append(file)
        else:
            if search_string == file[-len(str(search_string))]:
                matches.append(file)
            
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:   
        if exception: 
            raise FileNotFoundError("No file found")
        else:
            return ""
    else:
        if exception: 
            raise FileNotFoundError("More than 1 file found, use search_all instead")
        else:
            return ""


def get_file_info(path:str, block:list):
    info = {}
    
    try:
        # Check if file exists
        if not os.path.exists(path):
            raise FileNotFoundError("File not found")
        
        # Get file size
        size = os.path.getsize(path)
        info['size'] = size

        # Get file extension
        ext = os.path.splitext(path)[1].lower()
        info['extension'] = ext
        
        # Get the file type
        type_info = mimetypes.guess_type(path)
        if type_info[0]:
            info['type'] = type_info[0]

        # Get the encoding
        if type_info[1]:
            info['encoding'] = type_info[1]

    except Exception as e:
        info['error'] = str(e)

    # Remove keys from block list
    for key in block:
        if key in info:
            del info[key]
            
    return info