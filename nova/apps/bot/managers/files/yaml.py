import os
import yaml

from typing import Optional
from yaml import YAMLError

from ...helpers import get_os_path


def read(p: str, create: bool = False, silent: bool = False, from_root: bool = False) -> Optional[list | dict]:
    from ...log import Logger, log_exception
    
    logger = Logger.YAML
    yaml_path = get_os_path(p, from_root)

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            file = yaml.safe_load(f)

            if not silent:
                logger.info(f"Read '{yaml_path}'")

            return file
    
    except YAMLError as e:
        logger.error(f"Tried reading '{yaml_path}' but its sintax is invalid")
        log_exception(e, logger)
        
        return None
    
    except FileNotFoundError:
        logger.error(f"Tried reading '{yaml_path}' but it doesn't exist")
        
        if create:
            if not silent:
                logger.warning(f"Creating it as per request")
            
            write(yaml_path, {}, silent=silent, from_root=from_root)
            
            return read(p, silent=silent, from_root=from_root)
        
        return None
    
    except Exception as e:
        log_exception(e, logger)
        
        return None


def write(p: str, data: list | dict, silent: bool = False, from_root: bool = False, *args, **kwargs) -> bool:
    from ...log import Logger, log_exception
    
    logger = Logger.YAML
    
    yaml_path = get_os_path(p, from_root)
    yaml_dir = os.path.dirname(yaml_path)
    
    os.makedirs(yaml_dir, exist_ok=True)
    
    try:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, *args, **kwargs)
        
        file_data = read(p, silent=silent, from_root=from_root)
        
        if file_data != data:
            logger.error(f"File was written but its data did not match the provided data")
            
            return False
        
        if not silent:
            logger.info(f"Wrote to '{yaml_path}'")
        
        return True
    
    except YAMLError as e:
        logger.error(f"Tried writing to '{yaml_path}' but its sintax is invalid")
        log_exception(e, logger)
        
        return False
    
    except Exception as e:
        log_exception(e, logger)
        
        return False