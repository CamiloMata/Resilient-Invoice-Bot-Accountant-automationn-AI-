import os
import json
import logging
import io
import time
import zipfile
import pdfplumber
import openpyxl
import re
import concurrent.futures 
from datetime import datetime
from imap_tools import MailBox, AND
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# --- CONFIGURACIÓN ROBUSTA ---
# Se carga explícitamente el archivo data.env
load_dotenv('data.env')

# Configuración de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | [%(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler("invoice_bot_errors.log"),
        logging.StreamHandler()
    ]
)

TIMEOUT_GEMINI_SECONDS = 60
POLLING_INTERVAL = 15      

class ResilientInvoiceBot:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        self.excel_path = os.getenv('EXCEL_FILE_PATH')
        self.sheet_name = os.getenv('EXCEL_SHEET_NAME')

        # --- CORRECCIÓN TÉCNICA IMPORTANTE ---
        # Tu script es de LECTURA (IMAP), no de ENVÍO (SMTP).
        # El servidor correcto para leer en Outlook/Hotmail es outlook.office365.com
        # El puerto para IMAP SSL es 993 (imap_tools lo usa por defecto).
        self.imap_server = 'imap.gmail.com'

        # Configuración Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-flash-latest')
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    # ... [EL RESTO DE TUS MÉTODOS (_call_gemini_safe, analyze_with_timeout, etc.) PERMANECEN IGUAL] ...
    # (No los incluyo para ahorrar espacio, ya que no requieren cambios)

    def _call_gemini_safe(self, prompt):
        try:
            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            
            # 1. Validación de respuesta vacía o bloqueada por seguridad
            if not response or not response.parts: 
                logging.warning("⚠️ La IA devolvió una respuesta vacía.")
                return None

            raw_text = response.text
            
            # 2. Búsqueda inteligente del JSON (Bisturí)
            # Busca cualquier cosa que empiece por '{' y termine por '}'
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            
            if match:
                json_str = match.group(0)
            else:
                # Fallback: limpieza manual si regex falla
                json_str = raw_text.replace('```json', '').replace('```', '').strip()

            # 3. Intentar convertir
            return json.loads(json_str)

        except json.JSONDecodeError:
            # ESTO ES LO QUE TE AYUDARÁ A VER EL ERROR REAL
            logging.error(f"❌ La IA no devolvió JSON válido. Texto recibido:\n{raw_text}")
            return None
        except Exception as e:
            logging.error(f"Error general en API: {e}")
            return None

    def analyze_with_timeout(self, text_content, subject, source_type):
        prompt = f"""
        Actúa como analista contable Colombia. Fuente: {source_type}. Asunto: {subject}.
        Extrae: NIT (solo números), CUFE (hexadecimal o N/A), FECHA (YYYY-MM-DD), TOTAL (número).
        Devuelve JSON: {{ "fecha_emision": "YYYY-MM-DD", "nit_emisor": "string", "nombre_emisor": "string", "total_pagar": number, "numero_factura": "string", "cufe": "string", "forma_pago": "string", "medio_pago": "string", "fecha_vencimiento": "YYYY-MM-DD" }}
        CONTENIDO: {text_content[:30000]}
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._call_gemini_safe, prompt)
            try:
                result = future.result(timeout=TIMEOUT_GEMINI_SECONDS)
                return result
            except concurrent.futures.TimeoutError:
                logging.error(f"TIMEOUT: Gemini tardó más de {TIMEOUT_GEMINI_SECONDS}s. Abortando este correo.")
                return None
            except Exception as e:
                logging.error(f"Excepción en hilo de IA: {e}")
                return None

    def process_attachments(self, attachments):
        valid_content = None
        source_type = None
        try:
            for att in attachments:
                if not att.filename: continue
                fname = att.filename.lower()
                if fname.endswith('.zip'):
                    try:
                        with zipfile.ZipFile(io.BytesIO(att.payload)) as z:
                            xmls = [f for f in z.namelist() if f.lower().endswith('.xml')]
                            if xmls:
                                with z.open(xmls[0]) as f:
                                    valid_content = f.read().decode('utf-8', errors='ignore')
                                    source_type = "XML_ZIP"
                                    return valid_content, source_type 
                    except Exception as e:
                        logging.warning(f"ZIP corrupto o ilegible: {e}")
            
            for att in attachments:
                if not att.filename: continue
                if att.filename.lower().endswith('.pdf'):
                    try:
                        with pdfplumber.open(io.BytesIO(att.payload)) as pdf:
                            text = "".join([p.extract_text() or "" for p in pdf.pages])
                            if len(text) > 50:
                                return text, "PDF"
                    except Exception as e:
                        logging.warning(f"PDF ilegible: {e}")
        except Exception as e:
            logging.error(f"Error general procesando adjuntos: {e}")
        return None, None

    def save_excel(self, data, subject):
        try:
            wb = openpyxl.load_workbook(self.excel_path)
            if self.sheet_name in wb.sheetnames:
                ws = wb[self.sheet_name]
                row = [
                    data.get('fecha_emision'), data.get('nit_emisor'), data.get('nombre_emisor'),
                    data.get('total_pagar'), data.get('numero_factura'), data.get('cufe'),
                    data.get('forma_pago'), data.get('medio_pago'), data.get('fecha_vencimiento'),
                    subject
                ]
                ws.append(row)
                wb.save(self.excel_path)
                return True
            return False
        except PermissionError:
            logging.error("EL ARCHIVO EXCEL ESTÁ ABIERTO. No se pudo guardar.")
            return False
        except Exception as e:
            logging.error(f"Error en Excel: {e}")
            return False

    def process_single_email(self, msg):
        try:
            logging.info(f"--> Iniciando: {msg.subject[:50]}...")
            if not msg.attachments:
                logging.info("Saltando: Sin adjuntos.")
                return False 
            content, source = self.process_attachments(msg.attachments)
            if not content:
                logging.warning("Saltando: Adjuntos no válidos fiscalmente.")
                return False
            data = self.analyze_with_timeout(content, msg.subject, source)
            time.sleep(10)
            if not data:
                logging.error("Fallo en Análisis IA (Timeout o Error).")
                return False
            if self.save_excel(data, msg.subject):
                logging.info(f"✅ ÉXITO: Factura {data.get('numero_factura')} guardada.")
                return True
            else:
                logging.error("Fallo en Guardado Excel.")
                return False
        except Exception as e:
            logging.critical(f"ERROR NO CONTROLADO en email '{msg.subject}': {e}")
            return False
     
   # CÓDIGO CORREGIDO PARA app.py

    def start_daemon(self):
        logging.info(f"--- INICIANDO BOT GMAIL (Modelo: {self.model.model_name}) ---")
        logging.info("Presiona Ctrl+C para detener.")
        
        while True:
            try:
                with MailBox(self.imap_server).login(self.email_user, self.email_pass) as mailbox:
                    # CORRECCIÓN CRÍTICA: 
                    # limit=1: Trae solo 1 correo.
                    # reverse=True: Trae el más reciente, no el más viejo.
                    msgs = mailbox.fetch(AND(seen=False), limit=1, reverse=True)
                    
                    count = 0
                    
                    for msg in msgs:
                        count += 1
                        logging.info(f"--> Procesando: {msg.subject[:40]}...")
                        
                        if not msg.attachments:
                            logging.info("   (Sin adjuntos válidos)")
                            # Importante: Marcar como leído o mover para no repetirlo, 
                            # aunque tu código actual confía en que al leerlo (fetch) ya se marca como seen,
                            # a veces es mejor ser explícito si usas mark_seen=True en fetch (por defecto es True).
                            continue

                        content, source = self.process_attachments(msg.attachments)
                        
                        if content:
                            data = self.analyze_with_timeout(content, msg.subject, source)
                            if data:
                                if self.save_excel(data, msg.subject):
                                    logging.info(f"   ✅ Guardado: Factura {data.get('numero_factura')}")
                                    
                                    # --- FRENO PARA EVITAR ERROR 429 ---
                                    logging.info(f"   ⏳ Pausa de {PAUSE_BETWEEN_EMAILS}s (Anti-Bloqueo)...")
                                    time.sleep(PAUSE_BETWEEN_EMAILS)
                        else:
                            logging.info("   (No se pudo extraer texto legible)")

                    if count == 0:
                        # Usamos print simple para no llenar el log de "esperando"
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bandeja al día. Esperando...", end='\r')
                    else:
                        logging.info(f"Ciclo terminado. {count} procesados.")

            except Exception as e:
                logging.error(f"Error de conexión: {e}. Reintentando...")
            
            # Espera general del bucle principal
            time.sleep(POLLING_INTERVAL)
    # --- AGREGA ESTE NUEVO MÉTODO DENTRO DE LA CLASE ---
    def _extract_pdf_text(self, pdf_stream):
        """Método auxiliar para extraer texto de un stream de PDF (sea archivo o dentro de ZIP)"""
        try:
            with pdfplumber.open(pdf_stream) as pdf:
                text = "".join([p.extract_text() or "" for p in pdf.pages])
                # Validación mínima de contenido para asegurar que es legible
                return text if len(text) > 50 else None
        except Exception as e:
            logging.warning(f"Error leyendo stream PDF: {e}")
            return None

    # --- REEMPLAZA TU MÉTODO process_attachments ACTUAL CON ESTE ---
    def process_attachments(self, attachments):
        for att in attachments:
            if not att.filename: continue
            fname = att.filename.lower()
            
            # CASO 1: Archivos Comprimidos (.ZIP)
            if fname.endswith('.zip'):
                try:
                    # Descompresión en memoria (sin guardar en disco)
                    with zipfile.ZipFile(io.BytesIO(att.payload)) as z:
                        file_list = z.namelist()
                        
                        # Prioridad A: Buscar XML (Factura Electrónica Estructurada)
                        xmls = [f for f in file_list if f.lower().endswith('.xml')]
                        if xmls:
                            with z.open(xmls[0]) as f:
                                return f.read().decode('utf-8', errors='ignore'), "XML_ZIP"
                        
                        # Prioridad B: Buscar PDF dentro del ZIP (NUEVA FUNCIONALIDAD)
                        pdfs = [f for f in file_list if f.lower().endswith('.pdf')]
                        if pdfs:
                            # Tomamos el primer PDF encontrado en el ZIP
                            logging.info(f"PDF encontrado dentro de ZIP: {pdfs[0]}")
                            with z.open(pdfs[0]) as f:
                                # Leemos el archivo dentro del zip como bytes
                                pdf_bytes = io.BytesIO(f.read())
                                text = self._extract_pdf_text(pdf_bytes)
                                if text:
                                    return text, "PDF_IN_ZIP"
                                    
                except zipfile.BadZipFile:
                    logging.warning(f"Archivo ZIP corrupto: {fname}")
                except Exception as e:
                    logging.warning(f"Error procesando contenido del ZIP: {e}")

            # CASO 2: Archivos PDF Directos
            elif fname.endswith('.pdf'):
                try:
                    # Reutilizamos la lógica de extracción
                    text = self._extract_pdf_text(io.BytesIO(att.payload))
                    if text:
                        return text, "PDF"
                except Exception: 
                    pass
        
        return None, None
if __name__ == "__main__":
    bot = ResilientInvoiceBot()
    bot.start_daemon()

