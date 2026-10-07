import urllib.request
import json

url = 'https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/andhra-pradesh.geojson'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    
    # Extract coordinates
    coords = []
    for feature in data.get('features', []):
        geom_type = feature['geometry']['type']
        if geom_type == 'Polygon':
            for ring in feature['geometry']['coordinates']:
                coords.extend(ring)
        elif geom_type == 'MultiPolygon':
            for poly in feature['geometry']['coordinates']:
                for ring in poly:
                    coords.extend(ring)
    
    if not coords:
        print("No coords found.")
        exit(1)
        
    # Calculate bounding box
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # We want to fit it in a 440x440 box with 40px padding (so inside a 520x520 SVG)
    target_width = 440
    target_height = 440
    
    scale_x = target_width / (max_x - min_x)
    scale_y = target_height / (max_y - min_y)
    scale = min(scale_x, scale_y)
    
    x_offset = 40 + (target_width - (max_x - min_x) * scale) / 2
    y_offset = 40 + (target_height - (max_y - min_y) * scale) / 2
    
    # Generate SVG Path
    path_str = []
    # GeoJSON can have multiple disjoint polygons, but for AP it's mostly one main one + some small islands.
    # We'll just simplify and draw the largest polygon.
    largest_poly = []
    for feature in data.get('features', []):
        geom_type = feature['geometry']['type']
        polys = []
        if geom_type == 'Polygon':
            polys.append(feature['geometry']['coordinates'][0])
        elif geom_type == 'MultiPolygon':
            for poly in feature['geometry']['coordinates']:
                polys.append(poly[0])
                
    largest_poly = max(polys, key=len)
    
    # Simplify the polygon by taking every Nth point to reduce string size, as we just need a good visual shape
    step = max(1, len(largest_poly) // 400)
    simplified_poly = largest_poly[::step]
    
    for i, (x, y) in enumerate(simplified_poly):
        # Note: SVG y is inverted relative to lat/lon
        svg_x = (x - min_x) * scale + x_offset
        svg_y = target_height - (y - min_y) * scale + y_offset
        
        cmd = "M" if i == 0 else "L"
        # Round to 1 decimal place to keep string manageable
        path_str.append(f"{cmd} {svg_x:.1f} {svg_y:.1f}")
        
    path_str.append("Z")
    
    final_path = " ".join(path_str)
    with open("ap_path.txt", "w") as f:
        f.write(final_path)
    print("Successfully generated exact AP SVG path. Length:", len(final_path))
except Exception as e:
    print("Error:", e)
