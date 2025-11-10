# CONTEXT.md - Contexto Técnico del Proyecto Odontograma

> **Propósito**: Este archivo proporciona contexto técnico detallado del sistema para facilitar futuras mejoras y mantenimiento.

---

## 📋 Resumen del Proyecto

**Odontograma Digital** es una aplicación de escritorio desarrollada en PyQt5 que permite visualizar y gestionar estados bucales de pacientes. El sistema se conecta a SQL Server para obtener datos de odontogramas históricos y permite visualizar estados existentes y requeridos de tratamientos dentales.

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
odontograma.py                 # Punto de entrada (launcher)
├── Modules/
│   ├── conexion_db.py         # Gestión de conexiones SQL Server
│   ├── views.py               # Ventana principal (MainWindow)
│   ├── modelos_sin_imagenes.py # Vista del odontograma (QGraphicsView)
│   ├── menu_estados.py        # Panel lateral de estados
│   ├── menubox_prest.py       # Construcción de menús de prestaciones
│   └── utils.py               # Constantes y utilidades globales
├── Utils/
│   ├── loading_img.py         # Splash screen animado
│   ├── actions.py             # Captura de pantalla del odontograma
│   ├── sp_data_parse.py       # Parseo de datos del SP
│   └── center_window.py       # Utilidad de centrado
├── Styles/
│   ├── style.py               # Hoja de estilos QSS escalable
│   ├── style_models.py        # Paleta de colores
│   └── animation.py           # Animaciones de botones
└── src/                       # Recursos (iconos, imágenes, GIF)
```

---

## 🔌 Conexión a Base de Datos

### Estrategia de Drivers ODBC

**Archivo**: `Modules/conexion_db.py`

El sistema implementa una estrategia de **auto-detección y fallback** de drivers ODBC:

1. **Lista Priorizada**: Se definen drivers preferidos en orden:
   ```python
   _PREFERRED_ORDER = (
       "SQL Server",
       "SQL Server Native Client 11.0",
       "SQL Server Native Client 10.0",
   )
   ```

2. **Auto-detección**: El sistema detecta drivers instalados y prueba solo los de la lista preferida
3. **Cache**: Usa `@lru_cache` para evitar múltiples pruebas de conexión
4. **Variable de entorno**: Permite forzar un driver específico con `SQL_DRIVER`

### Stored Procedures Utilizados

1. **`[dbo].[odo_boca_consulta_efector]`**
   - Parámetros: `idafiliado, colegio, codfact, fecha`
   - Retorna: Lista de bocas registradas con `idboca`, `fechacarga`, `resumenclinico`

2. **`[dbo].[odo_buscaParametrosEstadoBoca]`**
   - Parámetros: `idboca`
   - Retorna: Datos completos del odontograma (credencial, afiliado, prestador, fecha, observaciones, **dientes**)

### Servidores Configurados

- **Producción**: `Concentrador` → Base de datos `Prestacion`
- **Desarrollo**: `concentrador-desarrollo` → Base de datos `Prestacion`

---

## 🦷 Sistema de Estados Dentales

### Códigos de Estado (0-19)

**Archivo**: `Modules/utils.py`

```python
ESTADOS = {
    "Ninguno": 0,
    "Obturacion": 1,              # Relleno dental
    "Agenesia": 2,                # Ausencia congénita
    "PD Ausente": 3,              # Pieza dental ausente
    "Corona": 4,                  # Corona dental
    "Implante": 5,                # Implante
    "Puente": 6,                  # Puente dental
    "Selladores": 7,              # Selladores
    "Ausente Fisiológico": 8,     # No erupcionado aún
    
    # Prótesis ROJAS (existentes)
    "Prótesis Removible SUPERIOR_R": 9,
    "Prótesis Removible INFERIOR_R": 10,
    "Prótesis Completa SUPERIOR_R": 11,
    "Prótesis Completa INFERIOR_R": 12,
    
    "Caries": 13,                 # Caries dental
    "Extracción": 14,             # Extracción indicada
    
    # Prótesis AZULES (requeridas)
    "Prótesis Removible SUPERIOR_B": 15,
    "Prótesis Removible INFERIOR_B": 16,
    "Prótesis Completa SUPERIOR_B": 17,
    "Prótesis Completa INFERIOR_B": 18,
}
```

### Formato de Datos del SP

**Archivo**: `Utils/sp_data_parse.py`

El campo `dientes` del SP viene como string CSV:
```
"155,117OV,1418M,1555,..."
```

**Formato**: `{ESTADO}{DIENTE}{CARAS}`

- **ESTADO**: 1-2 dígitos (1-19)
- **DIENTE**: últimos 2 dígitos (11-85)
- **CARAS**: letras opcionales (M, D, V, B, L, P, I, O)

**Ejemplo**:
- `155` → Estado 1, Diente 55, Sin caras específicas
- `117OV` → Estado 1, Diente 17, Caras Oclusal y Vestibular
- `1418M` → Estado 14, Diente 18, Cara Mesial

### Nomenclatura FDI

El sistema usa la **nomenclatura FDI** (Fédération Dentaire Internationale):

**Dentición Permanente**:
- Cuadrante 1 (superior derecho): 11-18
- Cuadrante 2 (superior izquierdo): 21-28
- Cuadrante 3 (inferior izquierdo): 31-38
- Cuadrante 4 (inferior derecho): 41-48

**Dentición Temporal (Decidua)**:
- Cuadrante 5 (superior derecho): 51-55
- Cuadrante 6 (superior izquierdo): 61-65
- Cuadrante 7 (inferior izquierdo): 71-75
- Cuadrante 8 (inferior derecho): 81-85

---

## 🎨 Sistema de Renderizado

### Arquitectura de Vistas

**Archivo**: `Modules/modelos_sin_imagenes.py`

1. **OdontogramView** (QGraphicsView)
   - Contenedor principal de la escena gráfica
   - Maneja zoom y transformaciones
   - Coordina actualizaciones de estados

2. **ToothItem**
   - Representa una pieza dental completa
   - Contiene 5 caras poligonales (M, D, V, L, O/I)
   - Gestiona overlays (corona, implante, prótesis, etc.)
   - Mantiene listas independientes de prótesis rojas y azules

3. **ToothFacePolygon** (QGraphicsPolygonItem)
   - Representa una cara individual del diente
   - Maneja eventos de clic para estados interactivos

### Sistema de Caras Dentales

```python
FACE_MAP = {
    "M": "left",      # Mesial
    "D": "right",     # Distal
    "V": "top",       # Vestibular/Bucal
    "B": "top",       # Bucal (alias)
    "L": "bottom",    # Lingual
    "P": "bottom",    # Palatina (alias)
    "I": "center",    # Incisal
    "O": "center",    # Oclusal
}
```

### Escalado Responsivo

**Archivos**: `Modules/views.py`, `Styles/style.py`

El sistema detecta resoluciones bajas (≤ 1366×768) y aplica un factor de escala de **0.80**:

- Ventana principal
- Fuentes
- Iconos
- QGraphicsView (transformación de la escena)
- Paddings y márgenes

---

## 🎯 Flujo de Datos

### 1. Inicio de la Aplicación

```
odontograma.py (main)
  ↓
  ├─ Parseo de argumentos CLI (credencial, fecha, efectorNombre, colegio, efectorCodFact)
  ├─ Splash screen animado (teeth.gif)
  ├─ Consulta BD → get_bocas_consulta_efector()
  └─ MainWindow(data) → Ventana principal
```

### 2. Carga de Odontograma

```
MainWindow._on_boca_seleccionada(row, col)
  ↓
  ├─ Obtener idboca de la tabla
  ├─ get_odontograma_data(idboca) → SP
  ├─ Actualizar header (credencial, afiliado, prestador, etc.)
  ├─ parse_dientes_sp(dientes_str) → [(estado, diente, caras), ...]
  └─ OdontogramView.apply_batch_states(states)
       ↓
       ├─ Reset de todos los dientes
       ├─ Aplicar estados por diente
       └─ update_bridges() → renderizar puentes
```

### 3. Filtros de Visualización

- **Todos**: Muestra todos los estados
- **Solo Existentes**: Oculta prótesis azules, caries y extracciones
- **Solo Requeridas**: Muestra únicamente prótesis azules, caries y extracciones

---

## 🔧 Configuración y Build

### Entorno Virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Dependencias Principales

```
PyQt5==5.15.11
PyQt5-Qt5==5.15.2
PyQt5_sip==12.16.0
pyodbc
```

### Compilación con PyInstaller

```powershell
pyinstaller --onefile --noconsole `
  --icon 'src/odontograma.ico' `
  --distpath '\\fs01\Aut_Dentisteria\exe test' `
  --add-data 'src;src' `
  --collect-submodules Modules `
  --collect-submodules Utils `
  --collect-submodules Styles `
  --hidden-import pyodbc `
  odontograma.py
```

**Nota**: El flag `--hidden-import pyodbc` es crítico para incluir el módulo de base de datos.

---

## 🐛 Problemas Conocidos y Soluciones

### 1. Error Intermitente de Conexión

**Síntoma**: `ConnectionError: Ningún driver ODBC válido`

**Causa**: El sistema intentaba probar drivers no estables en orden aleatorio.

**Solución Implementada**: 
- La función `_ordered_drivers()` ahora solo usa drivers de `_PREFERRED_ORDER`
- Se eliminó la inclusión de "otros drivers" que causaban inestabilidad

### 2. Singleton de Aplicación

**Implementación**: Se usa `QSharedMemory` para garantizar una sola instancia:

```python
_shared = QSharedMemory("OdontogramaSingletonKey")
if not _shared.create(1):
    print("Ya hay otra instancia en ejecución.")
    sys.exit(0)
```

### 3. Gestión de Prótesis Múltiples

**Desafío**: Un diente puede tener múltiples prótesis (rojas y azules).

**Solución**:
- `ToothItem` mantiene dos listas: `labels_red` y `labels_blue`
- Las etiquetas azules se renderizan por encima de las rojas
- No se eliminan etiquetas previas (acumulativas)

---

## 📊 Métricas del Proyecto

- **Líneas de código**: ~2,500 líneas (sin comentarios)
- **Módulos principales**: 15
- **Estados dentales soportados**: 19
- **Iconos de recursos**: 30+
- **Piezas dentales**: 52 (32 permanentes + 20 temporales)

---

## 🚀 Roadmap de Mejoras Futuras

### Prioridad Alta

1. **Exportación a PDF**
   - Generar reportes PDF con el odontograma y datos del paciente
   - Librería sugerida: `reportlab` o `PyQt5.QtPrintSupport`

2. **Historial de Cambios**
   - Implementar versionado de odontogramas
   - Comparativa visual entre fechas

3. **Validaciones de Integridad**
   - Alertas de estados incompatibles
   - Validación de tratamientos lógicos

### Prioridad Media

4. **Modo de Edición**
   - Permitir modificar estados y guardar en BD
   - Auditoría de cambios (quién, cuándo, qué)

5. **Búsqueda Avanzada**
   - Filtros por fecha, prestador, estado
   - Estadísticas de tratamientos

6. **Notas y Comentarios**
   - Sistema de anotaciones por diente
   - Integración con observaciones generales

### Prioridad Baja

7. **Versión Web**
   - Migración a Flask/Django
   - Interfaz responsive para tablets

8. **Integración con Escáneres**
   - Importar imágenes de radiografías
   - Overlay de imágenes sobre odontograma

---

## 📚 Referencias Técnicas

### Documentación PyQt5

- [QGraphicsView](https://doc.qt.io/qt-5/qgraphicsview.html)
- [QGraphicsScene](https://doc.qt.io/qt-5/qgraphicsscene.html)
- [Stylesheets (QSS)](https://doc.qt.io/qt-5/stylesheet-reference.html)

### SQL Server

- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [Connection Strings](https://www.connectionstrings.com/sql-server/)

### Nomenclatura Dental

- [FDI World Dental Federation](https://www.fdiworlddental.org/)
- [Sistema de Nomenclatura FDI](https://es.wikipedia.org/wiki/Sistema_de_nomenclatura_dental)

---

## 👥 Colaboradores y Mantenimiento

**Desarrollador Principal**: Wilson Wolf (INSSSEP-CPI)  
**Colaboradora**: Antonella Bouvier [@antobouvier](https://github.com/antobouvier)  
**Repositorio**: [github.com/WolfWilson/odontograma_python](https://github.com/WolfWilson/odontograma_python)

---

## 📝 Notas de Versión

### v2.0 (Actual)
- ✅ Sistema de prótesis dual (rojas/azules)
- ✅ Escalado responsivo
- ✅ Conexión estable a SQL Server
- ✅ Splash screen animado
- ✅ Captura de pantalla

### v1.0 (Histórica)
- Implementación inicial
- Soporte básico de estados
- Interfaz fija

---

**Última actualización**: Noviembre 2025
