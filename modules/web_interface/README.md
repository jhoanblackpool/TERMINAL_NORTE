# 🤖 Centro de Ejecución de Robots

Una aplicación web moderna para la gestión y ejecución de agentes automatizados, construida con Python (Eel) y tecnologías web modernas.

## ✨ Características Principales

- **🎯 Gestión Centralizada**: Visualiza y controla todos tus agentes desde una interfaz única
- **⚡ Ejecución en Tiempo Real**: Ejecuta agentes con feedback inmediato y monitoreo de estado
- **🔍 Búsqueda Avanzada**: Filtra agentes por nombre, área, estado y descripción
- **📊 Estadísticas Detalladas**: Monitorea rendimiento, tasa de éxito y tiempos de ejecución
- **🎨 Interfaz Moderna**: Diseño responsivo con soporte para modo oscuro y accesibilidad
- **🔒 Seguridad**: Confirmaciones para agentes críticos y validación de datos
- **📱 Responsive**: Funciona perfectamente en desktop, tablet y móvil
- **🌐 Offline Support**: Funcionalidad básica disponible sin conexión

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.8 o superior
- Navegador web moderno (Chrome, Firefox, Safari, Edge)

### Instalación

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/centro-robots.git
   cd centro-robots
   ```

2. **Crea un entorno virtual**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura la aplicación** (opcional)
   ```bash
   cp config.json.example config.json
   # Edita config.json según tus necesidades
   ```

5. **Ejecuta la aplicación**
   ```bash
   python app.py
   ```

6. **Abre tu navegador**
   - La aplicación se abrirá automáticamente en `http://localhost:8080`
   - Si no se abre automáticamente, navega manualmente a la URL

## 📁 Estructura del Proyecto

```
centro-robots/
├── app.py                  # Aplicación principal Python
├── config.json            # Configuración de la aplicación
├── requirements.txt        # Dependencias Python
├── README.md              # Este archivo
├── robot_center.log       # Logs de la aplicación
├── web/                   # Frontend web
│   ├── index.html         # Página principal
│   ├── script.js          # Lógica JavaScript
│   └── styles.css         # Estilos CSS
└── docs/                  # Documentación adicional
```

## ⚙️ Configuración

### Archivo config.json

```json
{
    "puerto": 8080,
    "modo_debug": false,
    "timeout_ejecucion": 30,
    "seguridad": {
        "confirmar_ejecucion_critica": true,
        "areas_criticas": ["Finanzas", "Legal"]
    }
}
```

### Variables de Entorno

Puedes usar variables de entorno para configuración sensible:

```bash
export ROBOT_CENTER_PORT=8080
export ROBOT_CENTER_DEBUG=false
export ROBOT_CENTER_SECRET_KEY=tu-clave-secreta
```

## 🎮 Uso de la Aplicación

### Panel de Control

1. **Búsqueda**: Usa la barra de búsqueda para encontrar agentes específicos
2. **Filtros**: Filtra por área (Finanzas, Operaciones, etc.) y estado (Activo, Inactivo)
3. **Vista**: Cambia entre vista de cuadrícula y lista
4. **Actualización**: Refresca los datos manualmente o automáticamente

### Gestión de Agentes

- **Ejecutar**: Haz clic en "Ejecutar" para iniciar un agente activo
- **Detalles**: Ve estadísticas completas, logs y dependencias
- **Estados**: Los agentes pueden estar Activos, En mantenimiento o Inactivos

### Atajos de Teclado

- `Ctrl + F`: Enfocar búsqueda
- `Ctrl + R`: Actualizar datos
- `Esc`: Cerrar modales
- `Tab`: Navegación por teclado

## 🔧 Desarrollo

### Configurar Entorno de Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar tests
pytest

# Formatear código
black .

# Verificar estilo
flake8

# Verificar tipos
mypy app.py
```

### Estructura de Código

- **Backend** (`app.py`): API Python con Eel, validación y logs
- **Frontend** (`web/`): HTML5, CSS3 moderno, JavaScript ES6+
- **Configuración**: JSON para configuración, logging estructurado

### Agregar Nuevos Agentes

1. Modifica `agentes_data` en `app.py`
2. Agrega la lógica de ejecución específica
3. Actualiza tests y documentación

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=app

# Tests específicos
pytest tests/test_agentes.py

# Tests de interfaz (requiere Selenium)
pytest tests/test_ui.py
```

## 📦 Construcción y Despliegue

### Crear Ejecutable

```bash
# Generar ejecutable con PyInstaller
pyinstaller --onefile --windowed app.py

# El ejecutable estará en dist/
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "app.py"]
```

### Despliegue en Servidor

1. **Nginx + uWSGI** para producción
2. **Systemd service** para auto-inicio
3. **SSL/TLS** con Let's Encrypt
4. **Monitoreo** con logs centralizados

## 🔒 Seguridad

- ✅ Validación de entrada en backend
- ✅ Escape de HTML para prevenir XSS
- ✅ Confirmaciones para operaciones críticas
- ✅ Logs de auditoría completos
- ✅ Timeouts de sesión configurables

## 🎨 Personalización

### Temas

Modifica `styles.css` para personalizar:
- Colores de marca
- Fuentes corporativas
- Espaciado y layout
- Animaciones

### Funcionalidad

Extiende `script.js` para:
- Nuevas funciones de filtrado
- Integraciones con APIs externas
- Notificaciones personalizadas
- Dashboards adicionales

## 🐛 Solución de Problemas

### Problemas Comunes

**❌ Error: Puerto en uso**
```bash
# Cambiar puerto en config.json o matar proceso
lsof -ti:8080 | xargs kill -9
```

**❌ Agentes no cargan**
- Verificar logs en `robot_center.log`
- Revisar configuración de base de datos
- Comprobar permisos de archivos

**❌ Interfaz no responde**
- Limpiar caché del navegador
- Verificar JavaScript en consola del navegador
- Comprobar conexión a internet

### Logs y Debugging

```bash
# Ver logs en tiempo real
tail -f robot_center.log

# Activar modo debug
# En config.json: "modo_debug": true

# Logs detallados
export PYTHONPATH=. && python -m logging.basicConfig level=DEBUG
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Guías de Contribución

- Sigue PEP 8 para Python
- Usa ESLint para JavaScript
- Agrega tests para nuevas funcionalidades
- Actualiza documentación
- Mantén commits atómicos y descriptivos

## 📝 Changelog

### v2.1.0 (Actual)
- ✨ Sistema de notificaciones toast mejorado
- 🔧 Modal funcional para detalles de agentes
- 🎨 Mejoras de accesibilidad y responsive
- 🐛 Corrección de filtros y debounce
- 📊 Estadísticas detalladas de agentes
- 🔒 Validación robusta de entrada

### v2.0.0
- 🎉 Interfaz completamente rediseñada
- ⚡ Migración a Eel framework
- 📱 Soporte responsive completo
- 🔍 Sistema de búsqueda mejorado

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👥 Equipo

- **Desarrollador Principal**: Tu Nombre (@tu-usuario)
- **UI/UX**: Diseñador UI
- **DevOps**: Especialista DevOps

## 📞 Soporte

- 📧 **Email**: soporte@empresa.com
- 💬 **Chat**: [Slack/Teams]
- 🐛 **Issues**: [GitHub Issues](https://github.com/tu-usuario/centro-robots/issues)
- 📖 **Docs**: [Documentación Completa](https://docs.empresa.com/centro-robots)

---

**⭐ Si este proyecto te resulta útil, no olvides darle una estrella en GitHub!**