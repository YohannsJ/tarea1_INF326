"""Suscriptor de sismos por ciudad. Sin argumento levanta las 5 ciudades en un solo proceso."""
import json, logging, os, sys, unicodedata, urllib.request
from math import asin, cos, radians, sin, sqrt
import pika
from config import config_reader  # lee Tarea1/config/config.ini
from logs import configurar_logs

CIUDADES = {  # nombre normalizado -> (latitud, longitud)
    "arica":        (-18.4746, -70.29792),
    "coquimbo":     (-29.95332, -71.33947),
    "valparaiso":   (-33.036, -71.62963),
    "concepcion":   (-36.82699, -73.04977),
    "punta arenas": (-53.16282, -70.90922),
}
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
RADIO_INTERES_KM = 500
EXCHANGE = "sismos"

configurar_logs()  # timestamp y componente con color (ver logs.py)


def normalizar(texto):
    """'Valparaíso' -> 'valparaiso': minúsculas y sin tildes, para aceptar cualquier forma de escribir."""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower().strip()


def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia sobre la superficie terrestre (Haversine, radio 6371 km)."""
    a = sin(radians(lat2 - lat1) / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def pedir_detalle(id_sismo):
    """Pull: solo quien se interesa consulta el detalle completo al servicio Datos Sismos."""
    with urllib.request.urlopen(f"{API_URL}/sismos/{id_sismo}", timeout=5) as respuesta:
        return json.load(respuesta)


def crear_receptor(ciudad):
    """Devuelve el callback de una ciudad; cada ciudad loguea con su propio nombre como prefijo."""
    log = logging.getLogger(ciudad)

    def al_recibir(canal, metodo, propiedades, cuerpo):
        evento = json.loads(cuerpo)
        distancia = distancia_km(*CIUDADES[ciudad], evento["lat"], evento["lon"])
        if distancia >= RADIO_INTERES_KM:
            return log.info("sismo %s (%s UTC) ignorado (a %.0f km)", evento["id"], evento["fecha_utc"], distancia)
        # Mismo mensaje mínimo que un ignorado, pero declara interés y anuncia el pull por id
        log.info("sismo %s (%s UTC) de interés (a %.0f km): fetch GET /sismos/%s", evento["id"], evento["fecha_utc"], distancia, evento["id"])
        try:
            log.info("sismo %s detalle recibido: %s", evento["id"], pedir_detalle(evento["id"]))
        except OSError as error:  # 404, timeout o servicio caído: se informa sin detener al suscriptor
            log.warning("sismo %s detalle no disponible (%s)", evento["id"], error)

    return al_recibir


ciudad_pedida = normalizar(" ".join(sys.argv[1:]))
if ciudad_pedida and ciudad_pedida not in CIUDADES:
    sys.exit(f"Uso: subscriber.py [{' | '.join(CIUDADES)}]")
ciudades = [ciudad_pedida] if ciudad_pedida else list(CIUDADES)

conexion = pika.BlockingConnection(pika.URLParameters(config_reader.amqp_connection_string()))
canal = conexion.channel()
canal.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
for ciudad in ciudades:
    # Una cola exclusiva por ciudad: cada una recibe su propia copia del evento (fanout)
    cola = canal.queue_declare(queue="", exclusive=True).method.queue
    canal.queue_bind(exchange=EXCHANGE, queue=cola)
    canal.basic_consume(queue=cola, on_message_callback=crear_receptor(ciudad), auto_ack=True)
    logging.getLogger(ciudad).info("esperando sismos...")
canal.start_consuming()
