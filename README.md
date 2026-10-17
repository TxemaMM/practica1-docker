# Ranking de videojuegos · Docker multientorno

Aplicación web donde los usuarios se registran, añaden videojuegos y votan. Muestra un Top 5 y un panel que indica en tiempo real si la base de datos y la caché están disponibles. Se despliega con Docker Compose en dos entornos: desarrollo y producción.

## Tecnologías

- **Docker y Docker Compose**: contenedores y orquestación
- **Python 3.12 + Flask + gunicorn**: aplicación web
- **PostgreSQL**: base de datos (con volumen persistente)
- **Redis**: caché del Top 5 (solo en producción)
- **Make**: atajos para todos los comandos del proyecto

## Requisitos

Para usar el proyecto hay que tener instalado:

- **Docker Engine** con el plugin **Docker Compose v2** (`docker compose version`)
- **make**
- **git**
- **curl** (lo usa `make status` y el script de usuarios de prueba)

## Arquitectura

```text
 Navegador ──► puerto publicado (8080 dev / 8081 prod)
                        │
                 ┌──────▼──────┐
                 │     app     │  Flask + gunicorn
                 └──┬───────┬──┘
   red backend      │       │      (internal: sin salida al exterior)
   ┌────────────────▼─┐   ┌─▼───────────────┐
   │  db (PostgreSQL) │   │ cache (Redis)   │  ← solo en prod
   │  volumen pgdata  │   └─────────────────┘
   └──────────────────┘
```

- **Tres servicios:** `app` (web), `db` (PostgreSQL) y `cache` (Redis, solo en producción).
- **Dos redes:** `frontend` (la app, con el puerto publicado) y `backend`, de tipo `internal`, donde viven `db` y `cache`. Solo `app` es accesible desde fuera.
- **Dos entornos independientes** que pueden funcionar a la vez: desarrollo (`docker-compose.dev.yml`, puerto 8080, sin caché) y producción (`docker-compose.prod.yml`, puerto 8081, con caché).
- **Persistencia:** el volumen `pgdata` conserva los datos aunque se eliminen los contenedores.
- **Inicialización automática:** `db/init.sql` crea las tablas y carga los juegos la primera vez que arranca la base de datos.

## Puesta en marcha

**1. Clonar el repositorio**

```bash
git clone https://github.com/TxemaMM/practica1-docker.git
cd practica1-docker
```

**2  Levantar todo desde cero**

```bash
make up
```

Construye la imagen y arranca los dos entornos. La primera vez tarda más porque descarga las imágenes.

- Desarrollo: <http://localhost:8080>
- Producción: <http://localhost:8081>

**Solo un entorno**

```bash
make up-dev     # solo desarrollo
make up-prod    # solo producción
```

**Comprobar que funciona**

```bash
make status
```

Consulta el estado de cada entorno. Los servicios tardan unos segundos en estar listos (`healthy`).

**Usuarios de prueba (opcional)**

Crea `hola1` … `hola10` con la contraseña que se indique:

```bash
make seed-dev PASS=<contraseña>
make seed-prod PASS=<contraseña>
```

**Resto de comandos**

```bash
make help
```

Lista todos los comandos disponibles: parar, ver logs, simular fallos, reiniciar desde cero, etc.



## Uso de inteligencia artificial

**Herramienta:** Claude (Anthropic), modelo Claude Sonnet 5.5.

He usado la IA como guía a lo largo de toda la práctica, a modo de tutor. Le pedí que me fuera llevando paso a paso y que me explicara cada comando y cada línea de código, y no que me diera todo hecho de golpe. Los archivos los he escrito yo a mano, y las pruebas las he ejecutado y comprobado en mi propio equipo.

**En qué partes ha participado:**

- **Planificación:** la estructura del proyecto, el flujo de trabajo con Git y cómo entregar las credenciales sin subirlas a GitHub.
- **Aplicación web (Flask) y base de datos:** la IA propuso el código y la estructura de las tablas. Yo elegí la temática (videojuegos y votaciones) y decidí qué debía hacer la web.
- **Dockerfile y Docker Compose:** la IA me propuso ideas para mejorar mi base de los archivos y me explicó cada instrucción: redes, healthchecks, volúmenes, `depends_on`, `env_file` frente a `environment`. Yo escribí los archivos, los levanté y fui comprobando su comportamiento.
- **Makefile y script de usuarios de prueba:** la IA propuso los comandos. Yo los probé y los fui usando durante las pruebas.
- **README:** hecho y revisado por mi, pero para dar mas organización redactado con ayuda de la IA.

**Lo que he hecho yo:** escribir los archivos, ejecutar todos los comandos, hacer los commits y subidas a GitHub, y probar el funcionamiento (persistencia de datos, caída de la base de datos y de la caché, healthchecks).
