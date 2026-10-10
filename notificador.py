"""Notificador de sismos: menú interactivo que publica eventos en el exchange fanout 'sismos'."""
import json, logging, time
from datetime import datetime, timezone
from pathlib import Path
import pika
from config import config_reader  # lee Tarea1/config/config.ini
from logs import configurar_logs

ARCHIVO_SISMOS = Path(__file__).parent / "sismos.json"
EXCHANGE = "sismos"

configurar_logs()  # timestamp y componente con color (ver logs.py)
log = logging.getLogger("notificador")


def leer_sismos():
    """Lee el catálogo cada vez, para incluir los sismos personalizados recién agregados."""
    return json.loads(ARCHIVO_SISMOS.read_text(encoding="utf-8"))


def publicar(sismos):
    """Abre una conexión por envío: mientras el menú espera input() no hay heartbeats y el broker la cerraría."""
    conexion = pika.BlockingConnection(pika.URLParameters(config_reader.amqp_connection_string()))
    canal = conexion.channel()
    canal.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
    for sismo in sismos:
        # Event notification: qué ocurrió (id), dónde (lat/lon, para filtrar por distancia) y cuándo (UTC)
        evento = json.dumps({"id": sismo["id"], "lat": sismo["latitud"], "lon": sismo["longitud"], "fecha_utc": sismo["fecha_utc"]})
        canal.basic_publish(exchange=EXCHANGE, routing_key="", body=evento)
        log.info("publicado %s", evento)
        time.sleep(1)  # pausa para que los logs de cada envío se lean en orden
    conexion.close()


def elegir_uno():
    sismos = leer_sismos()
    for i, sismo in enumerate(sismos, 1):
        print(f"  {i}. M{sismo['magnitud']}  {sismo['fecha_utc']} UTC  {sismo['referencia']}")
    indice = int(input("Número de sismo: ")) - 1
    if not 0 <= indice < len(sismos):  # evita que 0 o negativos tomen sismos desde el final
        raise IndexError
    return [sismos[indice]]


def crear_personalizado():
    """Pide los datos, asigna el siguiente id y la fecha actual, y lo agrega (append) al final de sismos.json."""
    sismos = leer_sismos()
    ahora, ahora_utc = datetime.now(), datetime.now(timezone.utc)
    sismo = {
        "id": max(s["id"] for s in sismos) + 1,  # id incremental: 1, 2, 3...
        "fecha_local": f"{ahora:%Y-%m-%d %H:%M:%S}",
        "fecha_utc": f"{ahora_utc:%Y-%m-%d %H:%M:%S}",
        "latitud": float(input("Latitud: ")),
        "longitud": float(input("Longitud: ")),
        "profundidad_km": float(input("Profundidad (km): ")),
        "magnitud": float(input("Magnitud: ")),
        "tipo_magnitud": "Ml",
        "referencia": input("Referencia: "),
        "agencia": "CSN",
    }
    sismos.append(sismo)
    lineas = ",\n".join("  " + json.dumps(s, ensure_ascii=False) for s in sismos)  # un sismo por línea
    ARCHIVO_SISMOS.write_text(f"[\n{lineas}\n]\n", encoding="utf-8")
    log.info("sismo %s agregado a %s", sismo["id"], ARCHIVO_SISMOS.name)
    return [sismo]


OPCIONES = {
    "1": ("Enviar todos secuencialmente", leer_sismos),
    "2": ("Enviar uno en particular", elegir_uno),
    "3": ("Crear sismo personalizado y enviarlo", crear_personalizado),
}

while True:
    print("\n" + "\n".join(f"{tecla}. {texto}" for tecla, (texto, _) in OPCIONES.items()) + "\n0. Salir")
    opcion = input("> ").strip()
    if opcion == "0":
        break
    if opcion not in OPCIONES:
        print("Opción inválida")
        continue
    try:
        publicar(OPCIONES[opcion][1]())
    except (ValueError, IndexError):  # número, índice o coordenada mal ingresados
        log.warning("entrada inválida, no se publicó nada")
