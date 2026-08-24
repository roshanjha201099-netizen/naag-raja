import asyncio
import asyncpg

async def main():
    try:
        print("Connecting to PostgreSQL on localhost:5432 with user 'postgres'...")
        conn = await asyncpg.connect(
            user="postgres",
            password="7044",
            host="localhost",
            port=5432,
            database="postgres"
        )
        print("Connected to PostgreSQL server successfully!")
        
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'naagrakshak'")
        if not exists:
            print("Database 'naagrakshak' does not exist. Creating database...")
            await conn.execute("CREATE DATABASE naagrakshak")
            print("SUCCESS: Database 'naagrakshak' created in PostgreSQL!")
        else:
            print("Database 'naagrakshak' already exists in PostgreSQL.")
            
        await conn.close()
    except Exception as e:
        print("PostgreSQL connection error:", e)

if __name__ == "__main__":
    asyncio.run(main())
    
