"""
Módulo de análisis de contenido PDF
Responsable de abrir, leer y analizar archivos PDF
"""
import logging
from typing import Optional, Dict, Any, List
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFAnalyzer:
    """Clase para análisis y manipulación de archivos PDF"""
    
    def __init__(self, filepath: str):
        """
        Inicializa el analizador de PDF
        
        Args:
            filepath: Ruta al archivo PDF
        """
        self.filepath = Path(filepath)
        self.pdf_reader = None
        self.pdf_plumber = None
        self.metadata = {}
        self._initialize()
    
    def _initialize(self):
        """Inicializa los lectores de PDF y extrae metadatos básicos"""
        try:
            with open(self.filepath, 'rb') as file:
                self.pdf_reader = PdfReader(file)
                self.metadata = {
                    'filename': self.filepath.name,
                    'total_pages': len(self.pdf_reader.pages),
                    'path': str(self.filepath),
                    'size': self.filepath.stat().st_size,
                    'is_encrypted': self.pdf_reader.is_encrypted
                }
                
                # Extraer metadatos del documento si están disponibles
                if self.pdf_reader.metadata:
                    self.metadata['document_info'] = {
                        'title': self.pdf_reader.metadata.get('/Title', ''),
                        'author': self.pdf_reader.metadata.get('/Author', ''),
                        'subject': self.pdf_reader.metadata.get('/Subject', ''),
                        'creator': self.pdf_reader.metadata.get('/Creator', ''),
                        'producer': self.pdf_reader.metadata.get('/Producer', ''),
                        'creation_date': str(self.pdf_reader.metadata.get('/CreationDate', '')),
                        'modification_date': str(self.pdf_reader.metadata.get('/ModDate', ''))
                    }
                    
                logger.info(f"PDF inicializado: {self.filepath.name} con {self.metadata['total_pages']} páginas")
        except Exception as e:
            logger.error(f"Error al inicializar PDF {self.filepath}: {e}")
            raise
    
    def extract_page_text(self, page_number: int) -> Optional[str]:
        """
        Extrae el texto de una página específica
        
        Args:
            page_number: Número de página (0-indexed)
            
        Returns:
            Texto extraído o None si hay error
        """
        try:
            with pdfplumber.open(self.filepath) as pdf:
                if page_number >= len(pdf.pages):
                    logger.error(f"Página {page_number} no existe en el PDF")
                    return None
                    
                page = pdf.pages[page_number]
                text = page.extract_text()
                
                if not text:
                    logger.warning(f"No se pudo extraer texto de la página {page_number + 1}")
                    
                return text
        except Exception as e:
            logger.error(f"Error al extraer texto de la página {page_number}: {e}")
            return None
    
    def extract_all_text(self) -> List[Dict[str, Any]]:
        """
        Extrae el texto de todas las páginas del PDF
        
        Returns:
            Lista con diccionarios conteniendo el texto de cada página
        """
        pages_data = []
        
        try:
            with pdfplumber.open(self.filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        pages_data.append({
                            'page_number': i + 1,
                            'text': text or '',
                            'has_text': bool(text),
                            'char_count': len(text) if text else 0
                        })
                    except Exception as e:
                        logger.error(f"Error al procesar página {i + 1}: {e}")
                        pages_data.append({
                            'page_number': i + 1,
                            'text': '',
                            'has_text': False,
                            'error': str(e)
                        })
                        
        except Exception as e:
            logger.error(f"Error al extraer texto del PDF completo: {e}")
            
        return pages_data
    
    def split_page(self, page_number: int, output_path: str) -> bool:
        """
        Extrae una página individual y la guarda como un nuevo PDF
        
        Args:
            page_number: Número de página a extraer (0-indexed)
            output_path: Ruta donde guardar el PDF resultante
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            with open(self.filepath, 'rb') as input_file:
                pdf_reader = PdfReader(input_file)
                
                if page_number >= len(pdf_reader.pages):
                    logger.error(f"Página {page_number} no existe")
                    return False
                
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_number])
                
                # Guardar el nuevo PDF
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                    
                logger.info(f"Página {page_number + 1} guardada en: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error al dividir página {page_number}: {e}")
            return False
    
    def split_all_pages(self, output_directory: str, name_pattern: str = "page_{page_num}.pdf") -> List[str]:
        """
        Divide el PDF en páginas individuales
        
        Args:
            output_directory: Directorio donde guardar las páginas
            name_pattern: Patrón de nombre para los archivos
            
        Returns:
            Lista de rutas de los archivos creados
        """
        created_files = []
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.filepath, 'rb') as input_file:
                pdf_reader = PdfReader(input_file)
                
                for i in range(len(pdf_reader.pages)):
                    pdf_writer = PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[i])
                    
                    # Generar nombre del archivo
                    filename = name_pattern.format(page_num=i+1)
                    output_path = output_dir / filename
                    
                    with open(output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                        
                    created_files.append(str(output_path))
                    logger.debug(f"Página {i+1} guardada: {filename}")
                    
            logger.info(f"PDF dividido en {len(created_files)} archivos")
            
        except Exception as e:
            logger.error(f"Error al dividir PDF: {e}")
            
        return created_files
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Obtiene los metadatos del PDF
        
        Returns:
            Diccionario con metadatos
        """
        return self.metadata.copy()
    
    def validate_pdf(self) -> Dict[str, Any]:
        """
        Valida la integridad del archivo PDF
        
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        try:
            # Verificar que el archivo existe
            if not self.filepath.exists():
                validation_result['is_valid'] = False
                validation_result['errors'].append("El archivo no existe")
                return validation_result
            
            validation_result['checks']['file_exists'] = True
            
            # Verificar que es un PDF válido
            try:
                with open(self.filepath, 'rb') as file:
                    pdf_test = PdfReader(file)
                    validation_result['checks']['valid_pdf'] = True
                    
                    # Verificar si está encriptado
                    if pdf_test.is_encrypted:
                        validation_result['warnings'].append("El PDF está encriptado")
                        validation_result['checks']['is_encrypted'] = True
                    else:
                        validation_result['checks']['is_encrypted'] = False
                    
                    # Verificar número de páginas
                    num_pages = len(pdf_test.pages)
                    if num_pages == 0:
                        validation_result['errors'].append("El PDF no tiene páginas")
                        validation_result['is_valid'] = False
                    validation_result['checks']['page_count'] = num_pages
                    
                    # Verificar que se puede extraer texto
                    with pdfplumber.open(self.filepath) as pdf:
                        has_extractable_text = False
                        for page in pdf.pages[:min(3, len(pdf.pages))]:  # Revisar primeras 3 páginas
                            text = page.extract_text()
                            if text and len(text.strip()) > 0:
                                has_extractable_text = True
                                break
                        
                        validation_result['checks']['has_extractable_text'] = has_extractable_text
                        if not has_extractable_text:
                            validation_result['warnings'].append("No se pudo extraer texto del PDF")
                            
            except Exception as e:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"PDF corrupto o inválido: {str(e)}")
                validation_result['checks']['valid_pdf'] = False
                
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Error durante la validación: {str(e)}")
            
        return validation_result
    
    def close(self):
        """Cierra los recursos abiertos"""
        self.pdf_reader = None
        self.pdf_plumber = None