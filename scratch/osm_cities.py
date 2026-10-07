import json
import urllib.request

# The cities we need exact coordinates for
cities = {
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
    "Kakinada": {"lat": 16.9891, "lon": 82.2475},
    "Amaravati": {"lat": 16.5131, "lon": 80.5165},
    "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "Guntur": {"lat": 16.3067, "lon": 80.4365},
    "Kurnool": {"lat": 15.8281, "lon": 78.0373},
    "Tirupati": {"lat": 13.6288, "lon": 79.4192},
    "Kadapa": {"lat": 14.4673, "lon": 78.8242},
    "Nellore": {"lat": 14.4426, "lon": 79.9865},
    "Anantapur": {"lat": 14.6819, "lon": 77.6006},
    "Srikakulam": {"lat": 18.2949, "lon": 83.8938},
    "Vizianagaram": {"lat": 18.1133, "lon": 83.3977},
}

try:
    url = 'https://nominatim.openstreetmap.org/search?state=Andhra%20Pradesh&country=India&polygon_geojson=1&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    
    geojson = data[0]['geojson']
    coords = []
    
    geom_type = geojson['type']
    if geom_type == 'Polygon':
        for ring in geojson['coordinates']:
            coords.extend(ring)
    elif geom_type == 'MultiPolygon':
        for poly in geojson['coordinates']:
            for ring in poly:
                coords.extend(ring)
                
    xs = [c[0] for c in coords] # lon
    ys = [c[1] for c in coords] # lat
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    target_width = 440
    target_height = 440
    
    scale_x = target_width / (max_x - min_x)
    scale_y = target_height / (max_y - min_y)
    scale = min(scale_x, scale_y)
    
    x_offset = 40 + (target_width - (max_x - min_x) * scale) / 2
    y_offset = 40 + (target_height - (max_y - min_y) * scale) / 2
    
    # Generate SVG Path
    polys = []
    if geom_type == 'Polygon':
        polys.append(geojson['coordinates'][0])
    elif geom_type == 'MultiPolygon':
        for poly in geojson['coordinates']:
            polys.append(poly[0])
            
    largest_poly = max(polys, key=len)
    step = max(1, len(largest_poly) // 500)
    simplified_poly = largest_poly[::step]
    
    path_str = []
    for i, (x, y) in enumerate(simplified_poly):
        svg_x = (x - min_x) * scale + x_offset
        svg_y = target_height - (y - min_y) * scale + y_offset
        cmd = "M" if i == 0 else "L"
        path_str.append(f"{cmd} {svg_x:.1f} {svg_y:.1f}")
    path_str.append("Z")
    final_path = " ".join(path_str)
    
    print("PATH:", final_path)
    print("====================")
    
    # Calculate exact positions for each city
    for city, pos in cities.items():
        x = pos['lon']
        y = pos['lat']
        svg_x = (x - min_x) * scale + x_offset
        svg_y = target_height - (y - min_y) * scale + y_offset
        print(f"CITY: {city} -> cx='{svg_x:.1f}' cy='{svg_y:.1f}'")

except Exception as e:
    print("Error:", e)
