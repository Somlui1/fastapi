from typing import Union
from google import genai
from fastapi import FastAPI
import base64
import requests
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error
import asyncpg

app = FastAPI()

class Supplier(BaseModel):
    name: str
    contact: str

# ✅ Model หลัก (object ที่มี object ซ้อนอยู่ข้างใน)
class Item(BaseModel):
    name: str
    price: float
    quantity: int
    supplier: Supplier  # 👈 ซ้อน object

@app.post("/testing/items/")
async def create_item(item: Item):
    total = item.price * item.quantity
    return item.model_dump()

class AnyJsonModel(BaseModel):
    model_config = ConfigDict(extra="allow")  # ยอมรับ field ใดก็ได้

@app.post("/testing/anyjson/")
async def receive_any_json(item: AnyJsonModel):
    return item.model_dump()  # แปลงเป็น dict



DATABASE_CONFIG = {
    "user": "admin",
    "password": "it@apico4U",
    "database": "license_logs",
    "host": "172.26.0.2",
    "port": 5432,
}

@app.get("/test-db-pg-connection")
async def test_db_connection():
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        await conn.close()
        return {"status": "success", "message": "Database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")




def get_connection():
    return mysql.connector.connect(
        host="172.17.0.3",
        port=3306,
        user="admin",
        password="root",
        database="glpi"
    )


@app.get("/test-db-mysql-connection")
def test_db_connection():
    try:
        print("Connecting to MySQL...")
        conn = get_connection()
        print("Connection established:", conn.is_connected())
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            return {
                "status": "success",
                "message": "Connected to MySQL",
                "version": version[0]
            }
        else:
            return {
                "status": "fail",
                "message": "Failed to connect to MySQL"
            }
    except Error as e:
        print(f"MySQL Error: {e}")  # ดู error ใน console
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as ex:
        print(f"Unexpected Error: {ex}")  # ดู error อื่น ๆ
        return {
            "status": "error",
            "message": str(ex)
        }

@app.get("/")
def readd_root():
    return {"Hello": "Welcome to FastAPI Edit at: 07 July 2025 16:51:20"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None,p: Union[str, None] = None):
    result = q+p
    return {"item_id": item_id, "result": result}

@app.get("/genai/{question}")
async def genai_response(question: str):
    client = genai.Client(api_key="AIzaSyBeUhdYmgosd4k19eDY8mswxYnrOq-hl34")
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=str(question),
)
    return {"question": question, "response": response.text}


TENANTS = {
    "ah": {
        "Credential": "583db905e5af13cd_r_id:it@minAPI1WGant!",
        "APIKey": "FfSghSoNzPlloALCK9LN5E46rzGnAYqxJ+mgirtf",
        "Account": "WGC-3-981e96282dcc4ad0856c"
    },
    "as": {
        "Credential": "8f6543f42f463fc6_r_id:5QG+M=H+)3iL)Fw",
        "APIKey": "yujbaVOGmOi5rzxU2wBwcCJMLrkKyxU7Fbw8rQgj",
        "Account": "WGC-3-50b8aa46e31d448698c7"
    },
    "ar": {
        "Credential": "7be27fa3e7cc352a_r_id:^^K7Uc~7PYruSek",
        "APIKey": "66eMRiegSh7EhWQh6C9S5hAnQ75OScy6T9kx+VKo",
        "Account": "WGC-3-048294f7f1ed497981c8"
    }
}


def fetch_devices(tenant_name):
    t = TENANTS[tenant_name]
    try:
        cred_b64 = base64.b64encode(t["Credential"].encode()).decode()
        token_resp = requests.post(
            "https://api.jpn.cloud.watchguard.com/oauth/token",
            headers={
                "accept": "application/json",
                "Authorization": f"Basic {cred_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"grant_type": "client_credentials", "scope": "api-access"}
        )
        token_resp.raise_for_status()
        token = token_resp.json().get("access_token")
        if not token:
            raise Exception("Token is null")

        url = (
            f"https://api.jpn.cloud.watchguard.com/rest/endpoint-security/"
            f"management/api/v1/accounts/{t['Account']}/devices"
        )
        dev_resp = requests.get(
            url,
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "WatchGuard-API-Key": t["APIKey"],
                "Authorization": f"Bearer {token}"
            },
            timeout=120
        )
        dev_resp.raise_for_status()
        return dev_resp.json().get("data", []), None

    except Exception as e:
        return [], str(e)


@app.get("/watchguard/devices")
def get_all_devices():
    all_devices = []
    errors = []

    for name in TENANTS:
        devices, err = fetch_devices(name)
        if err:
            errors.append({"tenant": name, "error": err})
        else:
            all_devices.extend(devices)

    return {"devices": all_devices, "errors": errors}


@app.get("/watchguard/{tenant_name}")
def get_devices_by_tenant(tenant_name: str):
    if tenant_name not in TENANTS:
        return {"error": f"Unknown tenant: {tenant_name}"}

    devices, err = fetch_devices(tenant_name)
    return {
        "devices": devices,
        "errors": [{"tenant": tenant_name, "error": err}] if err else []
    }




@app.get("/glpi/device/")
def get_devices_by_tenant(name: Optional[str] = None, boolean: Optional[bool] = None):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)  # dictionary=True เพื่อให้ได้ dict แทน tuple
        sql = """
            SELECT b.comment, b.contact, b.contact_num,
                   b.date_creation, b.date_mod, b.entities_id, b.id, b.is_deleted, b.is_dynamic,
                   b.is_recursive, b.is_template, b.last_boot, b.last_inventory_update, b.name,
                   b.networks_id, b.otherserial, b.serial, b.template_name, b.ticket_tco,
                   b.users_id, b.users_id_tech, b.uuid,
                   g1.completename AS tech_group,
                   g2.completename AS user_group,
                   a.name AS autoupdate,
                   l.completename AS location,
                   m.name AS computermodel,
                   t.name AS computertype,
                   mf.name AS manufacturer,
                   s.completename AS assetstatus
            FROM glpi.glpi_computers b
            LEFT JOIN glpi.glpi_groups g1 ON b.groups_id_tech = g1.id
            LEFT JOIN glpi.glpi_groups g2 ON b.groups_id = g2.id
            LEFT JOIN glpi.glpi_autoupdatesystems a ON b.autoupdatesystems_id = a.id
            LEFT JOIN glpi.glpi_locations l ON b.locations_id = l.id
            LEFT JOIN glpi.glpi_computermodels m ON b.computermodels_id = m.id
            LEFT JOIN glpi.glpi_computertypes t ON b.computertypes_id = t.id
            LEFT JOIN glpi.glpi_manufacturers mf ON b.manufacturers_id = mf.id
            LEFT JOIN glpi.glpi_states s ON b.states_id = s.id
            WHERE 1 = 1
        """

        params = []

        if name:
            sql += " AND b.name LIKE %s"
            params.append(f"%{name}%")

        cursor.execute(sql, params)
        result = cursor.fetchall()

        if boolean is not None:
            return {"exists": bool(result)}

        return result

    except Error as e:
        return {"error": str(e)}

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
