import os
import time
import binascii
import logging
import threading
from datetime import datetime
import itertools

try:
    from zoneinfo import ZoneInfo
    TIMEZONE_AVAILABLE = True
except ImportError:
    TIMEZONE_AVAILABLE = False

import requests
from flask import Flask, jsonify, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from data_pb2 import AccountPersonalShowInfo
import uid_generator_pb2



app = Flask(__name__)
app.json.sort_keys = False


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


RELEASE_VERSION = "OB55"

USER_AGENT = (
    "Dalvik/2.1.0 (Linux; U; Android 9; "
    "ASUS_Z01QD Build/PI)"
)

DEFAULT_KEY = "Yg&tc%DEuh6%Zc^8"
DEFAULT_IV = "6oyZDr22E3ychjM%"

JWT_API_URL = "https://jwt-gen-api-lwte.onrender.com/token"


REGION_ACCOUNTS = {
    "VN": [
        {
            "uid": "8326070438",
            "password": "_STAR_rr0b6pe0W",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxODgyNjIwNTcwNCwibmlja25hbWUiOiJmeW9GRGxoWkJRWUJEZ1lBIiwibm90aV9yZWdpb24iOiJWTiIsImxvY2tfcmVnaW9uIjoiVk4iLCJleHRlcm5hbF9pZCI6IjA2YWFmZWM2YmY2MzcxMTg4ZTFkYmVmMzkzNDExYjVhIiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEzMi42IiwiY2xpZW50X3ZlcnNpb25fY29kZSI6IjIwMTkxMjEyMjkiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVk4iLCJleHRlcm5hbF91aWQiOjgzMjYwNzA0MzgsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjowLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6Ijc0MjhiMjUzZGVmYzE2NDAxOGM2MDRhMWViYmZlYmRmIiwidXNpbmdfdmVyc2lvbiI6MSwicmVsZWFzZV9jaGFubmVsIjoiYW5kcm9pZCIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTUiLCJleHAiOjE3OTI2NzQ2Mzd9.gCki2_5Je33K3I2gngkjCyDiJ9LdZNqM8KOX1QEkY_k"
        },
        {
            "uid": "8326070439",
            "password": "_STAR_itU58oni9",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxODgyNjIwNTgwNywibmlja25hbWUiOiJmQXBaWFExeFZEZFVlQT09Iiwibm90aV9yZWdpb24iOiJWTiIsImxvY2tfcmVnaW9uIjoiVk4iLCJleHRlcm5hbF9pZCI6ImJiMjY2YmFjNGUxZDA3NTNmNmUxMjViMDVhMjU4NTg0IiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEzMi42IiwiY2xpZW50X3ZlcnNpb25fY29kZSI6IjIwMTkxMjEyMjkiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVk4iLCJleHRlcm5hbF91aWQiOjgzMjYwNzA0MzksInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjowLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6Ijc0MjhiMjUzZGVmYzE2NDAxOGM2MDRhMWViYmZlYmRmIiwidXNpbmdfdmVyc2lvbiI6MSwicmVsZWFzZV9jaGFubmVsIjoiYW5kcm9pZCIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTUiLCJleHAiOjE3OTI2NzQ2Mzh9.s67xLIJ-Tyn7_w8pXuM5xCje1g50SN4mZWnam7fQ_xk"
        },
        {
            "uid": "8326070437",
            "password": "_STAR_c85tJAiWE",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxODgyNjIwNTg1NSwibmlja25hbWUiOiJZd1JQVjBzSUFsRWlEUkJRIiwibm90aV9yZWdpb24iOiJWTiIsImxvY2tfcmVnaW9uIjoiVk4iLCJleHRlcm5hbF9pZCI6IjhmYTEzNWNkNTQzMzBlNTVmNTRjYjY0ZjBkZTY3OGI2IiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEzMi42IiwiY2xpZW50X3ZlcnNpb25fY29kZSI6IjIwMTkxMjEyMjkiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVk4iLCJleHRlcm5hbF91aWQiOjgzMjYwNzA0MzcsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjowLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6Ijc0MjhiMjUzZGVmYzE2NDAxOGM2MDRhMWViYmZlYmRmIiwidXNpbmdfdmVyc2lvbiI6MSwicmVsZWFzZV9jaGFubmVsIjoiYW5kcm9pZCIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTUiLCJleHAiOjE3OTI2NzQ2Mzh9.2vPGG9JvBZ6GHmZwVdxrm5pFm9_q9InVuCfI8s-hnXA"
        },
        {
            "uid": "8326070986",
            "password": "_STAR_Oho6SVpi6",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxODgyNjIwNzk3MSwibmlja25hbWUiOiJmQXhCWFFocFV4VmJjMVFvIiwibm90aV9yZWdpb24iOiJWTiIsImxvY2tfcmVnaW9uIjoiVk4iLCJleHRlcm5hbF9pZCI6ImMzZjM3ZDUxOTdhZDFlYjQxZjNjMWNmNzAyMzE1MzliIiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEzMi42IiwiY2xpZW50X3ZlcnNpb25fY29kZSI6IjIwMTkxMjEyMjkiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVk4iLCJleHRlcm5hbF91aWQiOjgzMjYwNzA5ODYsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjowLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6Ijc0MjhiMjUzZGVmYzE2NDAxOGM2MDRhMWViYmZlYmRmIiwidXNpbmdfdmVyc2lvbiI6MSwicmVsZWFzZV9jaGFubmVsIjoiYW5kcm9pZCIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTUiLCJleHAiOjE3OTI2NzQ2NTd9.-0XZ7n-qkvr17cuQI64IZvbYgEdASFiooRI9j8CTNhY"
        },
        {
            "uid": "8326070960",
            "password": "_STAR_87u6s3Q9H",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxODgyNjIwODA3OCwibmlja25hbWUiOiJaUXBOVVZvTkdWYzlEQVZTIiwibm90aV9yZWdpb24iOiJWTiIsImxvY2tfcmVnaW9uIjoiVk4iLCJleHRlcm5hbF9pZCI6IjYxMGFkZTA4NjVjZDg2YWY1MzY5OTcxZDUyYWI2ZWViIiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEzMi42IiwiY2xpZW50X3ZlcnNpb25fY29kZSI6IjIwMTkxMjEyMjkiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVk4iLCJleHRlcm5hbF91aWQiOjgzMjYwNzA5NjAsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjowLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6Ijc0MjhiMjUzZGVmYzE2NDAxOGM2MDRhMWViYmZlYmRmIiwidXNpbmdfdmVyc2lvbiI6MSwicmVsZWFzZV9jaGFubmVsIjoiYW5kcm9pZCIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTUiLCJleHAiOjE3OTI2NzQ2NTd9.fAREnLToFwF5Ancrv1nrBLDiL8yjvDTKBCW8SlSbmQA"
        },
        {
            "uid": "8326070998",
            "password": "_STAR_0z7fBiuYZ",
            "jwt_token": "eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ.eyJhY2NvdW50X2lkIjoxODgyNjIwODE0OCwibmlja25hbWUiOiJaUUJGVVYwS0FsTXJEQ2s9Iiwibm90aV9yZWdpb24iOiJWTiIsImxvY2tfcmVnaW9uIjoiVk4iLCJleHRlcm5hbF9pZCI6IjI2OGQ0NDNjMmZkNmIzMzVmY2ZhNWQ1OWMyYmM5Y2EyIiwiZXh0ZXJuYWxfdHlwZSI6NCwicGxhdF9pZCI6MSwiY2xpZW50X3ZlcnNpb24iOiIxLjEzMi42IiwiY2xpZW50X3ZlcnNpb25fY29kZSI6IjIwMTkxMjEyMjkiLCJlbXVsYXRvcl9zY29yZSI6MTAwLCJpc19lbXVsYXRvciI6dHJ1ZSwiY291bnRyeV9jb2RlIjoiVk4iLCJleHRlcm5hbF91aWQiOjgzMjYwNzA5OTgsInJlZ19hdmF0YXIiOjEwMjAwMDAwNywic291cmNlIjowLCJsb2NrX3JlZ2lvbl90aW1lIjowLCJjbGllbnRfdHlwZSI6Miwic2lnbmF0dXJlX21kNSI6Ijc0MjhiMjUzZGVmYzE2NDAxOGM2MDRhMWViYmZlYmRmIiwidXNpbmdfdmVyc2lvbiI6MSwicmVsZWFzZV9jaGFubmVsIjoiYW5kcm9pZCIsInJlbGVhc2VfdmVyc2lvbiI6Ik9CNTUiLCJleHAiOjE3OTI2NzQ2NTh9.BJlh_HDTHsZ81ejrfD1QLziIqiqDi3k7Y4kv281M1Y8"
        },
    ],
}

region_cycles = {
    region: itertools.cycle(accounts)
    for region, accounts in REGION_ACCOUNTS.items()
}
cycle_locks = {region: threading.Lock() for region in REGION_ACCOUNTS}


jwt_tokens = {}
jwt_expiry = {}
jwt_lock = threading.Lock()
JWT_CACHE_SECONDS = 600

def create_http_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    retry = Retry(
        total=1,
        backoff_factor=0.2,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=50,
        pool_maxsize=50
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


http_session = create_http_session()


def get_formatted_time():
    if TIMEZONE_AVAILABLE:
        try:
            return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%I:%M %p, %A, %B %d, %Y")
        except Exception:
            pass
    return datetime.now().strftime("%I:%M %p, %A, %B %d, %Y")


def get_iso_time():
    if TIMEZONE_AVAILABLE:
        try:
            return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat()
        except Exception:
            pass
    return datetime.now().isoformat()


# ============================================================
# Protobuf -> dict
# ============================================================

def proto_to_dict(message):
    result = {}
    for field in getattr(message.DESCRIPTOR, "fields", []):
        value = getattr(message, field.name)
        val_type = type(value).__name__

        if "MapContainer" in val_type:
            map_result = {}
            for key, item in value.items():
                if hasattr(item, "DESCRIPTOR"):
                    map_result[key] = proto_to_dict(item)
                elif isinstance(item, bytes):
                    map_result[key] = binascii.hexlify(item).decode("utf-8")
                else:
                    map_result[key] = item
            result[field.name] = map_result

        elif "Repeated" in val_type:
            list_result = []
            for item in value:
                if hasattr(item, "DESCRIPTOR"):
                    list_result.append(proto_to_dict(item))
                elif isinstance(item, bytes):
                    list_result.append(binascii.hexlify(item).decode("utf-8"))
                else:
                    list_result.append(item)
            result[field.name] = list_result

        elif hasattr(value, "DESCRIPTOR"):
            result[field.name] = proto_to_dict(value)

        elif getattr(field, "type", None) == 14:
            try:
                result[field.name] = field.enum_type.values_by_number[value].name
            except Exception:
                result[field.name] = value

        elif isinstance(value, bytes):
            result[field.name] = binascii.hexlify(value).decode("utf-8") if value else ""

        else:
            result[field.name] = value

    return result


# ============================================================
# Token extraction & normalization
# ============================================================

def extract_token(data):
    if not isinstance(data, dict):
        return None
    token = data.get("jwt_token") or data.get("token") or data.get("access_token")
    if token:
        return token
    nested = data.get("data")
    if isinstance(nested, dict):
        token = nested.get("jwt_token") or nested.get("token") or nested.get("access_token")
        if token:
            return token
    return None


def normalize_token(token):
    if not token:
        return None
    token = str(token).strip()
    if token.startswith("Bearer "):
        return token[7:].strip()
    return token


def is_token_valid(token, min_ttl=60):
    """Kiểm tra token còn hạn sống tối thiểu min_ttl giây không bằng cách đọc exp từ payload JWT"""
    if not token:
        return False
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        import base64
        import json
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp", 0)
        return exp > (time.time() + min_ttl)
    except Exception:
        return True


def get_next_bot_token():
    """Lấy token của bot tiếp theo theo cơ chế Round-Robin, tự động lấy token mới nếu hết hạn"""
    accounts = REGION_ACCOUNTS.get("VN", [])
    if not accounts:
        raise Exception("Danh sách REGION_ACCOUNTS['VN'] đang trống.")

    cycle_pool = region_cycles.get("VN")
    c_lock = cycle_locks.get("VN", jwt_lock)

    max_attempts = len(accounts)
    for attempt in range(max_attempts):
        with c_lock:
            account = next(cycle_pool)

        token = account.get("jwt_token")
        # Nếu token sẵn có và còn hạn thì dùng luôn
        if token and is_token_valid(token):
            return normalize_token(token)

        # Nếu không có hoặc token đã hết hạn, tự động đăng nhập lấy token mới
        uid = account.get("uid")
        password = account.get("password")
        if not uid or not password:
            continue

        try:
            logger.info("[VN] Đang lấy lại JWT token mới cho bot UID: %s...", uid)
            response = http_session.get(
                JWT_API_URL,
                params={"uid": uid, "password": password},
                timeout=10
            )
            response.raise_for_status()
            new_token = extract_token(response.json())
            if new_token:
                normalized = normalize_token(new_token)
                account["jwt_token"] = normalized  # Lưu lại vào cache của account này
                return normalized
            logger.warning("[VN] Không nhận được token cho UID: %s (lần thử %d/%d)", uid, attempt + 1, max_attempts)
        except requests.exceptions.RequestException as e:
            logger.warning("[VN] Lỗi lấy JWT cho UID %s: %s (lần thử %d/%d)", uid, e, attempt + 1, max_attempts)

    raise Exception("Không thể lấy JWT token hợp lệ từ bất kỳ bot nào trong danh sách REGION_ACCOUNTS['VN'].")


def get_api_endpoint(region="VN"):
    endpoints = {
        "VN": "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow",
    }
    return endpoints.get(region, endpoints["VN"])


def encrypt_aes(hex_data, key, iv):
    key_bytes = key.encode("utf-8")
    if len(key_bytes) < 16:
        key_bytes = key_bytes.ljust(16, b"\0")
    else:
        key_bytes = key_bytes[:16]

    iv_bytes = iv.encode("utf-8")
    if len(iv_bytes) < 16:
        iv_bytes = iv_bytes.ljust(16, b"\0")
    else:
        iv_bytes = iv_bytes[:16]

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_data = pad(bytes.fromhex(hex_data), AES.block_size)
    return binascii.hexlify(cipher.encrypt(padded_data)).decode()


def make_headers(token):
    return {
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-Ga-Sv": "1789534056",
        "Authorization": f"Bearer {normalize_token(token)}",
        "X-Ga": "v1 1",
        "Releaseversion": RELEASE_VERSION,
        "Content-Type": "application/octet-stream",
        "X-Unity-Version": "2018.4.12f1",
        "PlAy_VeR": "1.132.1",
        "Ob_VeR": RELEASE_VERSION
    }



def apis(encrypted_hex, region="VN", override_token=None):
    region = (region or "VN").upper()
    endpoint = get_api_endpoint(region)

    if override_token:
        headers = make_headers(override_token)
        response = http_session.post(
            endpoint,
            headers=headers,
            data=bytes.fromhex(encrypted_hex),
            timeout=8
        )
        response.raise_for_status()
        return response.content.hex()

    accounts_count = len(REGION_ACCOUNTS.get("VN", []))
    max_retries = max(accounts_count, 2)

    for attempt in range(max_retries):
        token = get_next_bot_token()
        headers = make_headers(token)
        try:
            response = http_session.post(
                endpoint,
                headers=headers,
                data=bytes.fromhex(encrypted_hex),
                timeout=8
            )
            if response.status_code in [401, 429]:
                logger.warning("[VN] Token gặp status %s, tự động chuyển sang bot tiếp theo (lần %d/%d)...", response.status_code, attempt + 1, max_retries)
                continue
            response.raise_for_status()
            return response.content.hex()
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
    raise Exception(f"API request failed for region {region} after {max_retries} bot attempts")


def add_metadata(result, start_time):
    if not isinstance(result, dict):
        return result
    result["Developer"] = "vtloveem"
    result["Telegram"] = "@vtloveem"
    result["Discord"] = "vtloveem.xyz"
    result["Time_Spent"] = f"{time.time() - start_time:.2f}s"
    result["Time"] = get_formatted_time()
    return result


# ============================================================
# Routes
# ============================================================

@app.route("/", methods=["GET"])
def home():
    return """<!DOCTYPE html><html><body><h3>Free Fire VN API Running (OB55)</h3></body></html>"""


@app.route("/info", methods=["GET"])
def get_player_info():
    start_time = time.time()
    try:
        uid = request.args.get("uid")
        region = request.args.get("region", "VN").upper()
        custom_key = request.args.get("key", DEFAULT_KEY)
        custom_iv = request.args.get("iv", DEFAULT_IV)
        custom_token = request.args.get("token")

        if not uid:
            return jsonify({"error": "UID parameter is required"}), 400
        try:
            uid_int = int(uid)
        except ValueError:
            return jsonify({"error": "Invalid UID format"}), 400

        message = uid_generator_pb2.uid_generator()
        message.saturn_ = uid_int
        message.garena = 1
        protobuf_data = message.SerializeToString()
        hex_data = binascii.hexlify(protobuf_data).decode()

        encrypted_hex = encrypt_aes(hex_data, custom_key, custom_iv)
        api_response = apis(encrypted_hex, region, override_token=custom_token)

        if not api_response:
            return jsonify({"error": "Empty response from API"}), 502

        message = AccountPersonalShowInfo()
        message.ParseFromString(bytes.fromhex(api_response))
        result = proto_to_dict(message)
        add_metadata(result, start_time)

        return jsonify(result), 200

    except requests.exceptions.HTTPError as he:
        if he.response is not None and "BR_ACCOUNT_NOT_FOUND" in he.response.text:
            return jsonify({
                "error": "Tài khoản không tồn tại trên máy chủ Free Fire VN (BR_ACCOUNT_NOT_FOUND). Hãy kiểm tra lại UID hoặc Account ID."
            }), 404
        logger.exception("[INFO HTTP ERROR] %s", he)
        return jsonify({"error": str(he)}), 500
    except Exception as e:
        logger.exception("[INFO ERROR] %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/favicon.ico")
def favicon():
    return "", 404


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Free Fire Player Info API",
        "time": get_iso_time()
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "1080")),
        threaded=True
    )
