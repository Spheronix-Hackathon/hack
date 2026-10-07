# Bounding box of Andhra Pradesh roughly
min_lon, max_lon = 76.76, 84.76
min_lat, max_lat = 12.62, 19.12

target_width = 440
target_height = 440

scale_x = target_width / (max_lon - min_lon)
scale_y = target_height / (max_lat - min_lat)
scale = min(scale_x, scale_y)

x_offset = 40 + (target_width - (max_lon - min_lon) * scale) / 2
y_offset = 40 + (target_height - (max_lat - min_lat) * scale) / 2

cities = {
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
    "Kakinada": {"lat": 16.9891, "lon": 82.2475},
    "Amaravati": {"lat": 16.5131, "lon": 80.5165},
    "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "Guntur": {"lat": 16.3067, "lon": 80.4365},
    "Kurnool": {"lat": 15.8281, "lon": 78.0373},
    "Tirupati": {"lat": 13.6288, "lon": 79.4192},
}

for city, pos in cities.items():
    x = pos['lon']
    y = pos['lat']
    svg_x = (x - min_lon) * scale + x_offset
    svg_y = target_height - (y - min_lat) * scale + y_offset
    print(f"CITY: {city} -> cx='{svg_x:.1f}' cy='{svg_y:.1f}'")
