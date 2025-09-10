import asyncio
import logging

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kompass")

class KompassServer(Server):
    def create_initialization_options(self):
        logger.info("✅ Kompass Server is ready and initialized")
        return super().create_initialization_options()

server = KompassServer("kompass")

async def main():
    logger.info("🚀 Starting Kompass Server")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Kompass Server stopped")
    except Exception as e:
        logger.error(f"💥 Kompass Server crashed: {e}")