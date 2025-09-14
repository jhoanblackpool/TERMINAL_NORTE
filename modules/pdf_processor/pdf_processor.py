"""
Módulo principal del procesador de PDFs
Integra todos los componentes para el procesamiento completo de facturas
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from tqdm import tqdm
import json

# Importar los módulos del procesador
from .pdf_analyzer import PDFAnalyzer
from .data_extractor import DataExtractor, DatosFactura, PatronExtraccion
from .file_manager import FileManager
from .validator import PDFValidator

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Procesador principal de archivos PDF de facturas
    Orquesta todos los componentes del sistema
    """
    
    def __init__(self, base_path: str, config: Dict[str, Any] = None):
        """
        Inicializa el procesador de PDFs
        
        Args:
            base_path: Ruta base del sistema
            config: Configuración personalizada
        """
        self.base_path = Path(base_path)
        self.config = config or {}
        
        # Inicializar componentes
        self.file_manager = FileManager(base_path, self.config.get('file_manager', {}))
        self.data_extractor = DataExtractor(
            patrones_cliente=self.config.get('patrones_cliente'),
            patrones_local=self.config.get('patrones_local'),
            patrones_adicionales=self.config.get('patrones_adicionales')
        )
        self.validator = PDFValidator(self.config.get('validator', {}))
        
        # Estadísticas del procesamiento
        self.estadisticas = {
            'archivos_procesados': 0,
            'paginas_procesadas': 0,
            'archivos_exitosos': 0,
            'archivos_con_error': 0,
            'tiempo_inicio': None,
            'tiempo_fin': None,
            'errores': []
        }
        
        # Configuración de procesamiento
        self.crear_backup = self.config.get('crear_backup', True)
        self.validar_antes = self.config.get('validar_antes_procesar', True)
        self.guardar_metadata = self.config.get('guardar_metadata', True)
        self.eliminar_originales = self.config.get('eliminar_originales', True)
        
        logger.info(f"PDFProcessor inicializado en: {base_path}")
    
    def procesar_archivo(self, filepath: str) -> Dict[str, Any]:
        """
        Procesa un archivo PDF completo
        
        Args:
            filepath: Ruta al archivo PDF
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        resultado = {
            'archivo': filepath,
            'exitoso': False,
            'paginas_procesadas': 0,
            'archivos_generados': [],
            'errores': [],
            'advertencias': [],
            'tiempo_procesamiento': 0,
            'metadata': {}
        }
        
        inicio = datetime.now()
        filepath = Path(filepath)
        
        try:
            logger.info(f"Iniciando procesamiento de: {filepath.name}")
            
            # 1. Validar archivo antes de procesar
            if self.validar_antes:
                validacion = self.validator.validar_archivo_pdf(str(filepath))
                
                if not validacion['es_valido']:
                    resultado['errores'] = validacion['errores']
                    resultado['advertencias'] = validacion['advertencias']
                    logger.error(f"Archivo inválido: {filepath.name}")
                    
                    # Mover a carpeta de errores
                    destino_error = self.file_manager.folders['errors'] / filepath.name
                    self.file_manager.mover_archivo(str(filepath), str(destino_error))
                    return resultado
                
                resultado['metadata']['validacion'] = validacion
            
            # 2. Crear backup si está configurado
            if self.crear_backup:
                backup_path = self.file_manager.crear_backup(str(filepath))
                if backup_path:
                    resultado['metadata']['backup'] = backup_path
                    logger.info(f"Backup creado: {backup_path}")
                else:
                    resultado['advertencias'].append("No se pudo crear backup")
            
            # 3. Analizar el PDF
            analyzer = PDFAnalyzer(str(filepath))
            pdf_metadata = analyzer.get_metadata()
            resultado['metadata']['pdf_info'] = pdf_metadata
            
            total_paginas = pdf_metadata['total_pages']
            logger.info(f"PDF con {total_paginas} páginas")
            
            # 4. Procesar cada página
            carpeta_temp = self.file_manager.folders['temp'] / f"proceso_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            carpeta_temp.mkdir(parents=True, exist_ok=True)
            
            for num_pagina in range(total_paginas):
                try:
                    logger.debug(f"Procesando página {num_pagina + 1} de {total_paginas}")
                    
                    # Extraer texto de la página
                    texto_pagina = analyzer.extract_page_text(num_pagina)
                    
                    if not texto_pagina:
                        resultado['advertencias'].append(f"No se pudo extraer texto de página {num_pagina + 1}")
                        continue
                    
                    # Extraer datos de la factura
                    datos_factura = self.data_extractor.extraer_datos_completos(texto_pagina, num_pagina + 1)
                    
                    # Validar datos extraídos
                    validacion_datos = self.data_extractor.validar_extraccion(datos_factura)
                    
                    if not datos_factura.es_valido():
                        resultado['errores'].append(f"Página {num_pagina + 1}: {', '.join(datos_factura.errores_extraccion)}")
                        continue
                    
                    # Generar nombre para el archivo
                    nombre_archivo = self.file_manager.generar_nombre_factura(
                        cliente=datos_factura.cliente,
                        local=datos_factura.local,
                        numero_factura=datos_factura.numero_factura,
                        fecha=datos_factura.fecha
                    )
                    
                    # Crear PDF individual para esta página
                    archivo_temp = carpeta_temp / f"temp_pagina_{num_pagina}.pdf"
                    if analyzer.split_page(num_pagina, str(archivo_temp)):
                        
                        # Determinar carpeta destino
                        if datos_factura.es_valido():
                            carpeta_destino = self.file_manager.folders['output']
                        else:
                            carpeta_destino = self.file_manager.folders['errors']
                        
                        archivo_final = carpeta_destino / nombre_archivo
                        
                        # Mover archivo a destino final
                        if self.file_manager.mover_archivo(str(archivo_temp), str(archivo_final)):
                            resultado['archivos_generados'].append(str(archivo_final))
                            resultado['paginas_procesadas'] += 1
                            
                            # Guardar metadata si está configurado
                            if self.guardar_metadata:
                                metadata_pagina = {
                                    'archivo_original': filepath.name,
                                    'pagina': num_pagina + 1,
                                    'datos_extraidos': datos_factura.to_dict(),
                                    'validacion': validacion_datos,
                                    'archivo_generado': str(archivo_final)
                                }
                                self.file_manager.guardar_metadata(nombre_archivo, metadata_pagina)
                            
                            logger.info(f"Página {num_pagina + 1} guardada como: {nombre_archivo}")
                        else:
                            resultado['errores'].append(f"No se pudo mover página {num_pagina + 1}")
                    else:
                        resultado['errores'].append(f"No se pudo dividir página {num_pagina + 1}")
                        
                except Exception as e:
                    logger.error(f"Error al procesar página {num_pagina + 1}: {e}")
                    resultado['errores'].append(f"Página {num_pagina + 1}: {str(e)}")
                    continue
            
            # 5. Limpiar temporales
            try:
                import shutil
                shutil.rmtree(carpeta_temp)
            except Exception as e:
                logger.warning(f"No se pudo eliminar carpeta temporal: {e}")
            
            # 6. Eliminar o mover archivo original
            if resultado['paginas_procesadas'] > 0:
                resultado['exitoso'] = True
                
                if self.eliminar_originales:
                    if not self.file_manager.eliminar_archivo(str(filepath)):
                        # Si no se puede eliminar, mover a procesados
                        carpeta_procesados = self.file_manager.folders['output'] / 'originales_procesados'
                        carpeta_procesados.mkdir(exist_ok=True)
                        destino_original = carpeta_procesados / filepath.name
                        self.file_manager.mover_archivo(str(filepath), str(destino_original))
                        resultado['metadata']['archivo_original_movido'] = str(destino_original)
                else:
                    # Mover a carpeta de procesados
                    carpeta_procesados = self.file_manager.folders['output'] / 'originales_procesados'
                    carpeta_procesados.mkdir(exist_ok=True)
                    destino_original = carpeta_procesados / filepath.name
                    self.file_manager.mover_archivo(str(filepath), str(destino_original))
                    resultado['metadata']['archivo_original'] = str(destino_original)
            else:
                # Si no se procesó ninguna página, mover a errores
                destino_error = self.file_manager.folders['errors'] / filepath.name
                self.file_manager.mover_archivo(str(filepath), str(destino_error))
                resultado['metadata']['movido_a_errores'] = str(destino_error)
            
            # Cerrar el analyzer
            analyzer.close()
            
        except Exception as e:
            logger.error(f"Error general al procesar {filepath.name}: {e}")
            resultado['errores'].append(f"Error general: {str(e)}")
            resultado['exitoso'] = False
        
        finally:
            # Calcular tiempo de procesamiento
            fin = datetime.now()
            resultado['tiempo_procesamiento'] = (fin - inicio).total_seconds()
            
            # Actualizar estadísticas
            self.estadisticas['archivos_procesados'] += 1
            self.estadisticas['paginas_procesadas'] += resultado['paginas_procesadas']
            
            if resultado['exitoso']:
                self.estadisticas['archivos_exitosos'] += 1
            else:
                self.estadisticas['archivos_con_error'] += 1
                self.estadisticas['errores'].extend(resultado['errores'])
        
        return resultado
    
    def procesar_lote(self, mostrar_progreso: bool = True) -> Dict[str, Any]:
        """
        Procesa todos los archivos pendientes en la carpeta de entrada
        
        Args:
            mostrar_progreso: Si debe mostrar barra de progreso
            
        Returns:
            Diccionario con resumen del procesamiento
        """
        self.estadisticas['tiempo_inicio'] = datetime.now()
        
        # Obtener archivos pendientes
        archivos_pendientes = self.file_manager.listar_archivos_pendientes('.pdf')
        
        if not archivos_pendientes:
            logger.warning("No hay archivos pendientes para procesar")
            return {
                'mensaje': 'No hay archivos pendientes',
                'archivos_procesados': 0
            }
        
        logger.info(f"Iniciando procesamiento de {len(archivos_pendientes)} archivos")
        
        resultados = []
        
        # Procesar archivos
        if mostrar_progreso:
            archivos_iter = tqdm(archivos_pendientes, desc="Procesando archivos")
        else:
            archivos_iter = archivos_pendientes
        
        for archivo in archivos_iter:
            if mostrar_progreso:
                archivos_iter.set_description(f"Procesando: {archivo.name}")
            
            resultado = self.procesar_archivo(str(archivo))
            resultados.append(resultado)
            
            # Actualizar descripción con resultado
            if mostrar_progreso:
                if resultado['exitoso']:
                    archivos_iter.set_description(f"✓ {archivo.name}")
                else:
                    archivos_iter.set_description(f"✗ {archivo.name}")
        
        self.estadisticas['tiempo_fin'] = datetime.now()
        
        # Generar resumen
        resumen = self.generar_resumen_procesamiento(resultados)
        
        # Guardar resumen si está configurado
        if self.guardar_metadata:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            resumen_path = self.file_manager.folders['metadata'] / f"resumen_procesamiento_{timestamp}.json"
            
            with open(resumen_path, 'w', encoding='utf-8') as f:
                json.dump(resumen, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Resumen guardado en: {resumen_path}")
        
        return resumen
    
    def generar_resumen_procesamiento(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera un resumen del procesamiento realizado
        
        Args:
            resultados: Lista de resultados individuales
            
        Returns:
            Diccionario con resumen
        """
        tiempo_total = (self.estadisticas['tiempo_fin'] - self.estadisticas['tiempo_inicio']).total_seconds() \
                      if self.estadisticas['tiempo_fin'] and self.estadisticas['tiempo_inicio'] else 0
        
        resumen = {
            'fecha_procesamiento': datetime.now().isoformat(),
            'estadisticas': {
                'total_archivos': len(resultados),
                'archivos_exitosos': sum(1 for r in resultados if r['exitoso']),
                'archivos_con_error': sum(1 for r in resultados if not r['exitoso']),
                'total_paginas_procesadas': sum(r['paginas_procesadas'] for r in resultados),
                'total_archivos_generados': sum(len(r['archivos_generados']) for r in resultados),
                'tiempo_total_segundos': tiempo_total,
                'tiempo_promedio_por_archivo': tiempo_total / len(resultados) if resultados else 0
            },
            'archivos_procesados': [
                {
                    'archivo': r['archivo'],
                    'exitoso': r['exitoso'],
                    'paginas': r['paginas_procesadas'],
                    'archivos_generados': len(r['archivos_generados']),
                    'tiempo': r['tiempo_procesamiento'],
                    'errores': len(r['errores'])
                }
                for r in resultados
            ],
            'errores_encontrados': [
                error for r in resultados for error in r['errores']
            ],
            'estadisticas_carpetas': self.file_manager.obtener_estadisticas()
        }
        
        return resumen
    
    def limpiar_sistema(self, dias_antiguedad_temp: int = 7) -> Dict[str, Any]:
        """
        Realiza limpieza del sistema
        
        Args:
            dias_antiguedad_temp: Días de antigüedad para eliminar temporales
            
        Returns:
            Diccionario con resultados de limpieza
        """
        resultado = {
            'temporales_eliminados': 0,
            'duplicados_detectados': [],
            'espacio_liberado': 0
        }
        
        # Limpiar temporales
        resultado['temporales_eliminados'] = self.file_manager.limpiar_temporales(dias_antiguedad_temp)
        
        # Detectar duplicados en procesados
        archivos_procesados = list(self.file_manager.folders['output'].glob('*.pdf'))
        if archivos_procesados:
            duplicados = self.validator.detectar_duplicados([str(f) for f in archivos_procesados])
            resultado['duplicados_detectados'] = duplicados
        
        # Calcular espacio liberado (aproximado)
        # Aquí podrías agregar lógica para calcular el espacio real liberado
        
        logger.info(f"Limpieza completada: {resultado}")
        
        return resultado