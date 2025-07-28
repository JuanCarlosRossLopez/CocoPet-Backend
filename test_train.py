import requests

filename = "bongopet3_limpio.xlsx"
url = "http://127.0.0.1:5000/mapa-ventas/api/train"

response = requests.post(url, json={"filename": filename})

if response.status_code == 200:
    clusters = response.json()
    for item in clusters:
        print(f"🧩 Cluster {item['cluster']}:")
        print(f"  📍 Centroide: ({item['centroide']['lat']}, {item['centroide']['lon']})")
        print(f"  📦 Productos: {item['productos']}")
        print(f"  🔢 Cantidad total: {item['cantidad_total']}")
        print("—" * 40)
else:
    print("❌ Error:", response.status_code, response.text)
