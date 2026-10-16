import os
import re
import sqlite3
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from dotenv import load_dotenv

def inicializar_db():
    conn = sqlite3.connect('gastos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            monto REAL,
            categoria TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_gasto(monto, categoria):
    conn = sqlite3.connect('gastos.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gastos (monto, categoria) VALUES (?, ?)
    ''', (monto, categoria))
    conn.commit()
    conn.close()

def extraer_datos(texto: str):
    match = re.search(r'\d+(?:\.\d+)?', texto)
    if not match:
        return None
    
    monto = float(match.group())
    descripcion = re.sub(r'\d+(?:\.\d+)?', '', texto).strip()
    
    if not descripcion:
        descripcion = "Sin descripción"
        
    return monto, descripcion

# --- NUEVO CEREBRO: Categorización Inteligente ---
def obtener_categoria(descripcion: str):
    desc = descripcion.lower()
    
    categorias = {
        "Supermercado": ["coto", "dia", "carrefour", "chino", "mercado", "jumbo"],
        "Transporte": ["nafta", "peaje", "uber", "tren", "colectivo", "subte", "pasaje"],
        "Servicios": ["luz", "agua", "gas", "internet", "celular", "abono"],
        "Comida": ["delivery", "rappi", "pedidosya", "pizza", "empanadas", "hamburguesa"],
        "Educación": ["facultad", "unaj", "curso", "cuaderno", "fotocopias", "apuntes"],
        "Entretenimiento": ["juego", "steam", "hogwarts", "cine", "salida"],
        "Indumentaria": ["ropa", "zapatillas", "adidas", "remera", "campera"]
    }
    
    for categoria, palabras_clave in categorias.items():
        for palabra in palabras_clave:
            if palabra in desc:
                return categoria
                
    return "Otros"
# -------------------------------------------------

def borrar_ultimo_gasto():
    conn = sqlite3.connect('gastos.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gastos WHERE id = (SELECT MAX(id) FROM gastos)')
    rows_deleted = cursor.rowcount
    conn.close()
    return rows_deleted > 0

async def comando_deshacer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if borrar_ultimo_gasto():
        await update.message.reply_text('✅ Se borró el último gasto registrado.')
    else:
        await update.message.reply_text('⚠️ No hay gastos que deshacer. La lista de gastos está vacía.')

async def procesar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    texto = update.message.text
    data = extraer_datos(texto)
    
    if data:
        monto, descripcion = data
        
        # 1. Pasamos la descripción por nuestro nuevo cerebro
        categoria_inteligente = obtener_categoria(descripcion)
        
        # 2. Guardamos combinando la categoría principal y el detalle que escribiste
        # Ejemplo: "Transporte | Nafta"
        categoria_db = f"{categoria_inteligente} | {descripcion.capitalize()}"
        guardar_gasto(monto, categoria_db)
        
        # 3. Formato de la respuesta
        monto_fmt = f"{monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        respuesta = (
            f"🧠 Categoría: {categoria_inteligente}\n"
            f"💰 Monto: ${monto_fmt}\n"
            f"📝 Detalle: {descripcion.capitalize()}\n"
            f"💾 Guardado."
        )
        await update.message.reply_text(respuesta)
    else:
        await update.message.reply_text('❌ No detecté ningún monto. Usa el formato: 5000 nafta')

def main() -> None:
    load_dotenv()
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        raise ValueError('TELEGRAM_TOKEN no encontrado. Revisa tu archivo .env')

    inicializar_db()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_gasto))
    application.add_handler(CommandHandler('deshacer', comando_deshacer))
    application.run_polling()

if __name__ == '__main__':
    main()
