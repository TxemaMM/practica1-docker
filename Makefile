DEV  = docker compose --env-file .env.dev  -f docker-compose.dev.yml
PROD = docker compose --env-file .env.prod -f docker-compose.prod.yml

.PHONY: help up down up-dev up-prod down-dev down-prod ps status logs-dev logs-prod stop-db-dev start-db-dev stop-db-prod start-db-prod stop-cache start-cache stop-app-dev start-app-dev stop-app-prod start-app-prod stop-deps-prod start-deps-prod fresh-dev fresh-prod clean-dev clean-prod seed-dev seed-prod

help:
	@echo "ENTORNOS"
	@echo "  make up / down            Levanta / para dev y prod (conserva datos)"
	@echo "  make up-dev / up-prod     Levanta solo uno (8080 / 8081)"
	@echo "  make down-dev / down-prod Para solo uno"
	@echo "  make ps                   Estado de los contenedores"
	@echo "  make status               Respuesta de /status (JSON + codigo HTTP)"
	@echo "  make logs-dev / logs-prod Logs en directo"
	@echo ""
	@echo "PRUEBAS DE CAIDA (quitar y volver a poner servicios)"
	@echo "  make stop-db-dev   / start-db-dev     Base de datos de dev"
	@echo "  make stop-db-prod  / start-db-prod    Base de datos de prod"
	@echo "  make stop-cache    / start-cache      Redis (solo prod)"
	@echo "  make stop-app-dev  / start-app-dev    Web de dev"
	@echo "  make stop-app-prod / start-app-prod   Web de prod"
	@echo "  make stop-deps-prod / start-deps-prod BD + Redis a la vez (prod)"
	@echo ""
	@echo "DESDE CERO / LIMPIEZA (piden confirmacion)"
	@echo "  make fresh-dev / fresh-prod   Recrea el entorno sin datos ni cache"
	@echo "  make clean-dev / clean-prod   Borra solo los datos"
	@echo ""
	@echo "AÑADIR 10 USUARIOS SIMULTANEAMENTE PARA PRUEBAS"
	@echo "  make seed-prod  Crea 10 cuentas del hola1-10 con la misma contraseña para todos (tu la pones)"
	@echo "  make seed-dev Crea 10 cuentas del hola1-10 con la misma contraseña para todos (tu la pones)"

up: up-dev up-prod

down: down-dev down-prod

up-dev:
	$(DEV) up -d --build
	@echo "DEV listo en http://localhost:8080"

up-prod:
	$(PROD) up -d --build
	@echo "PROD listo en http://localhost:8081"

down-dev:
	$(DEV) down

down-prod:
	$(PROD) down

ps:
	@echo "== DEV =="
	@$(DEV) ps
	@echo "== PROD =="
	@$(PROD) ps

status:
	@echo "DEV : $$(curl -s -w ' (HTTP %{http_code})' http://localhost:8080/status)"
	@echo "PROD: $$(curl -s -w ' (HTTP %{http_code})' http://localhost:8081/status)"

logs-dev:
	$(DEV) logs -f

logs-prod:
	$(PROD) logs -f

stop-db-dev:
	$(DEV) stop db

start-db-dev:
	$(DEV) start db

stop-db-prod:
	$(PROD) stop db

start-db-prod:
	$(PROD) start db

stop-cache:
	$(PROD) stop cache

start-cache:
	$(PROD) start cache

stop-app-dev:
	$(DEV) stop app

start-app-dev:
	$(DEV) start app

stop-app-prod:
	$(PROD) stop app

start-app-prod:
	$(PROD) start app

stop-deps-prod:
	$(PROD) stop db cache

start-deps-prod:
	$(PROD) start db cache

fresh-dev:
	@read -p "Esto BORRA datos e imagenes de DEV y lo reconstruye. Seguro? (s/N) " ans; [ "$$ans" = "s" ]
	$(DEV) down -v --rmi local
	$(DEV) build --no-cache
	$(DEV) up -d
	@echo "DEV recreado de cero en http://localhost:8080"

fresh-prod:
	@read -p "Esto BORRA datos e imagenes de PROD y lo reconstruye. Seguro? (s/N) " ans; [ "$$ans" = "s" ]
	$(PROD) down -v --rmi local
	$(PROD) build --no-cache
	$(PROD) up -d
	@echo "PROD recreado de cero en http://localhost:8081"

clean-dev:
	@read -p "Esto BORRA los datos de DEV. Seguro? (s/N) " ans; [ "$$ans" = "s" ]
	$(DEV) down -v

clean-prod:
	@read -p "Esto BORRA los datos de PROD. Seguro? (s/N) " ans; [ "$$ans" = "s" ]
	$(PROD) down -v

seed-dev:
	@test -n "$(PASS)" || (echo "Uso: make seed-dev PASS=contraseña"; exit 1)
	@SEED_PASSWORD="$(PASS)" ./scripts/seed_users.sh 8080

seed-prod:
	@test -n "$(PASS)" || (echo "Uso: make seed-prod PASS=contraseña"; exit 1)
	@SEED_PASSWORD="$(PASS)" ./scripts/seed_users.sh 8081