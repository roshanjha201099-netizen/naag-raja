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
    # --- BIHAR ---
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
        "id": "hosp_bh_05",
        "name": "DMCH Darbhanga (Darbhanga Medical College)",
        "type": "Govt Medical College",
        "state": "Bihar",
        "district": "Darbhanga",
        "address": "Laheriasarai, Darbhanga, Bihar 846003",
        "phone": "+91 6272 233 228",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 16,
        "latitude": 26.1362,
        "longitude": 85.8975
    },
    {
        "id": "hosp_bh_06",
        "name": "SKMCH Muzaffarpur (Sri Krishna Medical College)",
        "type": "Govt Medical College",
        "state": "Bihar",
        "district": "Muzaffarpur",
        "address": "Uma Nagar, Muzaffarpur, Bihar 842004",
        "phone": "+91 621 223 0080",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 18,
        "latitude": 26.1524,
        "longitude": 85.4056
    },

    # --- WEST BENGAL ---
    {
        "id": "hosp_wb_01",
        "name": "Calcutta National Medical College & Hospital (CNMCH)",
        "type": "Govt Medical College",
        "state": "West Bengal",
        "district": "Kolkata",
        "address": "32, Gorachand Road, Beniapukur, Kolkata 700014",
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
        "address": "Baburbag, Purba Bardhaman, West Bengal 713104",
        "phone": "+91 342 265 6652",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 18,
        "latitude": 23.2384,
        "longitude": 87.8596
    },
    {
        "id": "hosp_wb_03",
        "name": "RG Kar Medical College & Hospital",
        "type": "Govt Medical College",
        "state": "West Bengal",
        "district": "Kolkata",
        "address": "1, Kshudiram Bose Sarani, Kolkata 700004",
        "phone": "+91 33 2555 7675",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 28,
        "latitude": 22.6041,
        "longitude": 88.3755
    },

    # --- MAHARASHTRA ---
    {
        "id": "hosp_mh_01",
        "name": "KEM Hospital & Seth GS Medical College",
        "type": "Govt Medical College",
        "state": "Maharashtra",
        "district": "Mumbai",
        "address": "Acharya Donde Marg, Parel, Mumbai 400012",
        "phone": "+91 22 2410 7000",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 35,
        "latitude": 19.0016,
        "longitude": 72.8427
    },
    {
        "id": "hosp_mh_02",
        "name": "BJ Government Medical College & Sassoon General Hospital",
        "type": "Govt Medical College",
        "state": "Maharashtra",
        "district": "Pune",
        "address": "Near Pune Railway Station, Sangamvadi, Pune 411001",
        "phone": "+91 20 2612 8000",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 30,
        "latitude": 18.5284,
        "longitude": 73.8741
    },

    # --- DELHI NCR ---
    {
        "id": "hosp_dl_01",
        "name": "AIIMS New Delhi Emergency Toxicology",
        "type": "Central Govt Apex Institute",
        "state": "Delhi NCR",
        "district": "New Delhi",
        "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi 110029",
        "phone": "+91 11 2658 8500",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 50,
        "latitude": 28.5672,
        "longitude": 77.2100
    },
    {
        "id": "hosp_dl_02",
        "name": "Lok Nayak Hospital (LNJP)",
        "type": "Govt Hospital",
        "state": "Delhi NCR",
        "district": "Central Delhi",
        "address": "Jawaharlal Nehru Marg, New Delhi 110002",
        "phone": "+91 11 2323 3000",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 40,
        "latitude": 28.6366,
        "longitude": 77.2407
    },

    # --- UTTAR PRADESH ---
    {
        "id": "hosp_up_01",
        "name": "KGMU Trauma Center (King George Medical University)",
        "type": "Govt Apex Medical University",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "address": "Shah Mina Road, Chowk, Lucknow, Uttar Pradesh 226003",
        "phone": "+91 522 225 7540",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 40,
        "latitude": 26.8687,
        "longitude": 80.9168
    },
    {
        "id": "hosp_up_02",
        "name": "GSVM Medical College & Hallet Hospital",
        "type": "Govt Medical College",
        "state": "Uttar Pradesh",
        "district": "Kanpur",
        "address": "Swaroop Nagar, Kanpur, Uttar Pradesh 208002",
        "phone": "+91 512 253 5483",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 22,
        "latitude": 26.4812,
        "longitude": 80.3090
    },

    # --- TAMIL NADU ---
    {
        "id": "hosp_tn_01",
        "name": "Rajiv Gandhi Government General Hospital (RGGGH)",
        "type": "Govt Apex Medical College",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "address": "EVR Periyar Salai, Park Town, Chennai, Tamil Nadu 600003",
        "phone": "+91 44 2530 5000",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 45,
        "latitude": 13.0818,
        "longitude": 80.2774
    },

    # --- KERALA ---
    {
        "id": "hosp_kl_01",
        "name": "Government Medical College Thiruvananthapuram",
        "type": "Govt Medical College",
        "state": "Kerala",
        "district": "Thiruvananthapuram",
        "address": "Medical College PO, Thiruvananthapuram, Kerala 695011",
        "phone": "+91 471 252 8300",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 35,
        "latitude": 8.5241,
        "longitude": 76.9294
    },

    # --- KARNATAKA ---
    {
        "id": "hosp_ka_01",
        "name": "Victoria Hospital (BMCRI)",
        "type": "Govt Medical College",
        "state": "Karnataka",
        "district": "Bengaluru",
        "address": "Fort Road, Opp. City Market, Bengaluru, Karnataka 560002",
        "phone": "+91 80 2670 1150",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 38,
        "latitude": 12.9644,
        "longitude": 77.5756
    },

    # --- GUJARAT ---
    {
        "id": "hosp_gj_01",
        "name": "Civil Hospital Ahmedabad (BJ Medical College)",
        "type": "Govt Apex Medical Center",
        "state": "Gujarat",
        "district": "Ahmedabad",
        "address": "Asarwa, Ahmedabad, Gujarat 380016",
        "phone": "+91 79 2268 3721",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 50,
        "latitude": 23.0531,
        "longitude": 72.6022
    },

    # --- RAJASTHAN ---
    {
        "id": "hosp_rj_01",
        "name": "SMS Hospital (Sawai Man Singh Medical College)",
        "type": "Govt Apex Hospital",
        "state": "Rajasthan",
        "district": "Jaipur",
        "address": "Jawaharlal Nehru Marg, Jaipur, Rajasthan 302004",
        "phone": "+91 141 256 0291",
        "asv_available": True,
        "icu_facility": True,
        "ventilator_count": 42,
        "latitude": 26.8973,
        "longitude": 75.8166
    }
]

SAMPLE_RESCUE = [
    {
        "id": "resc_nat_01",
        "name": "National Forest Emergency Helpline",
        "organization": "Ministry of Environment, Forest & Climate Change",
        "state": "All Regions / Nationwide",
        "district": "All Districts",
        "phone": "1926",
        "response_hours": "24/7 National Emergency Toll-Free"
    },
    {
        "id": "resc_bh_01",
        "name": "Bihar Wildlife Rescue Cell",
        "organization": "Department of Environment, Forest & Climate Change",
        "state": "Bihar",
        "district": "Patna / Madhubani / All Districts",
        "phone": "+91 612 222 6405",
        "response_hours": "24x7 State Rescue Dispatch"
    },
    {
        "id": "resc_wb_01",
        "name": "West Bengal Forest Wildlife Control Room",
        "organization": "West Bengal Forest Department",
        "state": "West Bengal",
        "district": "Kolkata / All Districts",
        "phone": "+91 33 2335 8581",
        "response_hours": "24x7 State Wildlife Emergency"
    },
    {
        "id": "resc_mh_01",
        "name": "Maharashtra Forest Wildlife Helpline",
        "organization": "Maharashtra Forest Department",
        "state": "Maharashtra",
        "district": "Mumbai / Pune / All Districts",
        "phone": "1926",
        "response_hours": "24x7 Wildlife Rescue Toll-Free"
    },
    {
        "id": "resc_dl_01",
        "name": "Delhi Wildlife Rescue Cell (Wildlife SOS)",
        "organization": "Department of Forests & Wildlife Delhi",
        "state": "Delhi NCR",
        "district": "New Delhi / All NCR",
        "phone": "+91 98719 63535",
        "response_hours": "24x7 Rapid Emergency Response"
    },
    {
        "id": "resc_up_01",
        "name": "UP Forest Emergency Control Room",
        "organization": "Uttar Pradesh Forest Department",
        "state": "Uttar Pradesh",
        "district": "Lucknow / All Districts",
        "phone": "1926",
        "response_hours": "24x7 Emergency Helpline"
    },
    {
        "id": "resc_tn_01",
        "name": "Tamil Nadu Forest Wildlife Headquarters",
        "organization": "Tamil Nadu Forest Department",
        "state": "Tamil Nadu",
        "district": "Chennai / All Districts",
        "phone": "+91 44 2432 1738",
        "response_hours": "24x7 Wildlife Control"
    },
    {
        "id": "resc_ka_01",
        "name": "Karnataka Forest Emergency Control",
        "organization": "Karnataka Forest Department",
        "state": "Karnataka",
        "district": "Bengaluru / All Districts",
        "phone": "1926",
        "response_hours": "24x7 Wildlife Emergency"
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
