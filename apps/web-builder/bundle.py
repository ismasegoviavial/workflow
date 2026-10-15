import os

def bundle():
    dist_dir = os.path.abspath(r'd:\Fernanda\Proyectos\workflow-engine-platform\apps\web-builder\dist')
    assets_dir = os.path.join(dist_dir, 'assets')
    css_file = [f for f in os.listdir(assets_dir) if f.endswith('.css')][0]
    js_file = [f for f in os.listdir(assets_dir) if f.endswith('.js')][0]

    with open(os.path.join(assets_dir, css_file), 'r', encoding='utf-8') as f:
        css_content = f.read()

    with open(os.path.join(assets_dir, js_file), 'r', encoding='utf-8') as f:
        js_content = f.read()

    bundled_html = f"""<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cloud Data Fusion | Studio</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&amp;display=swap" rel="stylesheet">
    <style>
{css_content}
    </style>
  </head>
  <body class="bg-[#f8f9fa] text-slate-800 antialiased font-['Roboto',sans-serif] overflow-hidden select-none">
    <div id="root"></div>
    <script type="module">
{js_content}
    </script>
  </body>
</html>"""

    out_path = os.path.abspath(r'd:\Fernanda\Proyectos\workflow-engine-platform\apps\workflow-engine-api\static_studio.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(bundled_html)

    print(f"Bundled static studio saved to: {out_path} ({len(bundled_html)} bytes)")

if __name__ == '__main__':
    bundle()
