import os
import requests
from datetime import datetime

EMT_EMAIL = os.environ.get("EMT_EMAIL")
EMT_PASSWORD = os.environ.get("EMT_PASSWORD")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STOP_ID = "384"
ALERT_THRESHOLD_SECONDS = 300  # 5 minutos

def get_emt_token():
    url = "https://openapi.emtmadrid.es/v2/mobilitylabs/user/login/"
    headers = {
        "email": EMT_EMAIL,
        "password": EMT_PASSWORD,
        "X-ClientId": os.environ.get("EMT_CLIENT_ID"),
        "passKey": os.environ.get("EMT_PASSKEY")
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == "00":
            return data["data"][0]["accessToken"]
        else:
            print("Error login:", data.get("description"))
            return None
    except Exception as e:
        print("Excepción login:", e)
        return None

def get_arrivals(token):
    url = f"https://openapi.emtmadrid.es/v2/transport/busemtmad/stops/{STOP_ID}/arrives/"
    headers = {"accessToken": token}
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print("Excepción llegadas:", e)
        return []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Error Telegram:", e)

def main():
    print("--- Ejecución:", datetime.now(), "---")
    token = get_emt_token()
    if not token:
        return
    arrivals = get_arrivals(token)
    if not arrivals:
        print("Sin datos de llegadas.")
        return

    alertado = False
    for a in arrivals:
        seg = a.get("time_left", 999999)
        if seg <= ALERT_THRESHOLD_SECONDS:
            linea = a.get("line", "?")
            destino = a.get("destination", "Desconocido")
            min_ = seg // 60
            seg_ = seg % 60
            mensaje = (
                f"🚌 *¡Autobús cerca!*\n"
                f"*Parada:* {STOP_ID}\n"
                f"*Línea:* {linea} hacia {destino}\n"
                f"*Llega en:* {min_} min {seg_} s"
            )
            send_telegram(mensaje)
            print(f"Alerta enviada: línea {linea}")
            alertado = True

    if not alertado:
        print(f"Ninguna línea llega en menos de {ALERT_THRESHOLD_SECONDS // 60} minutos.")

if __name__ == "__main__":
    main()
