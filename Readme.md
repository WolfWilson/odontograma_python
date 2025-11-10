# 🦷 Odontograma Digital - Sistema de Visualización Odontológica

![Licencia](https://img.shields.io/badge/Licencia-MIT-green.svg) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg) ![Framework](https://img.shields.io/badge/Framework-PyQt5-orange.svg) ![Database](https://img.shields.io/badge/Database-SQL%20Server-red.svg) ![Status](https://img.shields.io/badge/Estado-Producción-success.svg)

Sistema profesional de visualización de **odontogramas digitales** integrado con SQL Server, diseñado para auditoría y consulta de estados bucales históricos de pacientes. Desarrollado para INSSSEP-CPI.

---

## 📌 **Características Principales**

✅ **Conexión a SQL Server** con auto-detección de drivers ODBC  
✅ **Visualización de Odontogramas Históricos** desde base de datos  
✅ **Interfaz Gráfica PyQt5** con representación precisa de 52 piezas dentales  
✅ **Sistema Dual de Prestaciones**: Existentes (rojas) y Requeridas (azules)  
✅ **Nomenclatura FDI Internacional** para dentición permanente y temporal  
✅ **Diseño Responsivo** adaptable a resoluciones bajas (1366×768)  
✅ **Captura de Pantalla** con exportación a PNG  
✅ **Splash Screen Animado** durante carga de datos  
✅ **Instancia Única** (previene múltiples ejecuciones)  

---

---

## 🚀 Instalación y Configuración

### � Requisitos del Sistema

- **Python**: 3.12.5 o superior
- **Sistema Operativo**: Windows (requerido para conexión a SQL Server)
- **Base de Datos**: SQL Server con acceso a servidor `Concentrador` o `concentrador-desarrollo`
- **Drivers ODBC**: Al menos uno de los siguientes:
  - SQL Server
  - SQL Server Native Client 11.0
  - SQL Server Native Client 10.0

### � Instalación

```powershell
# Clonar el repositorio
git clone https://github.com/WolfWilson/odontograma_python.git
cd odontograma_python

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### ▶️ Ejecución

**Parámetros requeridos**:
```powershell
python odontograma.py <credencial> <fecha> <efectorNombre> <colegio> <efectorCodFact>
```

**Ejemplo**:
```powershell
python odontograma.py 354495 "30/07/2025" "ODONTOLOGO DE PRUEBA COCH" 3 333
```

**Script de prueba** (`run_test.bat`):
```batch
@echo off
set CREDENCIAL=354495
set FECHA=14/07/2025
set EFECTOR_NOMBRE=ODONTOLOGO DE PRUEBA COCH
set COLEGIO=3
set EFECTOR_COD_FACT=333

python odontograma.py %CREDENCIAL% %FECHA% %EFECTOR_NOMBRE% %COLEGIO% %EFECTOR_COD_FACT%
pause
```

---

## �️ Conexión a Base de Datos

### Stored Procedures

El sistema consulta dos procedimientos almacenados:

1. **`[dbo].[odo_boca_consulta_efector]`**
   - **Entrada**: `idafiliado, colegio, codfact, fecha`
   - **Salida**: Lista de registros históricos (idboca, fechacarga, resumenclinico)

2. **`[dbo].[odo_buscaParametrosEstadoBoca]`**
   - **Entrada**: `idboca`
   - **Salida**: Datos completos del odontograma (credencial, afiliado, prestador, fecha, observaciones, **dientes**)

### Formato del Campo `dientes`

El sistema parsea un string CSV del formato:
```
"155,117OV,1418M,1555,..."
```

**Estructura**: `{ESTADO}{DIENTE}{CARAS}`

- **ESTADO**: 1-2 dígitos (códigos 1-19)
- **DIENTE**: últimos 2 dígitos (11-85 según FDI)
- **CARAS**: letras opcionales (M, D, V, B, L, P, I, O)

**Ejemplos**:
- `155` → Estado 1 (Obturación), Diente 55, Sin caras específicas
- `117OV` → Estado 1, Diente 17, Caras Oclusal y Vestibular
- `1418M` → Estado 14 (Extracción), Diente 18, Cara Mesial

### Validaciones

El parser valida:
- ✅ Estado en rango 1-19
- ✅ Diente válido según nomenclatura FDI (11-85)
- ✅ Caras dentales correctas (M, D, V, B, L, P, I, O)

---

## 🦷 Estados Dentales Soportados

### Códigos de Estado (1-19)

| Código | Estado | Color | Descripción |
|--------|--------|-------|-------------|
| 0 | Ninguno | - | Estado limpio |
| 1 | Obturación | Rojo | Relleno dental |
| 2 | Agenesia | Gris | Ausencia congénita |
| 3 | PD Ausente | Cruz Roja | Pieza dental ausente |
| 4 | Corona | Círculo Rojo | Corona dental |
| 5 | Implante | "IMP" Rojo | Implante |
| 6 | Puente | Línea Roja | Puente dental |
| 7 | Selladores | Punto Rojo | Selladores |
| 8 | Ausente Fisiológico | Círculo Punteado | No erupcionado |
| 9-12 | Prótesis _R | PRS/PRI/PCS/PCI Rojo | Prótesis existentes |
| 13 | Caries | Azul | Caries dental |
| 14 | Extracción | Cruz Roja (gruesa) | Extracción indicada |
| 15-18 | Prótesis _B | PRS/PRI/PCS/PCI Azul | Prótesis requeridas |

### Caras Dentales

Cada pieza dental se representa con **5 caras poligonales**:

- **M** (Mesial): Cara hacia el centro de la boca
- **D** (Distal): Cara hacia el final de la arcada
- **V/B** (Vestibular/Bucal): Cara externa (labios/mejillas)
- **L/P** (Lingual/Palatina): Cara interna (lengua/paladar)
- **O/I** (Oclusal/Incisal): Cara de masticación/borde

[![pasted-Image.png](https://i.postimg.cc/pTSv1fL9/pasted-Image.png)](https://postimg.cc/KktC1gLF)

### Identificación de Caras

[![imagen-2025-02-14-114053727.png](https://i.postimg.cc/c4nx2bYd/imagen-2025-02-14-114053727.png)](https://postimg.cc/2VCNBT2t)

---

## 🖼️ Capturas de Pantalla

### Odontograma con Datos de Paciente
[![odontograma-Carlos-P-rez-2025-02-10.png](https://i.postimg.cc/g2FyR1d5/odontograma-Carlos-P-rez-2025-02-10.png)](https://postimg.cc/PPy8n3Cz)

### Leyenda de Estados
[![leyenda.png](https://i.postimg.cc/YqgnJ6C5/leyenda.png)](https://postimg.cc/zVzFhRW7)

### Vista sin Paciente
[![odontograma-SIN-TITULAR-SIN-FECHA.png](https://i.postimg.cc/xdgLwCHD/odontograma-SIN-TITULAR-SIN-FECHA.png)](https://postimg.cc/5HYHvfnn)

---

## 🏗️ Estructura del Proyecto

```
odontograma_python/
├── odontograma.py              # Punto de entrada (launcher)
├── requirements.txt            # Dependencias Python
├── run_test.bat               # Script de prueba
├── CONTEXT.md                 # Documentación técnica detallada
│
├── Modules/                   # Módulos principales
│   ├── conexion_db.py         # Gestión de conexiones SQL Server
│   ├── views.py               # Ventana principal (MainWindow)
│   ├── modelos_sin_imagenes.py # Vista del odontograma (QGraphicsView)
│   ├── menu_estados.py        # Panel lateral de estados
│   ├── menubox_prest.py       # Construcción de menús
│   └── utils.py               # Constantes y utilidades
│
├── Utils/                     # Utilidades auxiliares
│   ├── loading_img.py         # Splash screen animado
│   ├── actions.py             # Captura de pantalla
│   ├── sp_data_parse.py       # Parseo de datos del SP
│   └── center_window.py       # Centrado de ventanas
│
├── Styles/                    # Estilos visuales
│   ├── style.py               # Hoja de estilos QSS escalable
│   ├── style_models.py        # Paleta de colores
│   └── animation.py           # Animaciones
│
├── src/                       # Recursos (iconos, imágenes)
│   ├── icon_*.png             # Iconos de estados
│   ├── teeth.gif              # Animación de carga
│   └── odontograma.ico        # Ícono de la aplicación
│
└── Captures/                  # Capturas guardadas (generado)
```

---

## 🔧 Características Técnicas

### Interfaz de Usuario

- **Framework**: PyQt5 con QGraphicsView para renderizado vectorial
- **Escalado Responsivo**: Auto-detección de resoluciones bajas (factor 0.80)
- **Singleton**: Una sola instancia en ejecución (QSharedMemory)
- **Splash Screen**: GIF animado durante carga de datos

### Base de Datos

- **Motor**: Microsoft SQL Server
- **Conexión**: pyodbc con auto-detección de drivers
- **Cache**: LRU cache para drivers validados
- **Servidores**: 
  - Producción: `Concentrador/Prestacion`
  - Desarrollo: `concentrador-desarrollo/Prestacion`

### Renderizado

- **Piezas Dentales**: 52 (32 permanentes + 20 temporales)
- **Caras por Diente**: 5 polígonos (M, D, V, L, O/I)
- **Estados Visuales**: 19 códigos diferentes
- **Overlays**: Corona, implante, prótesis, puentes

---

## 🛠️ Compilación para Producción

### PyInstaller

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

**Notas importantes**:
- `--noconsole`: Oculta la consola en Windows
- `--hidden-import pyodbc`: Incluye módulo de base de datos
- `--add-data 'src;src'`: Empaqueta recursos (iconos, imágenes)
- `--distpath`: Ruta de red para distribución

---

## 🚀 Roadmap de Mejoras

### ✅ Completado

- [x] Integración con SQL Server
- [x] Sistema dual de prestaciones (rojas/azules)
- [x] Escalado responsivo
- [x] Captura de pantalla
- [x] Splash screen animado

### 🔄 En Desarrollo

- [ ] Exportación a PDF con reportes
- [ ] Historial de cambios por paciente
- [ ] Comparativa visual entre fechas

### 📋 Planificado

- [ ] Modo de edición con guardado en BD
- [ ] Búsqueda avanzada y estadísticas
- [ ] Sistema de notas por diente
- [ ] Integración con imágenes radiográficas

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar este proyecto:

1. **Fork** el repositorio
2. Crea una rama con tu feature (`git checkout -b feature/mejora-increible`)
3. Commit tus cambios (`git commit -m 'Añade mejora increíble'`)
4. Push a la rama (`git push origin feature/mejora-increible`)
5. Abre un **Pull Request**

### Áreas de Contribución

- 🐛 Reporte de bugs
- 💡 Sugerencias de funcionalidades
- 📝 Mejoras en documentación
- 🎨 Diseño de iconos y UI
- 🧪 Tests unitarios

---

## 📜 Licencia

Este proyecto está bajo la **Licencia MIT**. Puedes usarlo y modificarlo libremente con atribución.

```
MIT License

Copyright (c) 2025 Wilson Wolf - INSSSEP-CPI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## � Equipo de Desarrollo

**Desarrollador Principal**  
👤 **Wilson Wolf**  
🏢 INSSSEP-CPI  
� wolfwilson1986@outlook.com  
🌐 [GitHub](https://github.com/WolfWilson)

**Colaboradora**  
👤 **Antonella Bouvier**  
🌐 [@antobouvier](https://github.com/antobouvier)

---

## 📚 Documentación Adicional

- 📄 **[CONTEXT.md](./CONTEXT.md)**: Documentación técnica detallada
- � **Repositorio**: [github.com/WolfWilson/odontograma_python](https://github.com/WolfWilson/odontograma_python)
- 📊 **Issues**: [github.com/WolfWilson/odontograma_python/issues](https://github.com/WolfWilson/odontograma_python/issues)

---

## � Agradecimientos

- **INSSSEP-CPI** por el apoyo institucional
- Comunidad de **PyQt5** por la documentación
- **FDI World Dental Federation** por la nomenclatura internacional

---

<div align="center">

**⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub ⭐**

Hecho con ❤️ para la comunidad odontológica

</div>


