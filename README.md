# INF326 — Tarea 1: Sistema de notificación de sismos

Sistema publish-subscribe con RabbitMQ (CloudAMQP) y consulta del detalle por HTTP mediante FastAPI. Cada ciudad recibe los eventos y consulta el detalle solo si el epicentro está a menos de 500 km.

## Integrante y rol

| Nombre | Rol |
| --- | --- |
| Yohanns Jara | Diseño de arquitectura, implementación del notificador, suscriptores y servicio HTTP, pruebas y elaboración del informe. |

## Instrucciones de ejecución

### Prerrequisitos

- Python 3.10 o superior y `pip`.
- Una instancia de RabbitMQ en CloudAMQP con acceso AMQPS (TLS).
- Credenciales de conexión en `config/config.ini`. Este archivo es privado y está excluido de Git.

Ejecutar los comandos desde la carpeta raíz de este repositorio, donde están `requirements.txt` y los scripts.

Preparación en Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config/config.ini.example config/config.ini
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config/config.ini.example config/config.ini
```

Completar `config/config.ini` con los datos de la instancia:

```ini
[CONNECTION]
USER_PASSWORD = usuario:clave
SERVER = host.rmq.cloudamqp.com
PORT = 5671
VHOST = vhost
```

### Comandos

Abrir tres terminales en la raíz del repositorio y activar el mismo entorno en cada una. Iniciar los componentes en este orden:

| Terminal | Comando | Función |
| --- | --- | --- |
| 1 | `python -m uvicorn datos_sismos:app --host 127.0.0.1 --port 8000` | Servicio HTTP de datos. |
| 2 | `python subscriber.py` | Suscriptores de Arica, Coquimbo, Valparaíso, Concepción y Punta Arenas. |
| 3 | `python notificador.py` | Menú para publicar los sismos. |

Esperar a que los cinco suscriptores indiquen `esperando sismos...` antes de publicar. Para ejecutar una sola ciudad, usar por ejemplo `python subscriber.py "Punta Arenas"` o `python subscriber.py "Valparaíso"`.

El notificador permite enviar todos los sismos secuencialmente, elegir uno del catálogo o crear y guardar un sismo personalizado antes de publicarlo. La opción `0` termina el menú; `Ctrl+C` detiene los demás componentes.

Verificar el servicio en <http://127.0.0.1:8000/sismos>, consultar un registro en <http://127.0.0.1:8000/sismos/1> y abrir la documentación interactiva en <http://127.0.0.1:8000/docs>.

Si el servicio HTTP usa otra dirección o puerto, definir `API_URL` en la terminal del suscriptor antes de iniciarlo:

```powershell
$env:API_URL = "http://127.0.0.1:8001"
```

En Linux o macOS: `export API_URL="http://127.0.0.1:8001"`.

## Consideraciones de implementación

- El exchange `sismos` es de tipo `fanout`. Cada ciudad tiene una cola exclusiva propia y recibe una copia de cada evento; las colas se eliminan al desconectarse. Los suscriptores deben estar conectados antes de publicar.
- El evento contiene únicamente `id`, `lat`, `lon` y `fecha_utc`. Cada suscriptor calcula la distancia con Haversine (radio terrestre de 6371 km). Solo si la distancia es estrictamente menor a 500 km consulta `GET /sismos/{id}`; en otro caso registra el evento como ignorado.
- Los mensajes usan `auto_ack=True`: no hay reentrega si el procesamiento falla ni recuperación de eventos publicados mientras el suscriptor está desconectado.
- Las consultas HTTP tienen un timeout de 5 segundos. Ante un `404`, timeout o servicio no disponible se registra el error y se continúa escuchando, sin reintentos.
- `sismos.json` es un catálogo local de demostración. El servicio lo relee en cada consulta para detectar los registros agregados por el notificador. Se debe usar un solo notificador y evitar escrituras concurrentes; no hay base de datos.
- Sin argumento, las cinco ciudades comparten un proceso y una conexión, con una cola por ciudad. Ejecutarlas por separado permite aislar sus procesos. El notificador abre una conexión por envío para evitar conexiones inactivas durante el menú.
- Los logs incluyen fecha, componente y colores para distinguir eventos de interés e ignorados. El servicio HTTP no incluye autenticación ni TLS; la conexión a CloudAMQP usa TLS. Es una demostración académica, sin garantías de entrega para alertas reales.
- El informe de la tarea está incluido en [Tarea1-YohannsJara.pdf](Tarea1-YohannsJara.pdf).
