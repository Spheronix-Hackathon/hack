import re

try:
    with open('static/new_landing.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    with open('ap_exact_path.txt', 'r', encoding='utf-8') as f:
        path = f.read().strip()
        
    # Replace the path
    html = re.sub(
        r'(<path class="ap-path" id="ap-outline"\s+d=")[^"]*(")',
        r'\1' + path + r'\2',
        html,
        flags=re.DOTALL
    )
    
    with open('static/new_landing.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Successfully injected the exact geographic path into the HTML!")
except Exception as e:
    print("Error:", e)
