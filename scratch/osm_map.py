import urllib.request
import json

# Nominatim API for Andhra Pradesh boundary
url = 'https://nominatim.openstreetmap.org/search?state=Andhra%20Pradesh&country=India&polygon_geojson=1&format=json'

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
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
                
    if not coords:
        print("No coords found.")
        exit(1)
        
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    target_width = 440
    target_height = 440
    
    scale_x = target_width / (max_x - min_x)
    scale_y = target_height / (max_y - min_y)
    scale = min(scale_x, scale_y)
    
    x_offset = 40 + (target_width - (max_x - min_x) * scale) / 2
    y_offset = 40 + (target_height - (max_y - min_y) * scale) / 2
    
    path_str = []
    
    # Process polygons
    polys = []
    if geom_type == 'Polygon':
        polys.append(geojson['coordinates'][0])
    elif geom_type == 'MultiPolygon':
        for poly in geojson['coordinates']:
            polys.append(poly[0])
            
    largest_poly = max(polys, key=len)
    
    # Simplify (keep every 5th point to keep SVG reasonable)
    step = max(1, len(largest_poly) // 500)
    simplified_poly = largest_poly[::step]
    
    for i, (x, y) in enumerate(simplified_poly):
        svg_x = (x - min_x) * scale + x_offset
        svg_y = target_height - (y - min_y) * scale + y_offset
        cmd = "M" if i == 0 else "L"
        path_str.append(f"{cmd} {svg_x:.1f} {svg_y:.1f}")
        
    path_str.append("Z")
    
    with open("ap_exact_path.txt", "w") as f:
        f.write(" ".join(path_str))
    print("Success! Created ap_exact_path.txt")
except Exception as e:
    print("Error:", e)
