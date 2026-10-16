from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import List
from datetime import datetime

app = FastAPI()

# Middleware CORS que permite todos los orígenes (CRÍTICO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get("/gastos")
def obtener_gastos() -> List[dict]:
    conn = None
    try:
        conn = sqlite3.connect('gastos.db')
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM gastos ORDER BY fecha DESC')
        
        # Convertimos filas en diccionarios automáticamente
        columnas = [desc[0] for desc in cursor.description]
        
        resultados = []
        for row in cursor.fetchall():
            dict_row = dict(zip(columnas, row))
            # Aseguramos formato fecha compatible
            if 'fecha' in dict_row and dict_row['fecha']:
                try:
                    dt_obj = datetime.fromisoformat(dict_row['fecha'].replace('Z', '+00:00'))
                    dict_row['fecha'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            
            # Formateamos el monto como número real para JSON
            try:
                dict_row['monto'] = float(dict_row['monto'])
            except (ValueError, TypeError):
                dict_row['monto'] = 0.0
            
            resultados.append(dict_row)
        
        return resultados
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
