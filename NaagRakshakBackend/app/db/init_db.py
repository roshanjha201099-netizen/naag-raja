import os
import asyncio
import pandas as pd
import logging
from sqlalchemy import select
from app.database import get_engine, get_sessionmaker, Base
from app.db.models import Species, SpeciesDistribution, MedicalFacility, RescueFacility
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("naagrakshak.init_db")

SAMPLE_FACILITIES = [
    {
        "id": "hosp_bh_01",
        "name": "PMCH Patna (Patna Medical College & Hospital)",
        "type": "Govt Apex Hospital",
        "state": "Bihar",
        "district": "Patna",
        "address": "Ashok Rajpath, Patna, Bihar 800004",
        "phone": "+91 612 230 0080",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 32,
        "latitude": 25.6207,
        "longitude": 85.1500
    },
    {
        "id": "hosp_bh_02",
        "name": "NMCH Patna (Nalanda Medical College)",
        "type": "Govt Medical College",
        "state": "Bihar",
        "district": "Patna",
        "address": "Kankarbagh Main Rd, Patna, Bihar 800020",
        "phone": "+91 612 235 4828",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 20,
        "latitude": 25.5960,
        "longitude": 85.1760
    },
    {
        "id": "hosp_bh_03",
        "name": "AIIMS Patna Emergency Toxicology",
        "type": "Central Govt Apex Institute",
        "state": "Bihar",
        "district": "Patna",
        "address": "Phulwari Sharif, Patna, Bihar 801507",
        "phone": "+91 612 245 1070",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 45,
        "latitude": 25.5604,
        "longitude": 85.0456
    },
    {
        "id": "hosp_bh_04",
        "name": "Sadar Hospital Madhubani",
        "type": "District Headquarter Hospital",
        "state": "Bihar",
        "district": "Madhubani",
        "address": "Station Road, Madhubani, Bihar 847211",
        "phone": "+91 6276 222 240",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 12,
        "latitude": 26.3508,
        "longitude": 86.0750
    },
    {
        "id": "hosp_wb_01",
        "name": "Calcutta National Medical College & Hospital (CNMCH)",
        "type": "Govt Medical College",
        "state": "West Bengal",
        "district": "Kolkata",
        "address": "32, Gorachand Road, Beniapukur, Kolkata",
        "phone": "+91 33 2284 4000",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 24,
        "latitude": 22.5452,
        "longitude": 88.3685
    },
    {
        "id": "hosp_wb_02",
        "name": "Burdwan Medical College & Hospital",
        "type": "Govt Medical College",
        "state": "West Bengal",
        "district": "Burdwan",
        "address": "Baburbag, Purba Bardhaman, West Bengal",
        "phone": "+91 342 265 6652",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 18,
        "latitude": 23.2384,
        "longitude": 87.8596
    },
    {
        "id": "hosp_mh_01",
        "name": "KEM Hospital & Seth GS Medical College",
        "type": "Govt Medical College",
        "state": "Maharashtra",
        "district": "Mumbai",
        "address": "Acharya Donde Marg, Parel, Mumbai",
        "phone": "+91 22 2410 7000",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 35,
        "latitude": 19.0016,
        "longitude": 72.8427
    },
    {
        "id": "hosp_dl_01",
        "name": "AIIMS New Delhi Emergency Department",
        "type": "Central Govt Apex Institute",
        "state": "Delhi",
        "district": "New Delhi",
        "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi",
        "phone": "+91 11 2658 8500",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 50,
        "latitude": 28.5672,
        "longitude": 77.2100
    }
]

SAMPLE_RESCUE = [
    {
        "id": "resc_nat_01",
        "name": "Forest Department Emergency Dispatch",
        "organization": "Ministry of Environment & Forests",
        "state": "All Regions / Nationwide",
        "district": "All Districts",
        "phone": "1926",
        "response_hours": "24/7 Emergency Wildlife Helpline"
    },
    {
        "id": "resc_bh_01",
        "name": "Bihar Wildlife Rescue Cell",
        "organization": "Department of Environment, Forest & Climate Change",
        "state": "Bihar",
        "district": "Patna / Madhubani / All Districts",
        "phone": "+91 612 222 6405",
        "response_hours": "24x7 Dispatch"
    }
]

async def create_postgres_db_if_not_exists():
    try:
        import asyncpg
        logger.info("Checking if PostgreSQL database 'naagrakshak' exists...")
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_SERVER,
            port=int(settings.POSTGRES_PORT),
            database="postgres"
        )
        db_exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", settings.POSTGRES_DB)
        if not db_exists:
            logger.info(f"PostgreSQL database '{settings.POSTGRES_DB}' does not exist. Creating it now...")
            await conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')
            logger.info(f"Created PostgreSQL database '{settings.POSTGRES_DB}'.")
        await conn.close()
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL default database: {e}. SQLite fallback will be used if needed.")

async def init_db():
    await create_postgres_db_if_not_exists()
    logger.info("Initializing Database Tables...")
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sm = get_sessionmaker()
    async with sm() as session:
        # Check if species table already populated
        res = await session.execute(select(Species))
        existing_species = res.scalars().first()

        if not existing_species and os.path.exists(settings.SPECIES_DATA_PATH):
            logger.info(f"Seeding Species Taxonomy from {settings.SPECIES_DATA_PATH}...")
            df = pd.read_csv(settings.SPECIES_DATA_PATH)
            
            for _, row in df.iterrows():
                is_venomous = str(row.get("venomous_status", "")).lower() in ["venomous", "highly venomous", "true"]
                is_medically_sig = str(row.get("venomous_status", "")).lower() in ["highly venomous", "true"]
                
                safety_lvl = "CRITICAL" if is_medically_sig else ("HIGH" if is_venomous else "LOW")

                species_obj = Species(
                    scientific_name=row["scientific_name"],
                    common_name=row.get("common_name", row["scientific_name"]),
                    hindi_name=row.get("hindi_name", row.get("common_name", "")),
                    family=row.get("family", "Unknown"),
                    genus=row.get("genus", row["scientific_name"].split()[0] if " " in row["scientific_name"] else ""),
                    venomous=is_venomous,
                    medically_significant=is_medically_sig,
                    safety_level=safety_lvl,
                    habitat=row.get("habitat", "Agricultural bunds, forests, and human habitations across India."),
                    description=row.get("description", f"Morphology key for {row['scientific_name']}"),
                    safety_message=f"Maintain standoff distance. Do not provoke."
                )
                session.add(species_obj)
            await session.commit()
            logger.info("Species seeding complete.")

        # Seed Medical Facilities
        res_med = await session.execute(select(MedicalFacility))
        if not res_med.scalars().first():
            logger.info("Seeding ASV Medical Facilities...")
            for f in SAMPLE_FACILITIES:
                session.add(MedicalFacility(**f))
            await session.commit()

        # Seed Rescue Facilities
        res_resc = await session.execute(select(RescueFacility))
        if not res_resc.scalars().first():
            logger.info("Seeding Rescue Helplines...")
            for r in SAMPLE_RESCUE:
                session.add(RescueFacility(**r))
            await session.commit()

    logger.info("Database Seeding Finished Successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
