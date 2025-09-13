import os
import logging
from modules.pdf_processor.pdf_processor import PDFProcessor

# --- Configuración del Logging ---
# Esto nos permite ver en la terminal qué está haciendo el programa.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Muestra los logs en la consola
    ]
)

def main():
    """
    Punto de entrada principal para ejecutar el robot de procesamiento de facturas.
    """
    logging.info("=================================================")
    logging.info("=  INICIANDO ROBOT DE PROCESAMIENTO DE FACTURAS  =")
    logging.info("=================================================")

    # La ruta base es el directorio donde se encuentra este script.
    # Usamos esto para que el programa siempre sepa dónde está, sin importar desde dónde lo llames.
    base_path = os.path.dirname(os.path.abspath(__file__))

    try:
        # 1. Creamos una instancia del procesador principal.
        # Le pasamos la ruta base para que pueda encontrar las carpetas
        # 'facturas_por_procesar', 'facturas_procesadas', etc.
        processor = PDFProcessor(base_path=base_path)

        # 2. Llamamos al método para procesar un lote de archivos.
        # Este método buscará automáticamente los PDFs en la carpeta de entrada.
        # `mostrar_progreso=True` activará una barra de progreso en la terminal.
        resumen = processor.procesar_lote(mostrar_progreso=True)

        # 3. Imprimimos un resumen final del proceso.
        logging.info("----------------- RESUMEN DEL PROCESO -----------------")
        stats = resumen.get('estadisticas', {})
        logging.info(f"Archivos totales procesados: {stats.get('total_archivos', 0)}")
        logging.info(f"Procesados con éxito: {stats.get('archivos_exitosos', 0)}")
        logging.info(f"Procesados con error: {stats.get('archivos_con_error', 0)}")
        total_time = stats.get('tiempo_total_segundos', 0)
        logging.info(f"Tiempo total de ejecución: {total_time:.2f} segundos.")
        logging.info("-------------------------------------------------------")

        if stats.get('archivos_con_error', 0) > 0:
            logging.warning("Algunos archivos no se pudieron procesar. Revisa la carpeta 'facturas_con_error'.")

    except Exception as e:
        logging.error(f"Ocurrió un error fatal durante la ejecución: {e}", exc_info=True)
        logging.info("El programa se ha detenido debido a un error crítico.")

    logging.info("=================================================")
    logging.info("=          PROCESO FINALIZADO                   =")
    logging.info("=================================================")


if __name__ == "__main__":
    # Esta es la línea que hace que la función `main()` se ejecute
    # solo cuando corres el script directamente con `python main.py`.
    main()
