# Centro de Ejecución de Robots

Una interfaz web moderna para gestionar y ejecutar agentes de automatización de forma segura.

## 🚀 Características

- **Interfaz moderna y responsiva** con diseño glassmorphism
- **Búsqueda y filtrado avanzado** por área, estado y función
- **Monitoreo en tiempo real** del estado de los agentes
- **Ejecución segura** de agentes con validación de estado
- **Vista de cuadrícula y lista** para mejor organización
- **Detalles completos** con estadísticas de rendimiento
- **Notificaciones toast** para feedback inmediato

## 📁 Estructura del Proyecto

```
modules/web_interface/
├── app.py                 # Servidor Eel y funciones expuestas
├── web/
│   ├── index.html        # Interfaz principal
│   ├── styles.css        # Estilos CSS
│   └── script.js         # Lógica JavaScript
├── requirements.txt      # Dependencias Python
└── README.md            # Este archivo
```

## 🛠️ Instalación

### 1. Clonar o crear el directorio
```bash
mkdir -p modules/web_interface
cd modules/web_interface
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Crear la estructura de directorios
```bash
mkdir web
```

### 5. Colocar los archivos
- `app.py` en la raíz del directorio
- `index.html`, `styles.css`, `script.js` en la carpeta `web/`

## 🚀 Ejecución

```bash
python app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8080`

## 💡 Uso

### Funciones Principales

1. **Buscar Agentes**: Utiliza la barra de búsqueda para encontrar agentes por nombre o función
2. **Filtrar por Área**: Selecciona un área específica (Finanzas, Operaciones, etc.)
3. **Filtrar por Estado**: Muestra solo agentes activos o en mantenimiento
4. **Ejecutar Agente**: Haz clic en "Ejecutar" para iniciar un agente (solo disponible si está activo)
5. **Ver Detalles**: Obtén información completa sobre el rendimiento del agente
6. **Cambiar Vista**: Alterna entre vista de cuadrícula y lista

### Agentes Incluidos

- **Agente Contable** (Finanzas): Envío automático de facturas y recordatorios
- **Agente Compras** (Operaciones): Descarga de órdenes y conciliación con proveedores  
- **Agente Soporte** (CX): Clasificación de tickets y respuestas sugeridas
- **Agente Logística** (Operaciones): Descarga de guías y alertas de entrega
- **Agente Recaudo** (Finanzas): Notificación de pagos y conciliación bancaria
- **Agente Legal** (Backoffice): Validación documental y seguimiento de contratos

## 🔧 Personalización

### Agregar Nuevos Agentes

Modifica la lista `agentes_data` en `app.py`:

```python
agentes_data.append({
    "id": 7,
    "nombre": "Mi Nuevo Agente",
    "area": "Mi Área",
    "estado": "Activo",
    "descripcion": "Descripción de lo que hace el agente",
    "color_estado": "success"
})
```

### Modificar Estilos

Edita `web/styles.css` para cambiar:
- Colores del tema
- Tamaños y espaciado
- Efectos visuales
- Responsividad

### Agregar Funcionalidades

Extiende `app.py` con nuevas funciones:

```python
@eel.expose
def mi_nueva_funcion():
    # Tu lógica aquí
    return resultado
```

Y úsala en `web/script.js`:

```javascript
const resultado = await eel.mi_nueva_funcion()();
```

## 🐛 Solución de Problemas

### La aplicación no se abre
- Verifica que todas las dependencias estén instaladas
- Asegúrate de que el puerto 8080 esté disponible
- Comprueba que Chrome esté instalado (Eel lo prefiere)

### Errores de conexión
- Reinicia la aplicación
- Verifica que no haya firewall bloqueando el puerto
- Revisa la consola de Python para errores específicos

### Problemas de interfaz
- Actualiza el navegador (Ctrl+F5)
- Verifica que todos los archivos estén en las carpetas correctas
- Revisa la consola del navegador (F12) para errores JavaScript

## 📝 Notas Técnicas

- **Eel**: Framework que conecta Python con interfaces web
- **Responsive Design**: Compatible con móviles y tablets
- **Glassmorphism**: Efectos visuales modernos con transparencias
- **Debouncing**: Optimización de búsqueda en tiempo real
- **Error Handling**: Manejo robusto de errores y notificaciones

## 🤝 Contribuciones

Para contribuir al proyecto:
1. Haz fork del repositorio
2. Crea una rama para tu feature
3. Implementa los cambios
4. Prueba exhaustivamente
5. Envía un pull request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.