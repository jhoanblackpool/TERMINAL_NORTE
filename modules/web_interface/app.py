# -*- coding: utf-8 -*-
"""
Centro de Ejecucion de Robots - Versión Corregida
Interfaz web con Eel para gestionar agentes de automatizacion
"""
import eel
import time
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import random

# Configurar encoding
sys.stdout.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('robot_center.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Inicializar Eel
eel.init('web')

# Configuración de la aplicación
CONFIG = {
    "puerto": 8080,
    "modo_debug": False,
    "timeout_ejecucion": 30,
    "max_intentos_ejecucion": 3
}

# Datos de ejemplo de los agentes
agentes_data = [
    {
        "id": 1,
        "nombre": "Agente Contable",
        "area": "Finanzas",
        "estado": "Activo",
        "descripcion": "Envio automatico de facturas y recordatorios.",
        "color_estado": "success",
        "version": "2.1.0",
        "autor": "Sistema"
    },
    {
        "id": 2,
        "nombre": "Agente Compras", 
        "area": "Operaciones",
        "estado": "Activo",
        "descripcion": "Descarga de ordenes y conciliacion con proveedores.",
        "color_estado": "success",
        "version": "1.8.3",
        "autor": "Sistema"
    },
    {
        "id": 3,
        "nombre": "Agente Soporte",
        "area": "CX", 
        "estado": "En mantenimiento",
        "descripcion": "Clasificacion de tickets y respuestas sugeridas.",
        "color_estado": "warning",
        "version": "1.5.2",
        "autor": "Sistema"
    },
    {
        "id": 4,
        "nombre": "Agente Logistica",
        "area": "Operaciones",
        "estado": "Activo",
        "descripcion": "Descarga de guias y alertas de entrega.",
        "color_estado": "success",
        "version": "2.0.1",
        "autor": "Sistema"
    },
    {
        "id": 5,
        "nombre": "Agente Recaudo",
        "area": "Finanzas",
        "estado": "Inactivo", 
        "descripcion": "Notificacion de pagos y conciliacion bancaria.",
        "color_estado": "error",
        "version": "1.9.0",
        "autor": "Sistema"
    },
    {
        "id": 6,
        "nombre": "Agente Legal",
        "area": "Backoffice",
        "estado": "Activo",
        "descripcion": "Validacion documental y seguimiento de contratos.",
        "color_estado": "success",
        "version": "1.7.4",
        "autor": "Sistema"
    }
]

def validar_string(valor: Any, max_length: int = 100) -> str:
    """Valida y limpia strings de entrada"""
    if not isinstance(valor, str):
        return ""
    return valor.strip()[:max_length]

def validar_id(valor: Any) -> bool:
    """Valida que un ID sea válido"""
    try:
        id_val = int(valor)
        return id_val > 0
    except (ValueError, TypeError):
        return False

@eel.expose
def obtener_agentes() -> List[Dict]:
    """Retorna la lista de agentes"""
    try:
        logger.info("Solicitud de lista de agentes")
        return agentes_data
    except Exception as e:
        logger.error(f"Error al obtener agentes: {e}")
        return []

@eel.expose
def filtrar_agentes(termino_busqueda: str = "", area: str = "Todos", estado: str = "Todos") -> List[Dict]:
    """Filtra agentes segun los criterios especificados"""
    try:
        logger.info(f"Filtrando agentes: busqueda='{termino_busqueda}', area='{area}', estado='{estado}'")
        
        # Validar y limpiar entrada
        termino_busqueda = validar_string(termino_busqueda, 50).lower()
        area = validar_string(area, 50)
        estado = validar_string(estado, 50)
        
        agentes_filtrados = agentes_data.copy()
        
        # Filtrar por termino de busqueda
        if termino_busqueda:
            agentes_filtrados = [
                agente for agente in agentes_filtrados 
                if termino_busqueda in agente["nombre"].lower() or 
                   termino_busqueda in agente["descripcion"].lower() or
                   termino_busqueda in agente["area"].lower()
            ]
        
        # Filtrar por area
        if area and area != "Todos":
            agentes_filtrados = [
                agente for agente in agentes_filtrados 
                if agente["area"] == area
            ]
        
        # Filtrar por estado  
        if estado and estado != "Todos":
            agentes_filtrados = [
                agente for agente in agentes_filtrados 
                if agente["estado"] == estado
            ]
        
        logger.info(f"Filtros aplicados: {len(agentes_filtrados)} agentes encontrados")
        return agentes_filtrados
        
    except Exception as e:
        logger.error(f"Error al filtrar agentes: {e}")
        return agentes_data

@eel.expose
def obtener_areas() -> List[str]:
    """Retorna las areas unicas disponibles"""
    try:
        areas = list(set([agente["area"] for agente in agentes_data if agente.get("area")]))
        return sorted(areas)
    except Exception as e:
        logger.error(f"Error al obtener areas: {e}")
        return []

@eel.expose
def obtener_estados() -> List[str]:
    """Retorna los estados unicos disponibles"""
    try:
        estados = list(set([agente["estado"] for agente in agentes_data if agente.get("estado")]))
        return sorted(estados)
    except Exception as e:
        logger.error(f"Error al obtener estados: {e}")
        return []

@eel.expose
def ejecutar_agente(agente_id: Any) -> Dict[str, Any]:
    """Ejecuta un agente especifico con validación completa"""
    try:
        # Validar entrada
        if not validar_id(agente_id):
            logger.warning(f"ID de agente inválido: {agente_id}")
            return {
                "success": False,
                "mensaje": "ID de agente inválido",
                "codigo_error": "INVALID_ID"
            }
        
        agente_id = int(agente_id)
        agente = next((a for a in agentes_data if a["id"] == agente_id), None)
        
        if not agente:
            logger.warning(f"Agente no encontrado: ID {agente_id}")
            return {
                "success": False,
                "mensaje": "Agente no encontrado",
                "codigo_error": "NOT_FOUND"
            }
        
        if agente["estado"] != "Activo":
            logger.warning(f"Intento de ejecutar agente inactivo: {agente['nombre']} ({agente['estado']})")
            return {
                "success": False,
                "mensaje": f"El agente está en estado: {agente['estado']}",
                "codigo_error": "AGENT_UNAVAILABLE"
            }
        
        # Simular ejecucion
        logger.info(f"Ejecutando agente: {agente['nombre']} (ID: {agente_id})")
        tiempo_inicio = time.time()
        
        # Simular procesamiento con posible fallo (10% probabilidad)
        time.sleep(random.uniform(0.5, 2.0))  # Tiempo de ejecución variable
        
        if random.random() < 0.1:  # 10% de fallo simulado para testing
            logger.error(f"Fallo simulado en ejecución de {agente['nombre']}")
            return {
                "success": False,
                "mensaje": "Error durante la ejecución del agente",
                "codigo_error": "EXECUTION_FAILED",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        tiempo_ejecucion = round(time.time() - tiempo_inicio, 2)
        
        logger.info(f"Agente {agente['nombre']} ejecutado exitosamente en {tiempo_ejecucion}s")
        
        return {
            "success": True,
            "mensaje": f"{agente['nombre']} ejecutado exitosamente",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duracion": f"{tiempo_ejecucion} segundos",
            "agente_id": agente_id,
            "agente_nombre": agente["nombre"]
        }
        
    except Exception as e:
        logger.error(f"Error inesperado al ejecutar agente {agente_id}: {e}")
        return {
            "success": False,
            "mensaje": "Error interno del servidor",
            "codigo_error": "INTERNAL_ERROR",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

@eel.expose
def obtener_detalles_agente(agente_id: Any) -> Optional[Dict[str, Any]]:
    """Obtiene detalles completos de un agente"""
    try:
        if not validar_id(agente_id):
            logger.warning(f"ID inválido para detalles: {agente_id}")
            return None
        
        agente_id = int(agente_id)
        agente = next((a for a in agentes_data if a["id"] == agente_id), None)
        
        if not agente:
            logger.warning(f"Agente no encontrado para detalles: ID {agente_id}")
            return None
        
        # Agregar informacion adicional para los detalles
        detalles = agente.copy()
        detalles.update({
            "ultima_ejecucion": "2024-09-12 14:30:00",
            "total_ejecuciones": random.randint(50, 500),
            "tiempo_promedio": f"{random.uniform(1.0, 5.0):.1f} segundos",
            "tasa_exito": f"{random.uniform(85.0, 99.5):.1f}%",
            "proxima_ejecucion": "2024-09-15 09:00:00",
            "dependencias": ["Sistema ERP", "Base de datos principal"],
            "logs_recientes": [
                "2024-09-12 14:30:00 - Ejecución completada exitosamente",
                "2024-09-12 10:15:00 - Ejecución completada exitosamente",
                "2024-09-11 16:45:00 - Ejecución completada exitosamente"
            ]
        })
        
        logger.info(f"Detalles obtenidos para agente: {agente['nombre']}")
        return detalles
        
    except Exception as e:
        logger.error(f"Error al obtener detalles del agente {agente_id}: {e}")
        return None

@eel.expose
def obtener_estadisticas_sistema() -> Dict[str, Any]:
    """Obtiene estadísticas generales del sistema"""
    try:
        total_agentes = len(agentes_data)
        agentes_activos = len([a for a in agentes_data if a["estado"] == "Activo"])
        agentes_mantenimiento = len([a for a in agentes_data if a["estado"] == "En mantenimiento"])
        agentes_inactivos = len([a for a in agentes_data if a["estado"] == "Inactivo"])
        
        return {
            "total_agentes": total_agentes,
            "agentes_activos": agentes_activos,
            "agentes_mantenimiento": agentes_mantenimiento,
            "agentes_inactivos": agentes_inactivos,
            "uptime_sistema": "48 días, 12 horas",
            "version_sistema": "2.1.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return {}

def cargar_configuracion() -> Dict[str, Any]:
    """Carga configuración desde archivo"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info("Configuración cargada desde archivo")
            return {**CONFIG, **config}
    except FileNotFoundError:
        logger.info("Archivo de configuración no encontrado, usando valores por defecto")
        return CONFIG
    except Exception as e:
        logger.error(f"Error al cargar configuración: {e}")
        return CONFIG

def main():
    """Funcion principal para iniciar la aplicacion"""
    try:
        # Cargar configuración
        config = cargar_configuracion()
        
        print("=" * 60)
        print("🤖 CENTRO DE EJECUCIÓN DE ROBOTS")
        print("=" * 60)
        print(f"📊 Agentes disponibles: {len(agentes_data)}")
        print(f"🌐 Puerto: {config['puerto']}")
        print(f"🔧 Modo debug: {'Activado' if config['modo_debug'] else 'Desactivado'}")
        print("=" * 60)
        print("🚀 Iniciando servidor...")
        print(f"💻 Servidor disponible en: http://localhost:{config['puerto']}")
        print("⏹️  Presiona Ctrl+C para detener")
        print("=" * 60)
        
        logger.info("Iniciando Centro de Ejecución de Robots")
        
        # Iniciar la aplicacion web
        eel.start('index.html', 
                 size=(1400, 900),
                 port=config['puerto'],
                 mode='chrome',
                 host='localhost',
                 debug=config['modo_debug'])
                 
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        logger.info("Servidor detenido por el usuario")
        
    except Exception as e:
        print(f"❌ Error al iniciar la aplicacion: {e}")
        logger.error(f"Error al iniciar aplicación: {e}")
        
        print("🔄 Intentando con modo por defecto...")
        try:
            # Fallback a modo por defecto si Chrome no esta disponible
            eel.start('index.html', 
                     size=(1400, 900),
                     port=config['puerto'])
        except Exception as e2:
            print(f"❌ Error en modo fallback: {e2}")
            logger.error(f"Error en modo fallback: {e2}")
            print("\n🔍 Verifica que:")
            print("   1. La carpeta 'web' existe")
            print("   2. El archivo 'web/index.html' existe")
            print(f"   3. El puerto {config['puerto']} no esté en uso")
            print("   4. Chrome esté instalado (para modo normal)")

if __name__ == '__main__':
    main()