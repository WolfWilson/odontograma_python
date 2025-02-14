# 🦷 Odontograma Digital - Sistema de Registro Odontológico

![Licencia](https://img.shields.io/badge/Licencia-MIT-green.svg) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg) ![Framework](https://img.shields.io/badge/Framework-PyQt5-orange.svg) ![Status](https://img.shields.io/badge/Estado-Estable-success.svg)

Sistema interactivo para la representación de un **odontograma digital**, permitiendo el registro y visualización de **estados bucales** mediante selección manual o **parámetros desde línea de comandos**.

---
## 📌 **Características Principales**
✅ **Interfaz Gráfica** desarrollada en **PyQt5** con representación precisa de los dientes.  
✅ **Soporte para Parámetros** desde CLI para cargar estados automáticamente.  
✅ **Registro Completo de Estados Bucales** según nomenclatura FDI.  
✅ **Soporte para Dentición Permanente y Temporal**.  
✅ **Modo Manual y Automático** con visualización interactiva.  
✅ **Exportación de Datos y Reportes** *(futuro desarrollo)*.  

---

## 🚀 Instalación y Ejecución
### 🔹 Requisitos
- Python 3.12.5+
- PyQt5
- Flask/Django *(opcional para versión web)*
- argparse

### 🔹 Instalación

git clone https://github.com/tuusuario/odontograma-digital.git
cd odontograma-digital
pip install -r requirements.txt

###🔹 Ejecución en Modo Manual
    python odontrograma.py

###🔹 Ejecución con Parámetros (Modo Automático)
    python odontograma.py --credencial "123456" --titular "Carlos Pérez" --prestador "Dr. María López" --fecha "2025-02-10" --observaciones "Revisión general y tratamientos aplicados." --dientes "111,212V,313D,414MD,515O,616VI,717V,818,125,225,326,437,548,651,661,662,752,863,974,1085,1147,1245,1342,1341,135OLP,653,654,655"

✅ Esto aplicará automáticamente los estados especificados a los dientes correspondientes.

## 🛠 Procesamiento de Parámetros
### 📌 Parámetros Aceptados 

[![odonto-parametros.png](https://i.postimg.cc/J46VzcLG/odonto-parametros.png)](https://postimg.cc/PPwF6DNj)
--Validaciones antes de procesar
**Antes de aplicar los estados a los dientes, el código valida:**
- Formato correcto (Estado + Diente + Caras opcionales).
- Estado válido (de 1 a 13).
- Diente válido (de 11 a 85).
- Caras válidas (solo M, D, V, B, L, P, I, O, G)

## 🔍 Formato del Parámetro --dientes
        {ESTADO}{DIENTE}{CARAS opcionales}
    --dientes "325,126VI,327,428V"
[![odont-parametros-diente.png](https://i.postimg.cc/GpnMLHH4/odont-parametros-diente.png)](https://postimg.cc/4Ywvw4vG)

✔ Soporta múltiples estados en un solo diente.
✔ El Puente (estado 6) se dibuja individualmente en cada diente involucrado.

## 🎨 Representación Gráfica
Cada diente se dibuja con 5 caras poligonales:

- M (Mesial)
- D (Distal)
- V (Vestibular/Bucal)
- L (Lingual/Palatina)
- O/I (Oclusal o Incisal, según el diente)
[![pasted-Image.png](https://i.postimg.cc/pTSv1fL9/pasted-Image.png)](https://postimg.cc/KktC1gLF)

## *Identificacion de las caras de los dientes**

[![imagen-2025-02-14-114053727.png](https://i.postimg.cc/c4nx2bYd/imagen-2025-02-14-114053727.png)](https://postimg.cc/2VCNBT2t)

EJEMPLO DE LA VISUALIZACIÓN:
[![odontograma-Carlos-P-rez-2025-02-10.png](https://i.postimg.cc/g2FyR1d5/odontograma-Carlos-P-rez-2025-02-10.png)](https://postimg.cc/PPy8n3Cz)

###  Estados y su Representación Visual 
[![leyenda.png](https://i.postimg.cc/YqgnJ6C5/leyenda.png)](https://postimg.cc/zVzFhRW7)

###  🏗 Estructura del Código

> 📂 odontograma-digital/

│── 📄 odontograma.py  # Código principal
│── 📂 Modules/style.css #archivo de parámetros visuales de la app
│── 📂 src/  # Imágenes y capturas
│── 📂 templates/  # HTML para versión web (opcional)
│── 📄 requirements.txt  # Dependencias
│── 📄 README.md  # Documentación

### 🛠 Posibles Mejoras y Futuro Desarrollo 

✅ Integración con Base de Datos
✅ Versión Web-App con Flask/Django
✅ Exportación de datos a PDF / JSON
✅ Optimización de la carga de parámetros y manejo de errores

## 📸 Capturas de Pantalla 

[![odontograma-SIN-TITULAR-SIN-FECHA.png](https://i.postimg.cc/xdgLwCHD/odontograma-SIN-TITULAR-SIN-FECHA.png)](https://postimg.cc/5HYHvfnn)

##  🤝 Contribuciones 

¡Las contribuciones son bienvenidas!
Si quieres mejorar este proyecto:

- Fork el repositorio.
- Crea una nueva rama (feature-mejora).
- Realiza un pull request.

## 📜 Licencia 

Este proyecto está bajo la Licencia MIT, lo que significa que puedes usarlo y modificarlo libremente.

📌 Autor: Wilson Wolf / INSSSEP-CPI
📌 Repositorio: GitHub - **[odontrograma_python]

## 📬 Contacto 
📧 Email: wolfwilson1986@outlook.com
🌐 Sitio Web: https://github.com/WolfWilson


