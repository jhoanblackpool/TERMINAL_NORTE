# -*- coding: utf-8 -*-
"""
Centro de Ejecucion de Robots
Interfaz web con Eel para gestionar agentes de automatizacion
"""
import eel
import time
from datetime import datetime

# Inicializar Eel
eel.init('web')

# Datos de ejemplo de los agentes
agentes_data = [
    {
        "id": 1,
        "nombre": "Agente Contable",
        "area": "Finanzas",
        "estado": "Activo",
        "descripcion": "Envio automatico de facturas y recordatorios.",
        "color_estado": "success"
    },
    {
        "id": 2,
        "nombre": "Agente Compras", 
        "area": "Operaciones",
        "estado": "Activo",
        "descripcion": "Descarga de ordenes y conciliacion con proveedores.",
        "color_estado": "success"
    },
    {
        "id": 3,
        "nombre": "Agente Soporte",
        "area": "CX", 
        "estado": "En mantenimiento",
        "descripcion": "Clasificacion de tickets y respuestas sugeridas.",
        "color_estado": "warning"
    },
    {
        "id": 4,
        "nombre": "Agente Logistica",
        "area": "Operaciones",
        "estado": "Activo",
        "descripcion": "Descarga de guias y alertas de entrega.",
        "color_estado": "success"
    },
    {
        "id": 5,
        "nombre": "Agente Recaudo",
        "area": "Finanzas",
        "estado": "Activo", 
        "descripcion": "Notificacion de pagos y conciliacion bancaria.",
        "color_estado": "success"
    },
    {
        "id": 6,
        "nombre": "Agente Legal",
        "area": "Backoffice",
        "estado": "Activo",
        "descripcion": "Validacion documental y seguimiento de contratos.",
        "color_estado": "success"
    }
]

@eel.expose
def obtener_agentes():
    """Retorna la lista de agentes"""
    return agentes_data

@eel.expose
def filtrar_agentes(termino_busqueda="", area="Todos", estado="Todos"):
    """Filtra agentes segun los criterios especificados"""
    agentes_filtrados = agentes_data.copy()
    
    # Filtrar por termino de busqueda
    if termino_busqueda:
        agentes_filtrados = [
            agente for agente in agentes_filtrados 
            if termino_busqueda.lower() in agente["nombre"].lower() or 
               termino_busqueda.lower() in agente["descripcion"].lower()
        ]
    
    # Filtrar por area
    if area != "Todos":
        agentes_filtrados = [
            agente for agente in agentes_filtrados 
            if agente["area"] == area
        ]
    
    # Filtrar por estado  
    if estado != "Todos":
        agentes_filtrados = [
            agente for agente in agentes_filtrados 
            if agente["estado"] == estado
        ]
    
    return agentes_filtrados

@eel.expose
def obtener_areas():
    """Retorna las areas unicas disponibles"""
    areas = list(set([agente["area"] for agente in agentes_data]))
    return sorted(areas)

@eel.expose
def obtener_estados():
    """Retorna los estados unicos disponibles"""
    estados = list(set([agente["estado"] for agente in agentes_data]))
    return sorted(estados)

@eel.expose
def ejecutar_agente(agente_id):
    """Ejecuta un agente especifico"""
    agente = next((a for a in agentes_data if a["id"] == agente_id), None)
    if agente:
        # Simular ejecucion
        print(f"Ejecutando {agente['nombre']}...")
        time.sleep(1)  # Simular procesamiento
        
        return {
            "success": True,
            "mensaje": f"{agente['nombre']} ejecutado exitosamente",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        return {
            "success": False,
            "mensaje": "Agente no encontrado"
        }

@eel.expose
def obtener_detalles_agente(agente_id):
    """Obtiene detalles completos de un agente"""
    agente = next((a for a in agentes_data if a["id"] == agente_id), None)
    if agente:
        # Agregar informacion adicional para los detalles
        detalles = agente.copy()
        detalles.update({
            "ultima_ejecucion": "2024-09-12 14:30:00",
            "total_ejecuciones": 245,
            "tiempo_promedio": "3.2 segundos",
            "tasa_exito": "98.5%"
        })
        return detalles
    return None

def main():
    """Funcion principal para iniciar la aplicacion"""
    try:
        print("=" * 50)
        print("Centro de Ejecucion de Robots")
        print("=" * 50)
        print("Iniciando servidor...")
        print("Servidor disponible en: http://localhost:8080")
        print("Presiona Ctrl+C para detener")
        print("=" * 50)
        
        # Iniciar la aplicacion web
        eel.start('index.html', 
                 size=(1400, 900),
                 port=8080,
                 mode='chrome',
                 host='localhost')
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except Exception as e:
        print(f"Error al iniciar la aplicacion: {e}")
        print("Intentando con modo por defecto...")
        try:
            # Fallback a modo por defecto si Chrome no esta disponible
            eel.start('index.html', 
                     size=(1400, 900),
                     port=8080)
        except Exception as e2:
            print(f"Error en modo fallback: {e2}")
            print("Verifica que:")
            print("1. La carpeta 'web' existe")
            print("2. El archivo 'web/index.html' existe")
            print("3. El puerto 8080 no este en uso")

if __name__ == '__main__':
    main()