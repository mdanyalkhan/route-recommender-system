from os.path import *


def parent_directory_at_level(current_path: str, level: int):
    """
    Returns file path at the specified level.
    :param current_path: Name of the current file path
    :param level: (int) the level in which you want to return the parent path.
    :return: parent_path (str) the string file path at the specified level.
    """
    parent_path: str = current_path
    for i in range(0, level):
        parent_path = dirname(parent_path)

    return parent_path
