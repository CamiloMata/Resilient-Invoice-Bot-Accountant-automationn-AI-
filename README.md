🤖 **Resilient Invoice Bot: Automatización Contable con IA**

📄 *Resumen Ejecutivo*
Resilient Invoice Bot es una herramienta de automatización inteligente diseñada para liberar a los equipos contables y administrativos de la entrada manual de datos.

Este sistema actúa como un asistente digital 24/7 que monitorea una cuenta de correo electrónico, descarga facturas (en PDF o XML/ZIP), lee su contenido utilizando Inteligencia Artificial (Google Gemini) y transfiere automáticamente la información clave (NIT, Fechas, Valores, CUFE) a un archivo de Excel en tiempo real.

🎯 *¿Para quién es este proyecto?*
Contadores y Auxiliares: Para eliminar la digitación repetitiva y reducir errores humanos.

Gerentes de Operaciones: Para agilizar el flujo de cuentas por pagar.

Desarrolladores Junior: Como ejemplo práctico de integración entre APIs de correo, IA Generativa y manipulación de archivos.

👁️ *Flujo de trabajo del bot*

graph TD
    
    %% Nodos (Pasos del proceso)
    User([👤 Usuario / Proveedor]) -->|Envía Factura PDF/ZIP| Email[📧 Bandeja de Entrada]
    Email -->|El Bot detecta correo| Check{❓ ¿Tiene Adjuntos?}
    
    Check -- No --> Ignore[🗑️ Ignorar Correo]
    Check -- Sí --> Process[⚙️ Procesar Archivo]
    
    Process -->|Envía texto a| AI[🧠 Inteligencia Artificial\n(Google Gemini)]
    AI -->|Extrae Datos| Data[📝 Datos: NIT, Valor, Fecha]
    
    Data -->|Escribe fila| Excel[(📗 Archivo Excel\nContabilidad)]
    
    %% Estilos para hacerlo amigable
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style AI fill:#bbf,stroke:#333,stroke-width:2px
    style Excel fill:#bfb,stroke:#333,stroke-width:2px

    +-----------------+       +--------------------+       +------------------+
|   PASO 1:       |       |     PASO 2:        |       |    PASO 3:       |
|   ENTRADA       |       |     PROCESO        |       |    SALIDA        |
+-----------------+       +--------------------+       +------------------+
|                 |       |                    |       |                  |
|  [ Proveedor ]  |       |   [ Bot de IA ]    |       |   [ Reporte ]    |
|        |        |       |         |          |       |        |         |
|  Envia Correo   +-----> |  Lee y Analiza     +-----> |  Guarda en Excel |
|  con Factura    |       |  con Google Gemini |       |  Automáticamente |
|                 |       |                    |       |                  |
+-----------------+       +--------------------+       +------------------+

⚙️ *¿Cómo Funciona? (Visión General)*
Imagina un empleado infatigable que nunca duerme. El proceso que sigue el bot es el siguiente:

Escucha: Se conecta a tu correo electrónico y espera nuevos mensajes.

Identifica: Detecta si el correo tiene adjuntos válidos (Facturas PDF o XML comprimidos).

Analiza (El Cerebro): Envía el texto de la factura a la IA de Google Gemini, pidiéndole que actúe como un "Analista Contable" y extraiga datos específicos.

Escribe: Guarda la información organizada en tu archivo Excel de control.

Repite: Vuelve a esperar el siguiente correo.

🔄*Flujo de Trabajo (Workflow)*

graph TD
    A[📩 Nuevo Correo con Factura] -->|Detectar Adjunto| B(📥 Descargar PDF/ZIP)
    B --> C{📄 ¿Es legible?}
    C -- No --> D[❌ Ignorar / Log de Error]
    C -- Sí --> E[🧠 Análisis con Gemini AI]
    E -->|Extraer JSON| F[📊 Datos Estructurados: NIT, Valor, Fecha]
    F --> G[💾 Guardar en Excel]
    G --> H[✅ Proceso Terminado]

🚀 *Guía de Uso Paso a Paso*
Si el sistema ya está configurado, tu interacción diaria es muy sencilla. Sigue estos pasos para procesar tus facturas:

1. Prepara tu Factura
Asegúrate de tener el archivo de la factura electrónica. El sistema acepta:

Archivos PDF: Facturas digitales normales.

Archivos ZIP: Carpetas comprimidas que contienen el XML o PDF de la factura (común en facturación electrónica en Colombia).

2. Envía el Correo
Envía un correo electrónico a la dirección configurada (ej. tu.auxiliar.bot@gmail.com) con la factura adjunta.

Asunto: Puede ser cualquiera, pero se recomienda poner el nombre del proveedor para tu referencia (el bot guardará el asunto en el Excel).

Adjunto: No olvides adjuntar el archivo.

3. El Bot Procesa
El sistema leerá el correo (usualmente cada 15 segundos), extraerá la información y la validará.

4. Verifica el Excel
Abre tu archivo de Excel (ej. Facturas_pruebas.xlsx). Verás una nueva fila con:

Fecha de emisión

NIT y Nombre del emisor

Total a pagar

Número de factura y CUFE

Fechas de vencimiento

⚠️ Nota Importante: Para que el bot pueda escribir en el Excel, el archivo debe estar cerrado en tu computadora si no usas Excel compartido en la nube. Si lo tienes abierto y bloqueado, el bot reportará un error y no guardará los datos.

📂 *Estructura del Repositorio*
A continuación, explicamos qué hace cada archivo para que entiendas la "anatomía" del proyecto:

| Archivo	          | Descripción
app.py	              El Cerebro. Contiene todo el código lógico: conexión al correo, instrucciones para la IA y guardado en Excel.
data.env	          Las Llaves. Archivo de configuración donde guardas tus contraseñas y rutas de forma segura.                 (No compartir este archivo).
invoice_bot_errors.log La Caja Negra. Un archivo de texto que registra todo lo que hace el bot y reporta si hubo errores.
requirements.txt	    Lista de librerías necesarias para que el bot funcione (se genera con pip freeze).


🛠️ *Requisitos Previos y Configuración Técnica*
Si vas a instalar este bot desde cero, necesitas lo siguiente:

1. Entorno
Python 3.9 o superior instalado en tu sistema.

Una cuenta de Google Cloud con acceso a la API de Gemini (es gratuita para bajo volumen).

Una cuenta de correo (Gmail recomendado) con Contraseña de Aplicación habilitada (IMAP activado).

2. Instalación de Librerías
Abre tu terminal y ejecuta:

pip install google-generativeai imap-tools openpyxl pdfplumber python-dotenv

3. Configuración del archivo .env
Crea un archivo llamado data.env en la misma carpeta del script y complétalo con tus datos reales:

# data.env
EMAIL_USER=tu_correo@gmail.com
**¡OJO! No es tu contraseña normal, es una "Contraseña de Aplicación" de 16 caracteres**
EMAIL_PASS=xxxx xxxx xxxx xxxx 
GEMINI_API_KEY=AIzaSyD... (Tu llave de API de Google) 
EXCEL_FILE_PATH=C:/Ruta/A/Tu/Archivo/Facturas.xlsx
EXCEL_SHEET_NAME=NombreDeLaPestaña

❓ *Solución de Problemas Comunes (Troubleshooting)*
Aquí listamos los errores más frecuentes y cómo solucionarlos sin conocimientos técnicos profundos:

🔴 Error: "El archivo Excel está abierto"
Síntoma: El bot dice que procesó la factura pero no aparece en el Excel. En el log aparece PermissionError.

Solución: Cierra el archivo Excel en tu computadora y vuelve a enviar la factura o espera al siguiente ciclo.

🔴 Error: "No se pudo extraer texto legible"
Síntoma: El bot ignora el correo.

Causa: Probablemente enviaste una factura escaneada (como una foto dentro de un PDF) que no tiene texto seleccionable.

Solución: Pide a tu proveedor la factura electrónica original (PDF digital o XML). Este bot no usa OCR de imágenes, solo extracción de texto.

🔴 Error: "Respuesta vacía de la IA"
Síntoma: El bot falla al analizar.

Causa: La IA de Google puede haber bloqueado el contenido por seguridad o tuvo un "hipo" temporal.

Solución: El bot está diseñado para ser "Resiliente". Simplemente reenvía el correo unos minutos después.

🛡️ *Buenas Prácticas y Mantenimiento*
Seguridad: Nunca subas tu archivo data.env a GitHub o compartas tus claves API públicamente.

Limpieza: Revisa el archivo invoice_bot_errors.log una vez a la semana para asegurar que todo marcha bien.

Volumen: Este bot usa la versión gratuita de Gemini Flash. Tiene límites de velocidad. El script incluye pausas automáticas para evitar bloqueos, pero evita enviar 100 correos en un solo minuto.

📞 Soporte
Si encuentras un error crítico ("ERROR NO CONTROLADO" en los logs), por favor contacta al equipo de desarrollo con una copia del archivo invoice_bot_errors.log para diagnóstico.





