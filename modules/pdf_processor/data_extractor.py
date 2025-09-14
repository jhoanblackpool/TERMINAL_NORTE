"""
Módulo de extracción de datos de facturas
Responsable de extraer información específica de las facturas usando patrones regex
"""
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PatronExtraccion:
    """Clase para definir patrones de extracción"""
    nombre: str
    patron: str
    grupo: int = 1
    flags: int = re.IGNORECASE
    validador: Optional[callable] = None
    transformador: Optional[callable] = None


@dataclass
class DatosFactura:
    """Estructura de datos para almacenar información extraída de una factura"""
    cliente: Optional[str] = None
    local: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha: Optional[datetime] = None
    monto_total: Optional[float] = None
    rut: Optional[str] = None
    direccion: Optional[str] = None
    pagina: Optional[int] = None
    texto_completo: Optional[str] = None
    metadatos_adicionales: Dict[str, Any] = field(default_factory=dict)
    errores_extraccion: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte los datos a diccionario"""
        return {
            'cliente': self.cliente,
            'local': self.local,
            'numero_factura': self.numero_factura,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'monto_total': self.monto_total,
            'rut': self.rut,
            'direccion': self.direccion,
            'pagina': self.pagina,
            'metadatos_adicionales': self.metadatos_adicionales,
            'errores_extraccion': self.errores_extraccion
        }
    
    def es_valido(self) -> bool:
        """Verifica si los datos mínimos requeridos están presentes"""
        return bool(self.cliente and self.local)


class DataExtractor:
    """Clase principal para extracción de datos de facturas"""
    
    # Patrones por defecto (los mismos que tenías en config.py)
    DEFAULT_PATRONES_CLIENTE = [
        PatronExtraccion("cliente_standard", r"CLIENTE:\s*([^\n]+)"),
        PatronExtraccion("cliente_senores", r"Señor\(es\):\s*([^\n]+)"),
        PatronExtraccion("cliente_mayusculas", r"SEÑORES?:\s*([^\n]+)"),
        PatronExtraccion("cliente_nombre", r"Nombre:\s*([^\n]+)"),
        PatronExtraccion("cliente_razon_social", r"Razón Social:\s*([^\n]+)")
    ]
    
    DEFAULT_PATRONES_LOCAL = [
        PatronExtraccion("local_ref_guion", r"REF:\s*\d+-(.*)", 
                        transformador=lambda x: x.strip()),
        PatronExtraccion("local_l_numero", r"(?<![A-Za-z])L\s*(\d+)",
                        validador=lambda x: x.isdigit()),
        PatronExtraccion("local_palabra", r"LOCAL.*?\s*(\d+)",
                        validador=lambda x: x.isdigit()),
        PatronExtraccion("local_ref_simple", r"REF:\s*([^\s]+)"),
        PatronExtraccion("local_bodega", r"BODEGA:\s*(\d+)",
                        validador=lambda x: x.isdigit())
    ]
    
    DEFAULT_PATRONES_ADICIONALES = {
        'numero_factura': [
            PatronExtraccion("documento_equivalente", r"DOCUMENTO EQUIVALENTE\s*No\.\s*(\d+)"),
            PatronExtraccion("factura_numero", r"(?:FACTURA|FACT\.?)\s*(?:N[°º]?|#)?\s*(\d+)"),
            PatronExtraccion("numero_documento", r"N[°º]\s*DOCUMENTO:\s*(\d+)"),
            PatronExtraccion("folio", r"FOLIO:\s*(\d+)")
        ],
        'fecha': [
            PatronExtraccion("fecha_emision", r"FECHA\s*(?:DE\s*)?EMISIÓN:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"),
            PatronExtraccion("fecha_standard", r"FECHA:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"),
            PatronExtraccion("fecha_documento", r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
        ],
        'monto': [
            PatronExtraccion("total_pagar", r"TOTAL\s*(?:A\s*)?PAGAR:?\s*\$?\s*([\d.,]+)"),
            PatronExtraccion("monto_total", r"TOTAL:?\s*\$?\s*([\d.,]+)"),
            PatronExtraccion("valor_total", r"VALOR\s*TOTAL:?\s*\$?\s*([\d.,]+)")
        ],
        'rut': [
            PatronExtraccion("rut_cliente", r"RUT:?\s*([\d.-]+)"),
            PatronExtraccion("rut_cuit", r"(?:CUIT|RUT|RUN):?\s*([\d.-]+)")
        ]
    }
    
    def __init__(self, patrones_cliente: List[PatronExtraccion] = None,
                 patrones_local: List[PatronExtraccion] = None,
                 patrones_adicionales: Dict[str, List[PatronExtraccion]] = None):
        """
        Inicializa el extractor con patrones personalizados o por defecto
        
        Args:
            patrones_cliente: Lista de patrones para extraer cliente
            patrones_local: Lista de patrones para extraer local
            patrones_adicionales: Diccionario con patrones adicionales
        """
        self.patrones_cliente = patrones_cliente or self.DEFAULT_PATRONES_CLIENTE
        self.patrones_local = patrones_local or self.DEFAULT_PATRONES_LOCAL
        self.patrones_adicionales = patrones_adicionales or self.DEFAULT_PATRONES_ADICIONALES
        
    def extraer_con_patron(self, texto: str, patrones: List[PatronExtraccion]) -> Tuple[Optional[str], Optional[str]]:
        """
        Intenta extraer información usando una lista de patrones
        
        Args:
            texto: Texto donde buscar
            patrones: Lista de patrones a probar
            
        Returns:
            Tupla (valor_extraido, nombre_patron) o (None, None)
        """
        for patron in patrones:
            try:
                match = re.search(patron.patron, texto, patron.flags)
                if match:
                    valor = match.group(patron.grupo).strip()
                    
                    # Aplicar validador si existe
                    if patron.validador and not patron.validador(valor):
                        continue
                    
                    # Aplicar transformador si existe
                    if patron.transformador:
                        valor = patron.transformador(valor)
                    
                    logger.debug(f"Extracción exitosa con patrón '{patron.nombre}': {valor}")
                    return valor, patron.nombre
                    
            except Exception as e:
                logger.error(f"Error con patrón '{patron.nombre}': {e}")
                continue
        
        return None, None
    
    def extraer_cliente(self, texto: str) -> Optional[str]:
        """
        Extrae el nombre del cliente del texto
        
        Args:
            texto: Texto de la factura
            
        Returns:
            Nombre del cliente o None
        """
        cliente, patron_usado = self.extraer_con_patron(texto, self.patrones_cliente)
        
        if not cliente:
            logger.warning("No se pudo extraer el cliente con ningún patrón")
        else:
            # Limpiar el nombre del cliente
            cliente = self.limpiar_texto(cliente)
            
        return cliente
    
    def extraer_local(self, texto: str) -> Optional[str]:
        """
        Extrae el número o identificador del local
        
        Args:
            texto: Texto de la factura
            
        Returns:
            Identificador del local o None
        """
        local, patron_usado = self.extraer_con_patron(texto, self.patrones_local)
        
        if not local:
            logger.warning("No se pudo extraer el local con ningún patrón")
        else:
            # Formatear el local si es necesario
            local = self.formatear_local(local)
            
        return local
    
    def extraer_datos_completos(self, texto: str, pagina: int = None) -> DatosFactura:
        """
        Extrae todos los datos disponibles de una factura
        
        Args:
            texto: Texto completo de la factura
            pagina: Número de página (opcional)
            
        Returns:
            Objeto DatosFactura con toda la información extraída
        """
        datos = DatosFactura(texto_completo=texto, pagina=pagina)
        
        # Extraer datos principales
        try:
            datos.cliente = self.extraer_cliente(texto)
            if not datos.cliente:
                datos.errores_extraccion.append("No se pudo extraer el cliente")
        except Exception as e:
            logger.error(f"Error al extraer cliente: {e}")
            datos.errores_extraccion.append(f"Error al extraer cliente: {str(e)}")
        
        try:
            datos.local = self.extraer_local(texto)
            if not datos.local:
                datos.errores_extraccion.append("No se pudo extraer el local")
        except Exception as e:
            logger.error(f"Error al extraer local: {e}")
            datos.errores_extraccion.append(f"Error al extraer local: {str(e)}")
        
        # Extraer datos adicionales
        for campo, patrones in self.patrones_adicionales.items():
            try:
                valor, _ = self.extraer_con_patron(texto, patrones)
                
                if valor:
                    if campo == 'numero_factura':
                        datos.numero_factura = valor
                    elif campo == 'fecha':
                        datos.fecha = self.parsear_fecha(valor)
                    elif campo == 'monto':
                        datos.monto_total = self.parsear_monto(valor)
                    elif campo == 'rut':
                        datos.rut = self.formatear_rut(valor)
                    else:
                        datos.metadatos_adicionales[campo] = valor
                        
            except Exception as e:
                logger.error(f"Error al extraer {campo}: {e}")
                datos.errores_extraccion.append(f"Error al extraer {campo}: {str(e)}")
        
        return datos
    
    def limpiar_texto(self, texto: str) -> str:
        """
        Limpia y normaliza el texto extraído
        
        Args:
            texto: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not texto:
            return texto
            
        # Eliminar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto)
        
        # Eliminar caracteres especiales al inicio y final
        texto = texto.strip(' .-,;:')
        
        return texto
    
    def formatear_local(self, local: str) -> str:
        """
        Formatea el identificador del local
        
        Args:
            local: Identificador del local
            
        Returns:
            Local formateado
        """
        if not local:
            return local
        
        # Simplemente limpiar espacios al inicio y final
        return local.strip()
    
    def parsear_fecha(self, fecha_str: str) -> Optional[datetime]:
        """
        Convierte string de fecha a objeto datetime
        
        Args:
            fecha_str: String con la fecha
            
        Returns:
            Objeto datetime o None
        """
        formatos_fecha = [
            '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
            '%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'
        ]
        
        for formato in formatos_fecha:
            try:
                return datetime.strptime(fecha_str.strip(), formato)
            except ValueError:
                continue
        
        logger.warning(f"No se pudo parsear la fecha: {fecha_str}")
        return None
    
    def parsear_monto(self, monto_str: str) -> Optional[float]:
        """
        Convierte string de monto a float
        
        Args:
            monto_str: String con el monto
            
        Returns:
            Monto como float o None
        """
        try:
            # Eliminar símbolos de moneda y espacios
            monto_str = re.sub(r'[$\s]', '', monto_str)
            
            # Reemplazar coma por punto si es decimal
            if ',' in monto_str and '.' in monto_str:
                # Formato 1,000.00 o 1.000,00
                if monto_str.rindex(',') > monto_str.rindex('.'):
                    # Formato europeo: 1.000,00
                    monto_str = monto_str.replace('.', '').replace(',', '.')
                else:
                    # Formato americano: 1,000.00
                    monto_str = monto_str.replace(',', '')
            elif ',' in monto_str:
                # Solo coma, podría ser decimal
                parts = monto_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Probablemente decimal
                    monto_str = monto_str.replace(',', '.')
                else:
                    # Probablemente separador de miles
                    monto_str = monto_str.replace(',', '')
            
            return float(monto_str)
            
        except Exception as e:
            logger.error(f"Error al parsear monto '{monto_str}': {e}")
            return None
    
    def formatear_rut(self, rut: str) -> str:
        """
        Formatea un RUT/RUN chileno
        
        Args:
            rut: String con el RUT
            
        Returns:
            RUT formateado
        """
        # Eliminar puntos y guiones
        rut = re.sub(r'[.-]', '', rut)
        
        if len(rut) > 1:
            # Formato XX.XXX.XXX-X
            return f"{rut[:-1]}-{rut[-1]}"
        
        return rut
    
    def validar_extraccion(self, datos: DatosFactura) -> Dict[str, Any]:
        """
        Valida los datos extraídos
        
        Args:
            datos: Datos extraídos de la factura
            
        Returns:
            Diccionario con resultados de validación
        """
        validacion = {
            'es_valido': True,
            'campos_faltantes': [],
            'advertencias': []
        }
        
        # Campos obligatorios
        if not datos.cliente:
            validacion['campos_faltantes'].append('cliente')
            validacion['es_valido'] = False
        
        if not datos.local:
            validacion['campos_faltantes'].append('local')
            validacion['es_valido'] = False
        
        # Campos opcionales pero importantes
        if not datos.numero_factura:
            validacion['advertencias'].append('No se encontró número de factura')
        
        if not datos.fecha:
            validacion['advertencias'].append('No se encontró fecha')
        
        if not datos.monto_total:
            validacion['advertencias'].append('No se encontró monto total')
        
        return validacion