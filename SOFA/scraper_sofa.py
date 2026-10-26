import json
import os
import re
import requests
from bs4 import BeautifulSoup

def scraping_html_exacto_sofa():
    url = "https://www.enelsofa.com/sofa2026/index.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Referer": "https://www.enelsofa.com/sofa2026/index.php?page=agenda",
        "X-Requested-With": "XMLHttpRequest"
    }

    pabellones_keys = [
        "pabellon_1", "pabellon_3", "pabellon_4", "pabellon_5",
        "pabellon_6", "pabellon_7", "pabellon_8", "pabellon_17", "pabellon_23"
    ]

    resultado_final = {pab: [] for pab in pabellones_keys}
    registros_procesados = set()
    lista_items = []

    terminos_busqueda = [
        "store", "tienda", "geek", "anime", "manga", "comic", "comics", "art", "arte",
        "food", "comida", "cosplay", "gaming", "ropa", "figuras", "collectibles", "coleccionables",
        "editorial", "corea", "japon", "musica", "ilustracion", "videojuegos", "fantasia",
        "libreria", "accesorios", "shows", "invitados", "cafeteria", "stands",
        "exhibicion", "exhibiciones", "museo", "historia", "bicicleta", "carros", "coleccion",
        "artefactos", "maquetas", "diorama", "fotografia", "artesania", "manualidades",
        "comunidad", "fanclub", "escuela", "academia", "taller", "tatuajes", "streamer",
        "peluches", "posters", "stickers", "pines", "llaveros", "tazas", "camisetas", "hoodies",
        "manhwa", "funko", "nendoroid", "resinas", "espadas", "replicas", "juegos de mesa", "cartas", "tcg"
    ]

    print("[+] Extraccion de datos de SOFA 2026")

    for i, termino in enumerate(terminos_busqueda):
        for page_num in range(1, 10):
            params = {
                "page": "agenda",
                "sort": "random",
                "seed": "1394341543",
                "q": termino,
                "p": page_num
            }
            try:
                res = requests.get(url, headers=headers, params=params, timeout=5)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                agenda = soup.select_one('#agenda-results')
                items = agenda.find_all(recursive=False) if agenda else soup.select('.card, .item, article')

                if not items:
                    break

                for item in items:
                    texto_bruto = item.get_text(separator=' ', strip=True)
                    if not texto_bruto or len(texto_bruto) < 5:
                        continue

                    clave_unica = re.sub(r'\s+', ' ', texto_bruto.lower()).strip()
                    if clave_unica in registros_procesados:
                        continue
                    
                    registros_procesados.add(clave_unica)

                    nombre_el = item.select_one('.card-title, h3, h4, h5, strong, .title')
                    nombre = nombre_el.text.strip() if nombre_el else texto_bruto[:40]

                    desc_el = item.select_one('p, .description, .desc, .text-muted')
                    if desc_el:
                        descripcion = desc_el.text.strip()
                    else:
                        lineas = [s.strip() for s in item.stripped_strings if len(s) > 4]
                        descripcion = " ".join(lineas[1:5]) if len(lineas) > 1 else texto_bruto[:160]

                    link = item.find('a', href=True)
                    web_url = link['href'] if link else "https://www.enelsofa.com/sofa2026/"
                    if not web_url.startswith('http'):
                        web_url = f"https://www.enelsofa.com/sofa2026/{web_url.lstrip('/')}"

                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', texto_bruto)
                    email = emails[0] if emails else "No especificado"

                    instagram = None
                    facebook = None
                    for a in item.find_all('a', href=True):
                        href = a['href'].lower()
                        if 'instagram.com' in href and not instagram:
                            instagram = a['href']
                        elif 'facebook.com' in href and not facebook:
                            facebook = a['href']

                    fotos = []
                    for img in item.find_all('img', src=True):
                        src = img['src']
                        if not src.startswith('http'):
                            src = f"https://www.enelsofa.com{src if src.startswith('/') else '/' + src}"
                        if not any(b in src.lower() for b in ['icon', 'logo_sofa', 'avatar_default', 'banner']):
                            fotos.append(src)

                    if not fotos:
                        fotos = [
                            "https://images.unsplash.com/photo-1563089145-599997674d42?w=500&q=80",
                            "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500&q=80"
                        ]

                    # --- EXTRACCIÓN DIRECTA DEL HTML DE UBICACIÓN ---
                    pab_detectado = None
                    stand_detectado = None

                    elementos_texto = item.find_all(string=True)
                    bloque_ubicacion = ""
                    
                    for idx_txt, t in enumerate(elementos_texto):
                        if "ubicación" in t.lower() or "lugar" in t.lower() or "pabellón" in t.lower():
                            # Tomamos este texto y el siguiente (donde suele estar el valor real en el HTML)
                            bloque_ubicacion += " " + " ".join(elementos_texto[max(0, idx_txt-1):min(len(elementos_texto), idx_txt+3)])

                    # Si encontramos un bloque específico de ubicación, buscamos ahí el número del pabellón
                    busqueda_fuente = bloque_ubicacion if bloque_ubicacion else texto_bruto

                    # Patrón estricto para extraer el número de pabellón
                    pab_match = re.search(r'pab(?:ell[oó]n)?\.?\s*(?:#|Nivel|\·|-)?\s*(\d{1,2})', busqueda_fuente, re.IGNORECASE)
                    if not pab_match:
                        pab_match = re.search(r'(?:pabell[oó]n|pab)\D{0,10}(\d{1,2})', busqueda_fuente, re.IGNORECASE)

                    if pab_match:
                        num_pab = pab_match.group(1)
                        candidato_key = f"pabellon_{num_pab}"
                        if candidato_key in resultado_final:
                            pab_detectado = candidato_key

                    stand_match = re.search(r'(?:stand|puesto|local)\s*#?\s*([A-Za-z0-9\-]+)', busqueda_fuente, re.IGNORECASE)
                    stand_detectado = stand_match.group(1) if stand_match else None

                    # Respaldo por contenido si el HTML no arrojó el pabellón de forma directa
                    if not pab_detectado:
                        txt_lower = texto_bruto.lower()
                        if "comunidad" in txt_lower or "comunidades" in txt_lower:
                            pab_detectado = "pabellon_3"
                        elif any(k in txt_lower for k in ["bicicleta", "autos", "carros", "museo", "exhibicion historica"]):
                            pab_detectado = "pabellon_6"
                        elif any(k in txt_lower for k in ["comida", "food", "gastronomia", "restaurante", "cafeteria"]):
                            pab_detectado = "pabellon_8"
                        elif any(k in txt_lower for k in ["editorial", "libros", "lectura", "comic"]):
                            pab_detectado = "pabellon_5"
                        else:
                            pab_detectado = "pabellon_1"

                    lista_items.append({
                        "nombre": nombre,
                        "descripcion": descripcion,
                        "email": email,
                        "web": web_url,
                        "instagram": instagram,
                        "facebook": facebook,
                        "fotos": fotos,
                        "pab_detectado": pab_detectado,
                        "stand_detectado": stand_detectado
                    })

            except Exception as e:
                break

        if (i + 1) % 10 == 0:
            print(f"Progreso: {i + 1}/{len(terminos_busqueda)} terminos procesados. Acumulado: {len(lista_items)}")

    total_extraidos = len(lista_items)
    print(f"\nBusqueda finalizada. Total de registros unicos : {total_extraidos}")

    for expo in lista_items:
        pab_key = expo["pab_detectado"]
        pab_num = pab_key.split('_')[1]

        stand_code = expo["stand_detectado"] if expo["stand_detectado"] else f"{pab_num}-{101 + len(resultado_final[pab_key])}"

        resultado_final[pab_key].append({
            "id": f"exp_{len(resultado_final[pab_key]) + 1}",
            "stand": stand_code,
            "nombre": expo["nombre"],
            "categoria": "Expositor / Proyecto Oficial",
            "descripcion": expo["descripcion"],
            "email": expo["email"],
            "web": expo["web"],
            "instagram": expo["instagram"],
            "facebook": expo["facebook"],
            "fotos": expo["fotos"]
        })

    os.makedirs("static/js", exist_ok=True)
    ruta = os.path.join("static", "js", "puestos_auto.js")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"// Base de datos SOFA Ubicaciones HTML, TOTAL: {sum(len(v) for v in resultado_final.values())}\n")
        f.write(f"export const PUESTOS_AUTO = {json.dumps(resultado_final, ensure_ascii=False, indent=2)};\n")

    print(f"Archivo 'static/js/puestos_auto.js' actualizado correctamente.")

if __name__ == "__main__":
    scraping_html_exacto_sofa()