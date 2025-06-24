import os
import json

from typing import Optional
from json import JSONDecodeError

from ...helpers import get_os_path


def read(p: str, create: bool = False, silent: bool = False, from_root: bool = False) -> Optional[list | dict]:
    from ...log import Logger, log_exception
    
    logger = Logger.JSON
    json_path = get_os_path(p, from_root)
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            file = json.load(f)
            
            if not silent:
                logger.info(f"Read '{json_path}'")
            
            return file
    
    except JSONDecodeError as e:
        logger.error(
            f"Tried reading a file at '{p}' but it's sintax is invalid " \
            f"[POS: {e.pos} | LINE No.: {e.lineno} | COL No.: {e.colno}]"
        )
        
        return None
    
    except FileNotFoundError:
        logger.error(f"Tried reading '{json_path}' but it doesn't exist")
        
        if create:
            if not silent:
                logger.warning(f"Creating it as per request")
            
            write(json_path, {}, silent=silent, from_root=from_root)
            
            return read(p, silent=silent, from_root=from_root)
        
        return None
    
    except Exception as e:
        log_exception(e, logger)
        
        return None


def write(p: str, data: list | dict, silent: bool = False, from_root: bool = False, *args, **kwargs) -> bool:
    from ...log import Logger, log_exception
    
    logger = Logger.JSON
    
    json_path = get_os_path(p, from_root)
    json_dir = os.path.dirname(json_path)
    
    os.makedirs(json_dir, exist_ok=True)
    
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, *args, **kwargs)
        
        file_data = read(p, silent=silent, from_root=from_root)
        
        if file_data != data:
            logger.error(f"File was written but its data did not match the provided data")
            
            return False
        
        if not silent:
            logger.info(f"Wrote to '{json_path}'")
        
        return True
    
    except JSONDecodeError as e:
        logger.error(
            f"Tried reading a file at '{p}' but it's sintax is invalid " \
            f"[POS: {e.pos} | LINE No.: {e.lineno} | COL No.: {e.colno}]"
        )

        return False

    except Exception as e:
        log_exception(e, logger)

        return False