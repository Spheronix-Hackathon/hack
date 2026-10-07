import re

cities = {
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
    "Kakinada": {"lat": 16.9891, "lon": 82.2475},
    "Amaravati": {"lat": 16.5131, "lon": 80.5165},
    "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "Guntur": {"lat": 16.3067, "lon": 80.4365},
    "Kurnool": {"lat": 15.8281, "lon": 78.0373},
    "Tirupati": {"lat": 13.6288, "lon": 79.4192},
}

with open("ap_exact_path.txt", "r") as f:
    path_str = f.read()

# Extract all x, y coordinates from path
coords = re.findall(r'[ML]\s+([0-9.]+)\s+([0-9.]+)', path_str)
svg_xs = [float(c[0]) for c in coords]
svg_ys = [float(c[1]) for c in coords]

svg_min_x, svg_max_x = min(svg_xs), max(svg_xs)
svg_min_y, svg_max_y = min(svg_ys), max(svg_ys)

print("SVG Bounds:")
print(f"X: {svg_min_x} to {svg_max_x}")
print(f"Y: {svg_min_y} to {svg_max_y}")

# But to project new lat/lon to these SVG bounds, we need the original lat/lon bounds that generated them.
# In osm_map.py, we used:
# xs = [lon], ys = [lat]
# We don't have the exact original min_lon/max_lon.
# Wait! AP's actual geographical bounds in Nominatim are exactly:
# min_lon: 76.7610444, max_lon: 84.7646194
# min_lat: 12.6241199, max_lat: 19.1233075

# Let's map lat/lon linearly to the SVG bounding box!
# We know the easternmost point of AP is max_lon -> maps to svg_max_x
# Westernmost point is min_lon -> maps to svg_min_x
# Northernmost point is max_lat -> maps to svg_min_y (since Y is inverted)
# Southernmost point is min_lat -> maps to svg_max_y

# Approximate known exact bounds of AP:
# Top (North): ~19.12° (Srikakulam tip)
# Bottom (South): ~12.62° (Chittoor tip)
# Left (West): ~76.76° (Anantapur tip)
# Right (East): ~84.76° (Srikakulam/Vizianagaram coast)

# Let's use exactly these for mapping, assuming the polygon covers this exact box.
lon_min = 76.761
lon_max = 84.764
lat_min = 12.624
lat_max = 19.123

for city, pos in cities.items():
    lon = pos['lon']
    lat = pos['lat']
    
    # Linear interpolation
    cx = svg_min_x + (lon - lon_min) / (lon_max - lon_min) * (svg_max_x - svg_min_x)
    # y is inverted
    cy = svg_max_y - (lat - lat_min) / (lat_max - lat_min) * (svg_max_y - svg_min_y)
    
    print(f"CITY: {city} -> cx='{cx:.1f}' cy='{cy:.1f}'")
