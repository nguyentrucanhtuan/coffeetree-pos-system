import asyncio
import argparse
import json
import logging
import os
import sys
from typing import Any, Type

# Add backend to sys.path to allow imports like 'app.main'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal, Base
from app.main import REGISTERED_MODULES

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def drop_tables(module_name: str = None):
    """Drop tables for a specific module or all modules."""
    async with engine.begin() as conn:
        if module_name:
            # Find the module class
            module_cls = next((m for m in REGISTERED_MODULES if m._module_name == module_name), None)
            if not module_cls:
                logger.error(f"❌ Module '{module_name}' not found in REGISTERED_MODULES.")
                return False
            
            # Drop the main table
            table_name = module_cls._sa_model.__tablename__
            logger.info(f"🗑 Dropping table '{table_name}'...")
            await conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            
            # Drop M2M junction tables if any
            for m2m_table in module_cls._sa_model._m2m_tables.values():
                logger.info(f"🗑 Dropping junction table '{m2m_table.name}'...")
                await conn.execute(text(f"DROP TABLE IF EXISTS {m2m_table.name}"))
        else:
            logger.info("🗑 Dropping ALL tables...")
            # We use metadata to drop all tables tracked by Base
            await conn.run_sync(Base.metadata.drop_all)
    return True

async def create_tables(module_name: str = None):
    """Create tables for a specific module or all modules."""
    async with engine.begin() as conn:
        if module_name:
            module_cls = next((m for m in REGISTERED_MODULES if m._module_name == module_name), None)
            if not module_cls:
                return False
            
            logger.info(f"🏗 Creating table for module '{module_name}'...")
            # Create the specific table using metadata
            # await conn.run_sync(module_cls._sa_model.__table__.create) # This is tricky with M2M
            # Simple way: just run create_all, it only creates missing ones
            await conn.run_sync(Base.metadata.create_all)
        else:
            logger.info("🏗 Creating ALL tables...")
            await conn.run_sync(Base.metadata.create_all)
    return True

async def seed_module(module_cls: Type[Any]):
    """Seed data for a module from its JSON file."""
    module_name = module_cls._module_name
    # Use absolute path relative to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    seed_path = os.path.abspath(os.path.join(script_dir, "..", "seeds", f"{module_name}.json"))
    
    if not os.path.exists(seed_path):
        logger.info(f"ℹ️ No seed file found for '{module_name}' at {seed_path}")
        return

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        async with AsyncSessionLocal() as db:
            for item in data:
                # Create SA model instance
                obj = module_cls._sa_model(**item)
                db.add(obj)
            await db.commit()
            logger.info(f"✅ Seeded {len(data)} records for '{module_name}'")
    except Exception as e:
        logger.error(f"❌ Error seeding '{module_name}': {e}")

async def reset_module(module_name: str):
    """Reset a specific module (drop, create, seed)."""
    module_cls = next((m for m in REGISTERED_MODULES if m._module_name == module_name), None)
    if not module_cls:
        logger.error(f"❌ Module '{module_name}' not found.")
        return

    if await drop_tables(module_name):
        await create_tables(module_name)
        await seed_module(module_cls)
        logger.info(f"✨ Module '{module_name}' reset successfully.")

async def reset_all():
    """Reset everything."""
    if await drop_tables():
        await create_tables()
        for module_cls in REGISTERED_MODULES:
            await seed_module(module_cls)
        logger.info("✨ All modules reset successfully.")

def main():
    parser = argparse.ArgumentParser(description="CoffeeTree Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # reset-module
    reset_mod_parser = subparsers.add_parser("reset-module", help="Reset a specific module")
    reset_mod_parser.add_argument("name", help="Name of the module (e.g., products)")

    # reset-all
    subparsers.add_parser("reset-all", help="Reset all modules and database")

    # list-modules
    subparsers.add_parser("list-modules", help="List all registered modules")

    args = parser.parse_args()

    if args.command == "reset-module":
        asyncio.run(reset_module(args.name))
    elif args.command == "reset-all":
        asyncio.run(reset_all())
    elif args.command == "list-modules":
        print("\nRegistered Modules:")
        for m in REGISTERED_MODULES:
            print(f"- {m._module_name} ({m._description})")
        print("")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
