# ml_models.py - Modelos de Machine Learning para BongoPet
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

class BongoPetMLModels:
    def __init__(self):
        self.kmeans_model = None
        self.rf_model = None
        self.scaler = None
        self.label_encoders = {}
        
    def prepare_data(self, df):
        """Prepara los datos para entrenamiento"""
        # Crear copia del dataframe
        data = df.copy()
        
        # Convertir fecha y extraer características temporales
        data['fecha'] = pd.to_datetime(data['fecha'])
        data['dia_semana'] = data['fecha'].dt.dayofweek
        data['mes'] = data['fecha'].dt.month
        data['dia_mes'] = data['fecha'].dt.day
        data['semana_año'] = data['fecha'].dt.isocalendar().week
        
        # Extraer marcas de productos
        data['marca'] = data['producto'].apply(self.extract_brand)
        
        # Crear variables categóricas numéricas
        categorical_columns = ['categoria', 'marca']
        for col in categorical_columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                data[f'{col}_encoded'] = self.label_encoders[col].fit_transform(data[col])
            else:
                data[f'{col}_encoded'] = self.label_encoders[col].transform(data[col])
        
        return data
    
    def extract_brand(self, producto):
        """Extrae la marca del nombre del producto"""
        producto = str(producto).lower()
        if 'nupec' in producto:
            return 'Nupec'
        elif 'nexgard' in producto:
            return 'Nexgard'
        elif 'royal canin' in producto:
            return 'Royal Canin'
        elif 'hills' in producto:
            return 'Hills'
        elif 'purina' in producto:
            return 'Purina'
        elif 'bravecto' in producto:
            return 'Bravecto'
        elif 'frontline' in producto:
            return 'Frontline'
        else:
            return 'Otras'
    
    def train_clustering_model(self, df, n_clusters=8):
        """Entrena el modelo de clustering para zonas geográficas"""
        print("Entrenando modelo K-means para clustering geográfico...")
        
        # Preparar datos geográficos
        geo_data = df[['latitud', 'longitud']].dropna()
        
        # Normalizar coordenadas
        self.scaler = StandardScaler()
        geo_scaled = self.scaler.fit_transform(geo_data)
        
        # Entrenar K-means
        self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = self.kmeans_model.fit_predict(geo_scaled)
        
        # Añadir clusters al dataframe original
        df_with_clusters = df.copy()
        valid_indices = geo_data.index
        df_with_clusters.loc[valid_indices, 'cluster'] = clusters
        
        # Análisis de clusters por categoría
        cluster_analysis = self.analyze_clusters(df_with_clusters)
        
        print(f"Modelo K-means entrenado con {n_clusters} clusters")
        return df_with_clusters, cluster_analysis
    
    def analyze_clusters(self, df):
        """Analiza las características de cada cluster"""
        cluster_info = {}
        
        for cluster_id in df['cluster'].dropna().unique():
            cluster_data = df[df['cluster'] == cluster_id]
            
            cluster_info[int(cluster_id)] = {
                'total_ventas': len(cluster_data),
                'ingresos_totales': cluster_data['precio'].sum(),
                'coordenadas_centro': {
                    'lat': cluster_data['latitud'].mean(),
                    'lng': cluster_data['longitud'].mean()
                },
                'categoria_dominante': cluster_data['categoria'].mode().iloc[0] if len(cluster_data) > 0 else 'N/A',
                'marca_dominante': cluster_data.apply(lambda x: self.extract_brand(x['producto']), axis=1).mode().iloc[0] if len(cluster_data) > 0 else 'N/A',
                'productos_populares': cluster_data['producto'].value_counts().head(3).to_dict(),
                'ventas_por_categoria': cluster_data['categoria'].value_counts().to_dict(),
                'precio_promedio': cluster_data['precio'].mean(),
                'dia_semana_popular': cluster_data['fecha'].dt.day_name().mode().iloc[0] if len(cluster_data) > 0 else 'N/A'
            }
        
        return cluster_info
    
    def train_sales_prediction_model(self, df):
        """Entrena el modelo Random Forest para predicción de ventas"""
        print("Entrenando modelo Random Forest para predicción de ventas...")
        
        # Preparar datos
        data = self.prepare_data(df)
        
        # Seleccionar características para el modelo
        feature_columns = [
            'latitud', 'longitud', 'dia_semana', 'mes', 'dia_mes', 
            'semana_año', 'categoria_encoded', 'marca_encoded'
        ]
        
        # Si tenemos clusters, los incluimos
        if 'cluster' in data.columns:
            feature_columns.append('cluster')
            data['cluster'] = data['cluster'].fillna(-1)  # Manejar valores nulos
        
        # Preparar X e y
        X = data[feature_columns].fillna(0)
        y_precio = data['precio']
        y_cantidad = data['cantidad']
        
        # Dividir datos
        X_train, X_test, y_precio_train, y_precio_test = train_test_split(
            X, y_precio, test_size=0.2, random_state=42
        )
        _, _, y_cantidad_train, y_cantidad_test = train_test_split(
            X, y_cantidad, test_size=0.2, random_state=42
        )
        
        # Entrenar modelos
        self.rf_model = {
            'precio': RandomForestRegressor(n_estimators=100, random_state=42),
            'cantidad': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
        self.rf_model['precio'].fit(X_train, y_precio_train)
        self.rf_model['cantidad'].fit(X_train, y_cantidad_train)
        
        # Evaluar modelos
        precio_pred = self.rf_model['precio'].predict(X_test)
        cantidad_pred = self.rf_model['cantidad'].predict(X_test)
        
        precio_r2 = r2_score(y_precio_test, precio_pred)
        cantidad_r2 = r2_score(y_cantidad_test, cantidad_pred)
        
        print(f"R² Score - Precio: {precio_r2:.4f}")
        print(f"R² Score - Cantidad: {cantidad_r2:.4f}")
        
        # Importancia de características
        feature_importance = {
            'precio': dict(zip(feature_columns, self.rf_model['precio'].feature_importances_)),
            'cantidad': dict(zip(feature_columns, self.rf_model['cantidad'].feature_importances_))
        }
        
        return feature_importance
    
    def predict_sales(self, lat, lng, categoria, marca, dia_semana=None, mes=None):
        """Realiza predicciones de ventas"""
        if self.rf_model is None:
            raise ValueError("El modelo no ha sido entrenado")
        
        # Usar valores actuales si no se especifican
        if dia_semana is None:
            dia_semana = pd.Timestamp.now().dayofweek
        if mes is None:
            mes = pd.Timestamp.now().month
        
        # Codificar categoría y marca
        categoria_encoded = self.label_encoders['categoria'].transform([categoria])[0]
        marca_encoded = self.label_encoders['marca'].transform([marca])[0]
        
        # Predecir cluster si el modelo de clustering está entrenado
        cluster = -1
        if self.kmeans_model is not None and self.scaler is not None:
            coords_scaled = self.scaler.transform([[lat, lng]])
            cluster = self.kmeans_model.predict(coords_scaled)[0]
        
        # Preparar datos para predicción
        features = np.array([[
            lat, lng, dia_semana, mes, pd.Timestamp.now().day,
            pd.Timestamp.now().isocalendar().week,
            categoria_encoded, marca_encoded, cluster
        ]])
        
        # Realizar predicciones
        precio_pred = self.rf_model['precio'].predict(features)[0]
        cantidad_pred = self.rf_model['cantidad'].predict(features)[0]
        
        return {
            'precio_estimado': round(precio_pred, 2),
            'cantidad_estimada': round(cantidad_pred, 2),
            'cluster_asignado': int(cluster)
        }
    
    def get_zone_predictions(self, df_with_clusters, cluster_analysis):
        """Genera predicciones por zona para el mapa de calor"""
        zone_predictions = {}
        
        for cluster_id, info in cluster_analysis.items():
            # Calcular predicciones para diferentes días de la semana
            weekly_predictions = {}
            for dia in range(7):
                dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                
                pred_alimento = self.predict_sales(
                    info['coordenadas_centro']['lat'],
                    info['coordenadas_centro']['lng'],
                    'Alimento', 'Nupec', dia
                )
                
                pred_medicamento = self.predict_sales(
                    info['coordenadas_centro']['lat'],
                    info['coordenadas_centro']['lng'],
                    'Medicamento', 'Nexgard', dia
                )
                
                weekly_predictions[dias_semana[dia]] = {
                    'alimento': pred_alimento,
                    'medicamento': pred_medicamento
                }
            
            zone_predictions[cluster_id] = {
                'info_zona': info,
                'predicciones_semanales': weekly_predictions
            }
        
        return zone_predictions
    
    def save_models(self, path_prefix='models/'):
        """Guarda los modelos entrenados"""
        if self.kmeans_model:
            joblib.dump(self.kmeans_model, f'{path_prefix}kmeans_model.pkl')
        if self.rf_model:
            joblib.dump(self.rf_model, f'{path_prefix}rf_model.pkl')
        if self.scaler:
            joblib.dump(self.scaler, f'{path_prefix}scaler.pkl')
        if self.label_encoders:
            joblib.dump(self.label_encoders, f'{path_prefix}label_encoders.pkl')
        
        print("Modelos guardados exitosamente")
    
    def load_models(self, path_prefix='models/'):
        """Carga los modelos entrenados"""
        try:
            self.kmeans_model = joblib.load(f'{path_prefix}kmeans_model.pkl')
            self.rf_model = joblib.load(f'{path_prefix}rf_model.pkl')
            self.scaler = joblib.load(f'{path_prefix}scaler.pkl')
            self.label_encoders = joblib.load(f'{path_prefix}label_encoders.pkl')
            print("Modelos cargados exitosamente")
        except Exception as e:
            print(f"Error cargando modelos: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    # Cargar datos (ajustar la ruta según tu archivo)
    df = pd.read_excel('bongopet3_limpio.xlsx')
    
    # Inicializar modelo
    ml_model = BongoPetMLModels()
    
    # Entrenar clustering
    df_with_clusters, cluster_analysis = ml_model.train_clustering_model(df, n_clusters=8)
    
    # Entrenar modelo de predicción
    feature_importance = ml_model.train_sales_prediction_model(df_with_clusters)
    
    # Generar predicciones por zona
    zone_predictions = ml_model.get_zone_predictions(df_with_clusters, cluster_analysis)
    
    # Guardar modelos
    ml_model.save_models()
    
    print("Entrenamiento completado!")
    print("Análisis de clusters:", cluster_analysis)
    print("Importancia de características:", feature_importance)