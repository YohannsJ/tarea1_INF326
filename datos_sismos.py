"""Servicio HTTP Datos Sismos: entrega el detalle completo de cada sismo (fuente de verdad: sismos.json)."""
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

ARCHIVO_SISMOS = Path(__file__).parent / "sismos.json"
app = FastAPI(title="Datos de sismos")


def leer_sismos():
    """Lee el archivo en cada consulta para ver los sismos personalizados que agrega el notificador."""
    return {s["id"]: s for s in json.loads(ARCHIVO_SISMOS.read_text(encoding="utf-8"))}


@app.get("/sismos")
def listar():
    return list(leer_sismos().values())


@app.get("/sismos/{id_sismo}")
def detalle(id_sismo: int):
    sismo = leer_sismos().get(id_sismo)
    if sismo is None:
        raise HTTPException(404, f"Sismo {id_sismo} no encontrado")
    return sismo
