"""Logs con color en consola: timestamp gris, cada componente con su color, 'ignorado' en rojo y 'de interés' en verde."""
import logging, os

os.system("")  # activa los códigos de color ANSI en la consola de Windows

GRIS, ROJO, VERDE, NEGRITA, RESET = "\033[90m", "\033[91m", "\033[92m", "\033[1m", "\033[0m"
COLOR_COMPONENTE = {  # rojo y verde quedan reservados para la decisión de interés
    "arica":        "\033[93m",  # amarillo
    "coquimbo":     "\033[94m",  # azul
    "valparaiso":   "\033[95m",  # magenta
    "concepcion":   "\033[96m",  # cian
    "punta arenas": "\033[34m",  # azul estandar
    "notificador":  NEGRITA,
}


class FormatoColor(logging.Formatter):
    """Arma cada línea como: <timestamp> [componente] mensaje, coloreando cada parte."""

    def format(self, registro):
        mensaje = (registro.getMessage()
                   .replace("ignorado", f"{ROJO}ignorado{RESET}")
                   .replace("de interés", f"{VERDE}de interés{RESET}"))
        color = COLOR_COMPONENTE.get(registro.name, "")
        return f"{GRIS}{self.formatTime(registro)}{RESET} {color}[{registro.name}]{RESET} {mensaje}"


def configurar_logs():
    """Instala el formato con color en el logger raíz; todos los logger.getLogger(nombre) lo heredan."""
    salida = logging.StreamHandler()
    salida.setFormatter(FormatoColor())
    logging.basicConfig(level=logging.INFO, handlers=[salida])
    logging.getLogger("pika").setLevel(logging.WARNING)  # oculta el ruido interno de pika
