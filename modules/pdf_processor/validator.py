"""
Módulo de validación de integridad
Responsable de validar archivos PDF y datos extraídos
"""
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PDFValidator:
    """Validador de archivos PDF y datos extraídos"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el validador
        
        Args:
            config: Configuración de validación
        """
        self.config = config or {}
        
        # Configuración de validación
        self.min_file_size = self.config.get('min_file_size', 100)  # bytes
        self.max_file_size = self.config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.required_fields = self.config.get('required_fields', ['cliente', 'local'])
        self.min_text_length = self.config.get('min_text_length', 10)
        
        # Historial de validaciones
        self.validation_history = []
    
    def validar_archivo_pdf(self, filepath: str) -> Dict[str, Any]:
        """
        Valida la integridad completa de un archivo PDF
        
        Args:
            filepath: Ruta al archivo PDF
            
        Returns:
            Diccionario con resultados de validación
        """
        resultado = {
            'archivo': filepath,
            'timestamp': datetime.now().isoformat(),
            'es_valido': True,
            'errores': [],
            'advertencias': [],
            'detalles': {}
        }
        
        filepath = Path(filepath)
        
        # 1. Verificar que el archivo existe
        if not filepath.exists():
            resultado['es_valido'] = False
            resultado['errores'].append("El archivo no existe")
            return resultado
        
        resultado['detalles']['existe'] = True
        
        # 2. Verificar tamaño del archivo
        try:
            tamaño = filepath.stat().st_size
            resultado['detalles']['tamaño'] = tamaño
            
            if tamaño < self.min_file_size:
                resultado['es_valido'] = False
                resultado['errores'].append(f"Archivo muy pequeño ({tamaño} bytes)")
            elif tamaño > self.max_file_size:
                resultado['es_valido'] = False
                resultado['errores'].append(f"Archivo muy grande ({tamaño} bytes)")
                
        except Exception as e:
            resultado['errores'].append(f"Error al verificar tamaño: {str(e)}")
        
        # 3. Verificar que es un PDF válido
        try:
            from PyPDF2 import PdfReader
            
            with open(filepath, 'rb') as file:
                pdf = PdfReader(file)
                resultado['detalles']['num_paginas'] = len(pdf.pages)
                resultado['detalles']['es_encriptado'] = pdf.is_encrypted
                
                if pdf.is_encrypted:
                    resultado['advertencias'].append("El PDF está encriptado")
                
                if len(pdf.pages) == 0:
                    resultado['es_valido'] = False
                    resultado['errores'].append("El PDF no tiene páginas")
                    
                # Verificar metadatos
                if pdf.metadata:
                    resultado['detalles']['tiene_metadata'] = True
                    metadata = {}
                    for key, value in pdf.metadata.items():
                        try:
                            metadata[key] = str(value)
                        except:
                            metadata[key] = "No convertible"
                    resultado['detalles']['metadata'] = metadata
                else:
                    resultado['detalles']['tiene_metadata'] = False
                    
        except Exception as e:
            resultado['es_valido'] = False
            resultado['errores'].append(f"PDF corrupto o inválido: {str(e)}")
            resultado['detalles']['pdf_valido'] = False
            return resultado
        
        resultado['detalles']['pdf_valido'] = True
        
        # 4. Verificar que se puede extraer texto
        try:
            import pdfplumber
            
            with pdfplumber.open(filepath) as pdf:
                texto_total = ""
                paginas_con_texto = 0
                
                for i, page in enumerate(pdf.pages):
                    try:
                        texto = page.extract_text()
                        if texto and len(texto.strip()) > self.min_text_length:
                            paginas_con_texto += 1
                            texto_total += texto
                    except Exception as e:
                        resultado['advertencias'].append(f"Error al extraer texto de página {i+1}: {str(e)}")
                
                resultado['detalles']['paginas_con_texto'] = paginas_con_texto
                resultado['detalles']['longitud_texto_total'] = len(texto_total)
                
                if paginas_con_texto == 0:
                    resultado['advertencias'].append("No se pudo extraer texto de ninguna página")
                    resultado['detalles']['tiene_texto_extraible'] = False
                else:
                    resultado['detalles']['tiene_texto_extraible'] = True
                    
        except Exception as e:
            resultado['advertencias'].append(f"Error al verificar extracción de texto: {str(e)}")
        
        # 5. Calcular hash del archivo para integridad
        try:
            resultado['detalles']['hash_md5'] = self._calcular_hash(filepath, 'md5')
            resultado['detalles']['hash_sha256'] = self._calcular_hash(filepath, 'sha256')
        except Exception as e:
            resultado['advertencias'].append(f"Error al calcular hash: {str(e)}")
        
        # Guardar en historial
        self.validation_history.append(resultado)
        
        return resultado
    
    def validar_datos_extraidos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida los datos extraídos de una factura
        
        Args:
            datos: Diccionario con datos extraídos
            
        Returns:
            Diccionario con resultados de validación
        """
        resultado = {
            'es_valido': True,
            'campos_faltantes': [],
            'campos_invalidos': [],
            'advertencias': [],
            'detalles': {}
        }
        
        # Verificar campos requeridos
        for campo in self.required_fields:
            if campo not in datos or not datos[campo]:
                resultado['campos_faltantes'].append(campo)
                resultado['es_valido'] = False
        
        # Validar cliente
        if 'cliente' in datos and datos['cliente']:
            cliente = datos['cliente']
            resultado['detalles']['cliente'] = {
                'valor': cliente,
                'longitud': len(cliente)
            }
            
            if len(cliente) < 3:
                resultado['campos_invalidos'].append('cliente: muy corto')
                resultado['es_valido'] = False
            elif len(cliente) > 100:
                resultado['advertencias'].append('cliente: muy largo, puede estar truncado')
            
            # Verificar caracteres sospechosos
            if any(char in cliente for char in ['@', '#', '$', '%', '^', '&', '*']):
                resultado['advertencias'].append('cliente: contiene caracteres inusuales')
        
        # Validar local
        if 'local' in datos and datos['local']:
            local = datos['local']
            resultado['detalles']['local'] = {
                'valor': local,
                'tipo': 'numerico' if local.replace('L', '').isdigit() else 'alfanumerico'
            }
            
            if len(local) == 0:
                resultado['campos_invalidos'].append('local: vacío')
                resultado['es_valido'] = False
        
        # Validar número de factura
        if 'numero_factura' in datos and datos['numero_factura']:
            num_factura = datos['numero_factura']
            resultado['detalles']['numero_factura'] = {
                'valor': num_factura,
                'es_numerico': num_factura.isdigit()
            }
            
            if not num_factura.replace('-', '').replace('/', '').isalnum():
                resultado['advertencias'].append('numero_factura: formato inusual')
        
        # Validar fecha
        if 'fecha' in datos and datos['fecha']:
            try:
                if isinstance(datos['fecha'], str):
                    # Intentar parsear si es string
                    from datetime import datetime
                    fecha = datetime.fromisoformat(datos['fecha'])
                else:
                    fecha = datos['fecha']
                
                resultado['detalles']['fecha'] = {
                    'valor': str(fecha),
                    'es_futura': fecha > datetime.now()
                }
                
                if fecha > datetime.now():
                    resultado['advertencias'].append('fecha: fecha futura detectada')
                
                # Verificar si la fecha es muy antigua (más de 5 años)
                if (datetime.now() - fecha).days > 1825:
                    resultado['advertencias'].append('fecha: fecha muy antigua (más de 5 años)')
                    
            except Exception as e:
                resultado['campos_invalidos'].append(f'fecha: formato inválido - {str(e)}')
        
        # Validar monto
        if 'monto_total' in datos and datos['monto_total'] is not None:
            monto = datos['monto_total']
            resultado['detalles']['monto_total'] = {
                'valor': monto,
                'es_valido': isinstance(monto, (int, float)) and monto >= 0
            }
            
            if monto < 0:
                resultado['campos_invalidos'].append('monto_total: valor negativo')
                resultado['es_valido'] = False
            elif monto == 0:
                resultado['advertencias'].append('monto_total: valor cero')
            elif monto > 10000000:  # Más de 10 millones
                resultado['advertencias'].append('monto_total: valor muy alto')
        
        # Validar RUT (si existe)
        if 'rut' in datos and datos['rut']:
            rut = datos['rut']
            resultado['detalles']['rut'] = {
                'valor': rut,
                'formato_valido': self._validar_formato_rut(rut)
            }
            
            if not self._validar_formato_rut(rut):
                resultado['advertencias'].append('rut: formato inválido')
        
        return resultado
    
    def validar_lote(self, archivos: List[str]) -> Dict[str, Any]:
        """
        Valida un lote de archivos PDF
        
        Args:
            archivos: Lista de rutas de archivos
            
        Returns:
            Resumen de validación del lote
        """
        resumen = {
            'total_archivos': len(archivos),
            'archivos_validos': 0,
            'archivos_invalidos': 0,
            'archivos_con_advertencias': 0,
            'errores_comunes': {},
            'detalles': []
        }
        
        for archivo in archivos:
            try:
                validacion = self.validar_archivo_pdf(archivo)
                
                resumen['detalles'].append({
                    'archivo': Path(archivo).name,
                    'valido': validacion['es_valido'],
                    'errores': len(validacion['errores']),
                    'advertencias': len(validacion['advertencias'])
                })
                
                if validacion['es_valido']:
                    resumen['archivos_validos'] += 1
                else:
                    resumen['archivos_invalidos'] += 1
                
                if validacion['advertencias']:
                    resumen['archivos_con_advertencias'] += 1
                
                # Contar errores comunes
                for error in validacion['errores']:
                    tipo_error = error.split(':')[0] if ':' in error else error
                    resumen['errores_comunes'][tipo_error] = resumen['errores_comunes'].get(tipo_error, 0) + 1
                    
            except Exception as e:
                logger.error(f"Error al validar {archivo}: {e}")
                resumen['archivos_invalidos'] += 1
                resumen['detalles'].append({
                    'archivo': Path(archivo).name,
                    'valido': False,
                    'error': str(e)
                })
        
        return resumen
    
    def generar_reporte_validacion(self, output_path: str = None) -> str:
        """
        Genera un reporte de todas las validaciones realizadas
        
        Args:
            output_path: Ruta donde guardar el reporte (opcional)
            
        Returns:
            Contenido del reporte como string
        """
        reporte = []
        reporte.append("=" * 60)
        reporte.append("REPORTE DE VALIDACIÓN DE ARCHIVOS PDF")
        reporte.append("=" * 60)
        reporte.append(f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        reporte.append(f"Total de validaciones: {len(self.validation_history)}")
        reporte.append("")
        