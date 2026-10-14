DEV  = docker compose --env-file .env.dev  -f docker-compose.dev.yml
PROD = docker compose --env-file .env.prod -f docker-compose.prod.yml

.PHONY: help up-dev up-prod down-dev down-prod ps logs-dev logs-prod status clean-dev clean-prod

help:
	@echo "Comandos disponibles:"
	@echo "  make up-dev      Levanta el entorno de desarrollo (puerto 8080)"
	@echo "  make up-prod     Levanta el entorno de produccion (puerto 8081)"
	@echo "  make down-dev    Para y elimina los contenedores de dev (conserva los datos)"
	@echo "  make down-prod   Para y elimina los contenedores de prod (conserva los datos)"
	@echo "  make ps          Estado de los dos entornos"
	@echo "  make status      Consulta /status de la web en dev y prod"
	@echo "  make logs-dev    Logs de dev en directo"
	@echo "  make logs-prod   Logs de prod en directo"
	@echo "  make clean-dev   BORRA los datos de dev (pide confirmacion)"
	@echo "  make clean-prod  BORRA los datos de prod (pide confirmacion)"

up-dev:
	$(DEV) up -d --build

up-prod:
	$(PROD) up -d --build

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
	@echo "DEV:  $$(curl -s http://localhost:8080/status)"
	@echo "PROD: $$(curl -s http://localhost:8081/status)"

logs-dev:
	$(DEV) logs -f

logs-prod:
	$(PROD) logs -f

clean-dev:
	@read -p "Esto BORRA los datos de DEV. Seguro? (s/N) " ans; [ "$$ans" = "s" ]
	$(DEV) down -v

clean-prod:
	@read -p "Esto BORRA los datos de PROD. Seguro? (s/N) " ans; [ "$$ans" = "s" ]
	$(PROD) down -v