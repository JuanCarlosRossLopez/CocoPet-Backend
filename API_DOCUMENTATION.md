# CocoPet Backend - API REST Documentation

## Configuración del Backend

Tu backend Flask ya está configurado para funcionar como una API REST completa. Los endpoints están disponibles en el prefijo `/api`.

## Endpoints Disponibles

### 1. Health Check
```
GET /api/health
```
Verifica que la API esté funcionando correctamente.

**Respuesta:**
```json
{
  "status": "success",
  "message": "API está funcionando correctamente",
  "version": "1.0.0"
}
```

### 2. Información de la API
```
GET /api
```
Obtiene información general de la API y lista de endpoints.

### 3. Subir Archivo Excel
```
POST /api/upload
```
Sube un archivo Excel con datos de ventas.

**Headers:**
```
Content-Type: multipart/form-data
```

**Body:**
- `file`: Archivo Excel (.xlsx o .xls)

**Estructura requerida del Excel:**
- `latitud`: Coordenada de latitud
- `longitud`: Coordenada de longitud  
- `producto`: Nombre del producto
- `cantidad`: Cantidad vendida

**Respuesta exitosa:**
```json
{
  "status": "success",
  "message": "Archivo subido correctamente",
  "filename": "ventas.xlsx",
  "records_count": 150
}
```

### 4. Listar Archivos
```
GET /api/files
```
Lista todos los archivos Excel subidos.

**Respuesta:**
```json
{
  "status": "success",
  "files": [
    {
      "filename": "ventas.xlsx",
      "size": 12845,
      "modified": 1643723400
    }
  ]
}
```

### 5. Obtener Datos Procesados
```
GET /api/data/<filename>
```
Obtiene los datos procesados con clustering aplicado.

**Respuesta:**
```json
{
  "status": "success",
  "data": [
    {
      "latitud": -34.6037,
      "longitud": -58.3816,
      "producto": "Alimento para Perros",
      "cantidad": 25,
      "cluster": 0
    }
  ],
  "statistics": {
    "total_records": 150,
    "unique_products": 8,
    "total_quantity": 1250,
    "clusters_found": 5,
    "center": {
      "latitud": -34.6037,
      "longitud": -58.3816
    }
  }
}
```

### 6. Generar Mapa
```
POST /api/map/<filename>
```
Genera un mapa interactivo con los datos del archivo.

**Respuesta:**
```json
{
  "status": "success",
  "message": "Mapa generado correctamente",
  "map_url": "/api/map-file/map_ventas.xlsx.html",
  "map_filename": "map_ventas.xlsx.html"
}
```

### 7. Servir Archivo de Mapa
```
GET /api/map-file/<filename>
```
Sirve el archivo HTML del mapa generado.

### 8. Análisis Avanzado
```
GET /api/analytics/<filename>
```
Obtiene análisis estadístico de los datos.

**Respuesta:**
```json
{
  "status": "success",
  "analytics": {
    "products": [
      {
        "producto": "Alimento para Perros",
        "total_cantidad": 450,
        "promedio_cantidad": 25.5,
        "numero_ventas": 18,
        "centro_geografico": {
          "latitud": -34.6037,
          "longitud": -58.3816
        }
      }
    ],
    "total_sales": 1250,
    "average_sale": 23.8,
    "geographic_center": {
      "latitud": -34.6037,
      "longitud": -58.3816
    }
  }
}
```

## Configuración de CORS

El backend ya tiene CORS habilitado para todas las rutas, permitiendo que cualquier frontend pueda consumir la API.

## Cómo Conectar desde el Frontend

### JavaScript/Fetch API
```javascript
// Ejemplo: Subir archivo
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Ejemplo: Obtener datos
fetch('http://localhost:5000/api/data/ventas.xlsx')
.then(response => response.json())
.then(data => {
  console.log('Datos:', data.data);
  console.log('Estadísticas:', data.statistics);
});
```

### React/Axios
```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Subir archivo
const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
};

// Obtener datos
const getData = async (filename) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/data/${filename}`);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
};
```

### Vue.js
```javascript
// En un componente Vue
export default {
  data() {
    return {
      apiUrl: 'http://localhost:5000/api',
      data: null
    }
  },
  methods: {
    async uploadFile(file) {
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await this.$http.post(`${this.apiUrl}/upload`, formData);
        console.log('Archivo subido:', response.data);
      } catch (error) {
        console.error('Error:', error.response.data);
      }
    },
    
    async loadData(filename) {
      try {
        const response = await this.$http.get(`${this.apiUrl}/data/${filename}`);
        this.data = response.data.data;
      } catch (error) {
        console.error('Error:', error.response.data);
      }
    }
  }
}
```

## Iniciar el Backend

Para ejecutar tu backend:

```bash
python app.py
```

El servidor estará disponible en: `http://localhost:5000`

## Manejo de Errores

Todos los endpoints devuelven errores en formato JSON:

```json
{
  "status": "error",
  "message": "Descripción del error"
}
```

Códigos de estado HTTP:
- `200`: Éxito
- `400`: Error de solicitud (datos inválidos)
- `404`: Recurso no encontrado
- `500`: Error interno del servidor

## Consideraciones de Seguridad

Para producción, considera:

1. **Validación de archivos**: Limitar tamaño y tipo de archivos
2. **Autenticación**: Implementar JWT o sessions
3. **Rate limiting**: Limitar requests por IP
4. **HTTPS**: Usar certificados SSL
5. **Variables de entorno**: Para configuración sensible

## Ejemplo de Flujo Completo

1. **Frontend sube archivo**: `POST /api/upload`
2. **Frontend obtiene datos**: `GET /api/data/archivo.xlsx`  
3. **Frontend solicita mapa**: `POST /api/map/archivo.xlsx`
4. **Frontend muestra mapa**: Usar la URL devuelta
5. **Frontend obtiene análisis**: `GET /api/analytics/archivo.xlsx`
