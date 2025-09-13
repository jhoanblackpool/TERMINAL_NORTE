"""
Módulo de gestión de archivos
Responsable de organizar, mover y gestionar archivos PDF
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import time
import json
import send2trash

logger = logging.getLogger(__name__)


class FileManager:
    """Gestor principal de archivos y carpetas del sistema"""
    
    # Caracteres inválidos para nombres de archivo en Windows/Linux
    CARACTERES_INVALIDOS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\n', '\r', '\t']
    
    def __init__(self, base_path: str, config: Dict[str, Any] = None):
        """
        Inicializa el gestor de archivos
        
        Args:
            base_path: Ruta base del sistema
            config: Configuración adicional
        """
        self.base_path = Path(base_path)
        self.config = config or {}
        
        # Configuración de carpetas por defecto
        self.folders = {
            'input': self.base_path / 'facturas_por_procesar',
            'output': self.base_path / 'facturas_procesadas',
            'errors': self.base_path / 'facturas_con_error',
            'backup': self.base_path / 'backup_originales',
            'temp': self.base_path / 'temp',
            'logs': self.base_path / 'logs',
            'metadata': self.base_path / 'metadata'
        }
        
        # Configuración de reintentos
        self.max_reintentos = self.config.get('max_reintentos', 3)
        self.tiempo_espera = self.config.get('tiempo_espera_reintento', 1)
        
        # Inicializar estructura de carpetas
        self._inicializar_estructura()
    
    def _inicializar_estructura(self):
        """Crea la estructura de carpetas necesaria"""
        for nombre, ruta in self.folders.items():
            try:
                ruta.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Carpeta '{nombre}' creada/verificada en: {ruta}")
            except Exception as e:
                logger.error(f"Error al crear carpeta '{nombre}': {e}")
    
    def limpiar_nombre_archivo(self, nombre: str, reemplazo: str = '') -> str:
        """
        Elimina caracteres inválidos de un nombre de archivo
        
        Args:
            nombre: Nombre a limpiar
            reemplazo: Caracter de reemplazo para caracteres inválidos
            
        Returns:
            Nombre limpio y seguro para usar como nombre de archivo
        """
        if not nombre:
            return "sin_nombre"
        
        # Eliminar caracteres inválidos
        for char in self.CARACTERES_INVALIDOS:
            nombre = nombre.replace(char, reemplazo)
        
        # Eliminar espacios múltiples
        nombre = ' '.join(nombre.split())
        
        # Eliminar espacios al inicio y final
        nombre = nombre.strip()
        
        # Limitar longitud del nombre (Windows tiene límite de 255 caracteres)
        if len(nombre) > 200:
            nombre = nombre[:200]
        
        # Si quedó vacío, usar nombre por defecto
        if not nombre:
            nombre = "sin_nombre"
        
        return nombre
    
    def generar_nombre_factura(self, cliente: str, local: str, 
                              numero_factura: str = None,
                              fecha: datetime = None,
                              formato: str = "{local} - {cliente}") -> str:
        """
        Genera un nombre de archivo para una factura
        
        Args:
            cliente: Nombre del cliente
            local: Identificador del local
            numero_factura: Número de factura (opcional)
            fecha: Fecha de la factura (opcional)
            formato: Formato del nombre (puede incluir {cliente}, {local}, {factura}, {fecha})
            
        Returns:
            Nombre de archivo generado
        """
        # Limpiar valores
        cliente_limpio = self.limpiar_nombre_archivo(cliente)
        local_limpio = self.limpiar_nombre_archivo(local)
        
        # Preparar diccionario de reemplazo
        valores = {
            'cliente': cliente_limpio,
            'local': local_limpio,
            'factura': numero_factura or '',
            'fecha': fecha.strftime('%Y%m%d') if fecha else ''
        }
        
        # Generar nombre
        try:
            nombre = formato.format(**valores)
        except KeyError:
            # Si hay error en el formato, usar formato por defecto
            nombre = f"{local_limpio} - {cliente_limpio}"
        
        # Agregar extensión si no la tiene
        if not nombre.endswith('.pdf'):
            nombre += '.pdf'
        
        return nombre
    
    def mover_archivo(self, origen: str, destino: str, 
                     crear_carpeta: bool = True,
                     sobrescribir: bool = False) -> bool:
        """
        Mueve un archivo con reintentos en caso de error
        
        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino
            crear_carpeta: Si debe crear la carpeta destino si no existe
            sobrescribir: Si debe sobrescribir si el destino existe
            
        Returns:
            True si la operación fue exitosa
        """
        origen = Path(origen)
        destino = Path(destino)
        
        if not origen.exists():
            logger.error(f"El archivo origen no existe: {origen}")
            return False
        
        # Crear carpeta destino si es necesario
        if crear_carpeta:
            destino.parent.mkdir(parents=True, exist_ok=True)
        
        # Verificar si el destino ya existe
        if destino.exists() and not sobrescribir:
            # Generar nombre único
            destino = self._generar_nombre_unico(destino)
        
        # Intentar mover con reintentos
        for intento in range(self.max_reintentos):
            try:
                shutil.move(str(origen), str(destino))
                logger.info(f"Archivo movido: {origen.name} -> {destino}")
                return True
                
            except PermissionError:
                if intento < self.max_reintentos - 1:
                    logger.warning(f"Archivo bloqueado, reintento {intento + 1}/{self.max_reintentos}")
                    time.sleep(self.tiempo_espera)
                else:
                    logger.error(f"No se pudo mover el archivo después de {self.max_reintentos} intentos")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al mover archivo: {e}")
                return False
        
        return False
    
    def copiar_archivo(self, origen: str, destino: str,
                      crear_carpeta: bool = True,
                      sobrescribir: bool = False) -> bool:
        """
        Copia un archivo con reintentos en caso de error
        
        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino
            crear_carpeta: Si debe crear la carpeta destino si no existe
            sobrescribir: Si debe sobrescribir si el destino existe
            
        Returns:
            True si la operación fue exitosa
        """
        origen = Path(origen)
        destino = Path(destino)
        
        if not origen.exists():
            logger.error(f"El archivo origen no existe: {origen}")
            return False
        
        # Crear carpeta destino si es necesario
        if crear_carpeta:
            destino.parent.mkdir(parents=True, exist_ok=True)
        
        # Verificar si el destino ya existe
        if destino.exists() and not sobrescribir:
            destino = self._generar_nombre_unico(destino)
        
        # Intentar copiar con reintentos
        for intento in range(self.max_reintentos):
            try:
                shutil.copy2(str(origen), str(destino))
                logger.info(f"Archivo copiado: {origen.name} -> {destino}")
                return True
                
            except PermissionError:
                if intento < self.max_reintentos - 1:
                    logger.warning(f"Archivo bloqueado, reintento {intento + 1}/{self.max_reintentos}")
                    time.sleep(self.tiempo_espera)
                else:
                    logger.error(f"No se pudo copiar el archivo después de {self.max_reintentos} intentos")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al copiar archivo: {e}")
                return False
        
        return False
    
    def crear_backup(self, archivo: str, incluir_timestamp: bool = True) -> Optional[str]:
        """
        Crea una copia de respaldo de un archivo
        
        Args:
            archivo: Ruta del archivo a respaldar
            incluir_timestamp: Si debe incluir timestamp en el nombre del backup
            
        Returns:
            Ruta del archivo de backup o None si falló
        """
        archivo = Path(archivo)
        
        if not archivo.exists():
            logger.error(f"No se puede crear backup, archivo no existe: {archivo}")
            return None
        
        # Generar nombre del backup
        if incluir_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_backup = f"{archivo.stem}_{timestamp}{archivo.suffix}"
        else:
            nombre_backup = archivo.name
        
        destino_backup = self.folders['backup'] / nombre_backup
        
        # Si existe, generar nombre único
        if destino_backup.exists():
            destino_backup = self._generar_nombre_unico(destino_backup)
        
        # Copiar archivo
        if self.copiar_archivo(str(archivo), str(destino_backup)):
            logger.info(f"Backup creado: {destino_backup}")
            return str(destino_backup)
        
        return None
    
    def eliminar_archivo(self, archivo: str, intentar_papelera: bool = True) -> bool:
        """
        Elimina un archivo de forma segura
        
        Args:
            archivo: Ruta del archivo a eliminar
            intentar_papelera: Si debe intentar mover a papelera primero
            
        Returns:
            True si se eliminó correctamente
        """
        archivo = Path(archivo)
        
        if not archivo.exists():
            logger.warning(f"El archivo no existe: {archivo}")
            return True  # Consideramos exitoso si no existe
        
        # Intentar eliminar con reintentos
        for intento in range(self.max_reintentos):
            try:
                # Dar permisos completos antes de eliminar
                os.chmod(str(archivo), 0o777)
                
                if intentar_papelera:
                    # Intentar mover a papelera (solo Windows)
                    try:
                       
                        send2trash.send2trash(str(archivo))
                        logger.info(f"Archivo enviado a papelera: {archivo}")
                        return True
                    except ImportError:
                        pass  # Si no está disponible send2trash, eliminar directamente
                
                # Eliminar directamente
                archivo.unlink()
                logger.info(f"Archivo eliminado: {archivo}")
                return True
                
            except PermissionError:
                if intento < self.max_reintentos - 1:
                    logger.warning(f"Archivo bloqueado, reintento {intento + 1}/{self.max_reintentos}")
                    time.sleep(self.tiempo_espera)
                else:
                    logger.error(f"No se pudo eliminar el archivo después de {self.max_reintentos} intentos")
                    return False
                    
            except Exception as e:
                logger.error(f"Error al eliminar archivo: {e}")
                return False
        
        return False
    
    def organizar_factura_procesada(self, archivo_original: str,
                                   archivo_procesado: str,
                                   datos_factura: Dict[str, Any],
                                   crear_backup: bool = True) -> Dict[str, Any]:
        """
        Organiza una factura procesada según los datos extraídos
        
        Args:
            archivo_original: Ruta del archivo original
            archivo_procesado: Ruta del archivo procesado
            datos_factura: Datos extraídos de la factura
            crear_backup: Si debe crear backup del original
            
        Returns:
            Diccionario con información del proceso
        """
        resultado = {
            'exitoso': False,
            'archivo_final': None,
            'backup': None,
            'errores': []
        }
        
        try:
            # Crear backup si se solicita
            if crear_backup:
                resultado['backup'] = self.crear_backup(archivo_original)
                if not resultado['backup']:
                    resultado['errores'].append("No se pudo crear backup")
            
            # Generar nombre final
            cliente = datos_factura.get('cliente', 'sin_cliente')
            local = datos_factura.get('local', 'sin_local')
            nombre_final = self.generar_nombre_factura(cliente, local)
            
            # Determinar carpeta destino
            if datos_factura.get('es_valido', True):
                carpeta_destino = self.folders['output']
            else:
                carpeta_destino = self.folders['errors']
                resultado['errores'].append("Factura marcada como inválida")
            
            # Mover archivo procesado
            destino_final = carpeta_destino / nombre_final
            if self.mover_archivo(archivo_procesado, str(destino_final)):
                resultado['archivo_final'] = str(destino_final)
                resultado['exitoso'] = True
                
                # Eliminar original si todo salió bien
                if not self.eliminar_archivo(archivo_original):
                    # Si no se puede eliminar, moverlo a procesados
                    carpeta_originales = self.folders['output'] / 'originales'
                    carpeta_originales.mkdir(exist_ok=True)
                    self.mover_archivo(
                        archivo_original,
                        str(carpeta_originales / Path(archivo_original).name)
                    )
            else:
                resultado['errores'].append("No se pudo mover el archivo procesado")
                
        except Exception as e:
            logger.error(f"Error al organizar factura: {e}")
            resultado['errores'].append(str(e))
        
        return resultado
    
    def listar_archivos_pendientes(self, extension: str = '.pdf') -> List[Path]:
        """
        Lista los archivos pendientes de procesar
        
        Args:
            extension: Extensión de archivos a buscar
            
        Returns:
            Lista de rutas de archivos
        """
        try:
            archivos = list(self.folders['input'].glob(f'*{extension}'))
            logger.info(f"Se encontraron {len(archivos)} archivos pendientes")
            return archivos
        except Exception as e:
            logger.error(f"Error al listar archivos: {e}")
            return []
    
    def guardar_metadata(self, nombre_archivo: str, metadata: Dict[str, Any]) -> bool:
        """
        Guarda metadatos de un archivo procesado
        
        Args:
            nombre_archivo: Nombre del archivo
            metadata: Metadatos a guardar
            
        Returns:
            True si se guardó correctamente
        """
        try:
            # Agregar timestamp
            metadata['procesado_en'] = datetime.now().isoformat()
            
            # Generar nombre del archivo de metadata
            nombre_meta = Path(nombre_archivo).stem + '_metadata.json'
            ruta_metadata = self.folders['metadata'] / nombre_meta
            
            # Guardar JSON
            with open(ruta_metadata, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Metadata guardada: {ruta_metadata}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar metadata: {e}")
            return False
    
    def limpiar_temporales(self, dias_antiguedad: int = 7) -> int:
        """
        Limpia archivos temporales antiguos
        
        Args:
            dias_antiguedad: Archivos más antiguos que estos días serán eliminados
            
        Returns:
            Número de archivos eliminados
        """
        eliminados = 0
        limite = time.time() - (dias_antiguedad * 24 * 3600)
        
        try:
            for archivo in self.folders['temp'].iterdir():
                if archivo.is_file() and archivo.stat().st_mtime < limite:
                    if self.eliminar_archivo(str(archivo)):
                        eliminados += 1
            
            logger.info(f"Se eliminaron {eliminados} archivos temporales")
            
        except Exception as e:
            logger.error(f"Error al limpiar temporales: {e}")
        
        return eliminados
    
    def _generar_nombre_unico(self, ruta: Path) -> Path:
        """
        Genera un nombre único si el archivo ya existe
        
        Args:
            ruta: Ruta del archivo
            
        Returns:
            Ruta con nombre único
        """
        if not ruta.exists():
            return ruta
        
        contador = 1
        while True:
            nueva_ruta = ruta.parent / f"{ruta.stem}_{contador}{ruta.suffix}"
            if not nueva_ruta.exists():
                return nueva_ruta
            contador += 1
            
            if contador > 1000:  # Evitar bucle infinito
                raise ValueError(f"No se pudo generar nombre único para {ruta}")
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de archivos
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {}
        
        for nombre, carpeta in self.folders.items():
            try:
                if carpeta.exists():
                    archivos = list(carpeta.glob('*.pdf'))
                    stats[nombre] = {
                        'total_archivos': len(archivos),
                        'tamaño_total': sum(f.stat().st_size for f in archivos),
                        'ruta': str(carpeta)
                    }
                else:
                    stats[nombre] = {
                        'total_archivos': 0,
                        'tamaño_total': 0,
                        'ruta': str(carpeta),
                        'nota': 'Carpeta no existe'
                    }
            except Exception as e:
                stats[nombre] = {'error': str(e)}
        
        return stats