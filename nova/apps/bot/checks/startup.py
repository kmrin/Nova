from discord import Client, Intents, LoginFailure

from ..log import Logger, format_exception

logger = Logger.STARTUP_CHECKS


async def check_token(token: str) -> bool:
    logger.info("Checking token validity")
    
    dummy = Client(intents=Intents.default())
    
    @dummy.event
    async def on_ready() -> None:
        await dummy.close()
    
    try:
        await dummy.start(token)
        
        if not dummy.user:
            logger.error("Token is invalid, I have no user")
            return False
        
        logger.info(f"Token is valid, I am {dummy.user.display_name}!")
        return True
    
    except LoginFailure as e:
        await dummy.close()
        
        logger.error("Invalid token")
        return False
    
    except Exception as e:
        await dummy.close()
        
        logger.error(f"An unknown error occurred while checking the token: {format_exception(e)}")
        return False