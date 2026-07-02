import io
import re
import pandas as pd
import streamlit as st
from deep_translator import GoogleTranslator

# ─────────── CONFIGURACIÓN ───────────

MAX_TITULO = 75
MAX_HIGHLIGHT = 125

IDIOMAS = {
    "Español (ES)": "es",
    "Francés (FR)": "fr",
    "Italiano (IT)": "it",
    "Alemán (DE)": "de",
    "Inglés (EN)": "en",
}

MARCAS_INICIO = {"cecotec"}

NO_TRADUCIR = {
    # Marca
    "cecotec",

    # Gamas / familias
    "bolero",
    "coolmarket",
    "minicooling",

    # Tecnologías / nombres comerciales
    "nofrost",
    "totalnofrost",
    "inverter",
    "fresh",
    "flex",
    "green",
    "hub",
    "airflow",
    "multi",

    # Sufijos de modelo / colores comerciales que deben mantenerse en inglés
    "white",
    "black",
    "dark",
    "glass",
    "steel",
    "inox",
    "silver",
    "grey",
    "gray",
    "cream",
    "beige",
    "red",
    "blue",
    "titanium",
    "anthracite",
    "mirror",
    "wood",
    "stone",
    "pearl",
    "gold",
    "champagne",
    "copper",
    "bronze",
    "graphite",
    "platinum",
    "metal",
    "metallic",

    # Nombres de acabado/modelo frecuentes
    "capri",
}

CASING_FIJO = {
    "cecotec": "Cecotec",
    "bolero": "Bolero",
    "coolmarket": "CoolMarket",
    "minicooling": "MiniCooling",
    "nofrost": "NoFrost",
    "totalnofrost": "TotalNoFrost",
    "inverter": "Inverter",
    "fresh": "Fresh",
    "flex": "Flex",
    "green": "Green",
    "hub": "Hub",
    "capri": "Capri",

    "white": "White",
    "glass": "Glass",
    "black": "Black",
    "dark": "Dark",
    "steel": "Steel",
    "inox": "Inox",
    "silver": "Silver",
    "grey": "Grey",
    "gray": "Gray",
    "cream": "Cream",
    "beige": "Beige",
    "red": "Red",
    "blue": "Blue",
    "titanium": "Titanium",
    "anthracite": "Anthracite",
    "mirror": "Mirror",
    "wood": "Wood",
    "stone": "Stone",
    "pearl": "Pearl",
    "gold": "Gold",
    "champagne": "Champagne",
    "copper": "Copper",
    "bronze": "Bronze",
    "graphite": "Graphite",
    "platinum": "Platinum",
    "metal": "Metal",
    "metallic": "Metallic",

    "airflow": "AirFlow",
    "multi": "Multi",

    # ES
    "alto": "Alto",
    "alta": "Alta",
    "altura": "Altura",
    "ancho": "Ancho",
    "ancha": "Ancha",
    "profundo": "Profundo",
    "profunda": "Profunda",
    "profundidad": "Profundidad",
    "sistema": "Sistema",
    "compresor": "Compresor",
    "motor": "Motor",
    "modo": "Modo",
    "inteligente": "Inteligente",
    "cajón": "Cajón",
    "cajon": "Cajón",
    "cajones": "Cajones",

    # EN
    "height": "Height",
    "width": "Width",
    "depth": "Depth",
    "high": "High",
    "wide": "Wide",
    "deep": "Deep",
    "system": "System",
    "compressor": "Compressor",
    "smart": "Smart",
    "mode": "Mode",
    "drawer": "Drawer",
    "drawers": "Drawers",

    "l": "L",
    "v": "V",
    "w": "W",
    "kw": "kW",
    "cm": "cm",
    "mm": "mm",
    "kg": "kg",
    "g": "g",
    "ºc": "ºC",
    "°c": "°C",
}

UNIDADES_PROTEGIDAS = {
    "l", "v", "w", "kw", "cm", "mm", "m", "kg", "g", "ºc", "°c"
}

MENORES = {
    "es": {
        "de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas",
        "lo", "y", "e", "o", "u", "a", "al", "ante", "bajo", "con",
        "contra", "desde", "durante", "en", "entre", "hacia", "hasta",
        "para", "por", "según", "sin", "sobre", "tras", "que", "su", "sus"
    },
    "fr": {
        "le", "la", "les", "un", "une", "des", "de", "du", "d", "l", "et",
        "ou", "à", "au", "aux", "en", "dans", "sur", "sous", "pour", "par",
        "avec", "sans", "ce", "ces"
    },
    "it": {
        "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "del",
        "della", "dei", "delle", "e", "o", "a", "da", "in", "con", "su",
        "per", "tra", "fra", "che"
    },
    "de": {
        "der", "die", "das", "den", "dem", "ein", "eine", "einen", "und",
        "oder", "mit", "ohne", "für", "von", "zu", "im", "in", "auf", "aus"
    },
    "en": {
        "a", "an", "the", "and", "or", "but", "for", "nor", "with",
        "without", "of", "in", "on", "at", "by", "from", "to", "into",
        "onto", "over", "under", "as", "per"
    },
}

PROHIBIDOS = {
    "es": [
        "oferta", "ofertas", "envío gratis", "envio gratis", "gratis",
        "mejor precio", "rebaja", "descuento", "promoción", "promocion",
        "100% original"
    ],
    "fr": [
        "offre", "gratuit", "livraison gratuite", "meilleur prix",
        "promotion", "remise"
    ],
    "it": [
        "offerta", "gratis", "spedizione gratuita", "miglior prezzo",
        "sconto", "promozione"
    ],
    "de": [
        "angebot", "gratis", "kostenloser versand", "bester preis",
        "rabatt", "aktion"
    ],
    "en": [
        "offer", "offers", "free shipping", "free delivery", "free",
        "best price", "sale", "discount", "promotion", "promo",
        "100% original"
    ],
}

# Reparación posterior por si el traductor traduce algún acabado/modelo protegido.
POST_TRADUCCION_MODELO = {
    "fr": {
        "foncé": "Dark",
        "foncee": "Dark",
        "foncée": "Dark",
        "sombre": "Dark",
        "verre": "Glass",
        "blanc": "White",
        "blanche": "White",
        "noir": "Black",
        "noire": "Black",
        "acier": "Steel",
        "inox": "Inox",
        "argent": "Silver",
        "gris": "Grey",
        "grise": "Grey",
        "crème": "Cream",
        "creme": "Cream",
        "beige": "Beige",
        "rouge": "Red",
        "bleu": "Blue",
        "bleue": "Blue",
        "titane": "Titanium",
        "anthracite": "Anthracite",
        "miroir": "Mirror",
        "bois": "Wood",
        "pierre": "Stone",
        "perle": "Pearl",
        "or": "Gold",
        "champagne": "Champagne",
        "cuivre": "Copper",
        "bronze": "Bronze",
        "graphite": "Graphite",
        "platine": "Platinum",
        "métal": "Metal",
        "metal": "Metal",
        "métallique": "Metallic",
        "metallique": "Metallic",
    },
    "it": {
        "scuro": "Dark",
        "scura": "Dark",
        "vetro": "Glass",
        "bianco": "White",
        "bianca": "White",
        "nero": "Black",
        "nera": "Black",
        "acciaio": "Steel",
        "inox": "Inox",
        "argento": "Silver",
        "grigio": "Grey",
        "grigia": "Grey",
        "crema": "Cream",
        "beige": "Beige",
        "rosso": "Red",
        "rossa": "Red",
        "blu": "Blue",
        "titanio": "Titanium",
        "antracite": "Anthracite",
        "specchio": "Mirror",
        "legno": "Wood",
        "pietra": "Stone",
        "perla": "Pearl",
        "oro": "Gold",
        "champagne": "Champagne",
        "rame": "Copper",
        "bronzo": "Bronze",
        "grafite": "Graphite",
        "platino": "Platinum",
        "metallo": "Metal",
        "metallico": "Metallic",
        "metallica": "Metallic",
    },
    "de": {
        "dunkel": "Dark",
        "glas": "Glass",
        "weiß": "White",
        "weiss": "White",
        "schwarz": "Black",
        "stahl": "Steel",
        "inox": "Inox",
        "silber": "Silver",
        "grau": "Grey",
        "creme": "Cream",
        "beige": "Beige",
        "rot": "Red",
        "blau": "Blue",
        "titan": "Titanium",
        "titanium": "Titanium",
        "anthrazit": "Anthracite",
        "spiegel": "Mirror",
        "holz": "Wood",
        "stein": "Stone",
        "perle": "Pearl",
        "gold": "Gold",
        "champagner": "Champagne",
        "champagne": "Champagne",
        "kupfer": "Copper",
        "bronze": "Bronze",
        "graphit": "Graphite",
        "platin": "Platinum",
        "metall": "Metal",
        "metallisch": "Metallic",
    },
    "en": {},
}

# ─────────── PATRONES ───────────

PATRON_VOLT_MULTIPLE = re.compile(
    r"\b(?:funciona|fonctionne|funziona|funktioniert|works|operates)"
    r"(?:\s+(?:a|à|con|avec|mit|en|sur|with))?\s+"
    r"\d+\s*V"
    r"(?:\s*(?:y|e|et|und|and|/|\+)\s*\d+\s*V)+\b",
    flags=re.IGNORECASE
)

PATRON_TEMP = re.compile(
    r"\b\d+(?:[,.]\d+)?\s*[-–]\s*\d+(?:[,.]\d+)?\s*(?:ºC|°C|C)\b",
    flags=re.IGNORECASE
)

PATRON_LITROS = re.compile(
    r"\b\d+(?:[,.]\d+)?\s*L\b",
    flags=re.IGNORECASE
)

PATRON_DIMENSION = re.compile(
    r"\b(?:Alto|Alta|Altura|Ancho|Ancha|Profundo|Profunda|Profundidad|"
    r"Height|Width|Depth|High|Wide|Deep)"
    r"\s+\d+(?:[,.]\d+)?\s*cm\b",
    flags=re.IGNORECASE
)

PATRON_CLASE = re.compile(
    r"\b(?:Clase|Class|Classe|Klasse)\s+[A-G]\b",
    flags=re.IGNORECASE
)

PATRON_TECNOLOGIA_CORTA = re.compile(
    r"\b(?:Total\s+)?NoFrost\b"
    r"|\bMotor\s+Inverter\b"
    r"|\bInverter\s+Motor\b"
    r"|\bCompresor\s+Inverter\b"
    r"|\bInverter\s+Compressor\b"
    r"|\bInverter\b"
    r"|\bSistema\s+Multi\s+AirFlow\b"
    r"|\bMulti\s+AirFlow\s+System\b"
    r"|\bMulti\s+AirFlow\b"
    r"|\bModo\s+Inteligente\b"
    r"|\bSmart\s+Mode\b",
    flags=re.IGNORECASE
)

PH_PREFIX = "ZXQPROT"
PH_SUFFIX = "QXZ"

# ─────────── UTILIDADES DE TOKENS ───────────

def base_token(token: str) -> str:
    return token.strip(".,;:()\"'")

def reemplazar_base_token(token: str, nuevo: str) -> str:
    base = base_token(token)
    if not base:
        return token
    return token.replace(base, nuevo, 1)

def siguiente_token_base(tokens: list, idx: int) -> str:
    if idx + 1 >= len(tokens):
        return ""
    return base_token(tokens[idx + 1])

def anterior_token_base(tokens: list, idx: int) -> str:
    if idx - 1 < 0:
        return ""
    return base_token(tokens[idx - 1])

def es_letra_modelo_una_letra(tokens: list, idx: int) -> bool:
    actual = base_token(tokens[idx])

    if len(actual) != 1 or not actual.isalpha():
        return False

    previo = anterior_token_base(tokens, idx)
    siguiente = siguiente_token_base(tokens, idx)

    previo_low = previo.lower()

    if previo_low in {"clase", "classe", "class", "klasse"}:
        return True

    if any(ch.isdigit() for ch in siguiente):
        return True

    if any(ch.isdigit() for ch in previo):
        return True

    return False

def bloque_parece_modelo(bloque: str) -> bool:
    if not bloque:
        return False

    palabras = {base_token(p).lower() for p in bloque.split()}

    claves_modelo = {
        "cecotec",
        "bolero",
        "coolmarket",
        "minicooling",
        "combi",
        "nofrost",
        "totalnofrost",
        "inverter",
        "fresh",
        "flex",
        "green",
        "hub",
        "airflow",
        "multi",
    }

    if palabras.intersection(claves_modelo):
        return True

    if re.search(r"\b\d{2,4}\b", bloque):
        return True

    if re.search(r"\b[A-Z]\s*,\s*\d", bloque):
        return True

    return False

def reparar_modelos_traducidos(texto: str, lang: str) -> str:
    if not texto or lang not in POST_TRADUCCION_MODELO:
        return texto

    mapping = POST_TRADUCCION_MODELO[lang]

    if not mapping:
        return texto

    partes = re.split(r"(,\s*)", texto)

    def reparar_bloque(bloque: str) -> str:
        tokens = bloque.split()
        out = []

        for tok in tokens:
            base = base_token(tok)
            low = base.lower()

            if low in mapping:
                out.append(reemplazar_base_token(tok, mapping[low]))
            else:
                out.append(tok)

        return " ".join(out)

    for i in range(0, len(partes), 2):
        bloque = partes[i]

        if not bloque.strip():
            continue

        es_primer_bloque = i == 0

        if es_primer_bloque or bloque_parece_modelo(bloque):
            partes[i] = reparar_bloque(bloque)

    t = "".join(partes)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)

    return t.strip(" ,.")

# ─────────── LIMPIEZA Y NORMALIZACIÓN ───────────

def limpiar(texto: str, lang: str) -> str:
    if not isinstance(texto, str):
        return ""

    t = texto.strip()
    t = re.sub(r"\s+", " ", t)

    t = t.replace("“", '"').replace("”", '"')
    t = t.replace("‘", "'").replace("’", "'")
    t = t.replace("–", "-").replace("—", "-")

    t = re.sub(r"\s*-\s*", " - ", t)

    t = re.sub(
        r"[^\w\s\-.,&/+%º°ªÀ-ÿ\"'()]",
        "",
        t,
        flags=re.UNICODE
    )

    for term in PROHIBIDOS.get(lang, []):
        t = re.sub(rf"\b{re.escape(term)}\b", "", t, flags=re.IGNORECASE)

    t = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", t, flags=re.IGNORECASE)

    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    t = re.sub(r"([.,]){2,}", r"\1", t)

    return t.strip(" ,.")

def normalizar_puntos_separadores(texto: str) -> str:
    if not texto:
        return ""

    out = []
    i = 0

    while i < len(texto):
        ch = texto[i]

        if ch == ".":
            prev_char = texto[i - 1] if i > 0 else ""
            next_char_direct = texto[i + 1] if i + 1 < len(texto) else ""

            if prev_char.isdigit() and next_char_direct.isdigit():
                out.append(ch)
                i += 1
                continue

            j = i + 1
            while j < len(texto) and texto[j].isspace():
                j += 1

            siguiente_existe = j < len(texto)
            siguiente_char = texto[j] if siguiente_existe else ""

            siguiente_es_inicio = (
                siguiente_existe
                and re.match(
                    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñÀ-ÿ0-9]",
                    siguiente_char
                ) is not None
            )

            if siguiente_es_inicio:
                out.append(", ")
                i = j
                continue

        out.append(ch)
        i += 1

    t = "".join(out)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)

    return t.strip(" ,.")

def normalizar_semantica(texto: str, lang: str) -> str:
    if not texto:
        return ""

    t = texto

    t = normalizar_puntos_separadores(t)

    t = re.sub(
        r"\bMini\s*-\s*(Réfrigérateur|Refrigerador|Frigorífico|Frigorifero|Kühlschrank|Refrigerator|Fridge)\b",
        r"Mini \1",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\b(\d+(?:[,.]\d+)?)\s*(litros?|litres?|liter|litri|liters?)\b\.?",
        r"\1 L",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\b(\d{1,2})\s+L\b",
        r"\1L",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\b(\d+)\s*V\b",
        r"\1V",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\b(?:rango|plage|gamme|intervallo|bereich|range)"
        r"(?:\s+(?:de|da|von|from))?\s+"
        r"(\d+(?:[,.]\d+)?)\s*(?:a|à|e|et|und|to|-)\s*"
        r"(\d+(?:[,.]\d+)?)\s*"
        r"(?:grados?|degrés?|degrees?|grad|ºc|°c|celsius)\b",
        r"\1-\2 ºC",
        t,
        flags=re.IGNORECASE
    )

    # Dimensiones en español
    t = re.sub(
        r"\bAltura\s+(\d+(?:[,.]\d+)?\s*cm)\b",
        r"Alto \1",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\bAncho\s+(\d+(?:[,.]\d+)?\s*cm)\b",
        r"Ancho \1",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\bProfundidad\s+(\d+(?:[,.]\d+)?\s*cm)\b",
        r"Profundo \1",
        t,
        flags=re.IGNORECASE
    )

    # Dimensiones en inglés
    t = re.sub(
        r"\bHeight\s+(\d+(?:[,.]\d+)?\s*cm)\b",
        r"High \1",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\bWidth\s+(\d+(?:[,.]\d+)?\s*cm)\b",
        r"Wide \1",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(
        r"\bDepth\s+(\d+(?:[,.]\d+)?\s*cm)\b",
        r"Deep \1",
        t,
        flags=re.IGNORECASE
    )

    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)

    return t.strip(" ,.")

def reducir_si_no_cabe(texto: str, limite: int, lang: str) -> str:
    t = texto

    if len(t) <= limite:
        return t

    reglas = [
        (r"\bRéfrigérateur Combiné\s+(?=.*\bCombi\b)", "Réfrigérateur "),
        (r"\bFrigorífico Combi\s+(?=.*\bCombi\b)", "Frigorífico "),
        (r"\bFrigorifero Combinato\s+(?=.*\bCombi\b)", "Frigorifero "),
        (r"\bKühl\s*-\s*Gefrierkombination\s+(?=.*\bCombi\b)", "Kühlschrank "),
        (r"\bKühlgefrierkombination\s+(?=.*\bCombi\b)", "Kühlschrank "),
        (r"\bCombi\s+Refrigerator\s+(?=.*\bCombi\b)", "Refrigerator "),
        (r"\bCombined\s+Refrigerator\s+(?=.*\bCombi\b)", "Refrigerator "),
    ]

    for patron, reemplazo in reglas:
        if len(t) <= limite:
            break
        t = re.sub(patron, reemplazo, t, flags=re.IGNORECASE)
        t = re.sub(r"\s+", " ", t).strip(" ,.")

    return t

def aplicar_casing_fijo(palabra: str) -> str:
    base = base_token(palabra)
    if not base:
        return palabra

    low = base.lower()

    if low not in CASING_FIJO:
        return palabra

    return reemplazar_base_token(palabra, CASING_FIJO[low])

def capitalizar(texto: str, lang: str) -> str:
    if not texto:
        return ""

    menores = MENORES.get(lang, set())
    tokens = texto.split()
    out = []

    for idx, w in enumerate(tokens):
        base = base_token(w)
        low = base.lower()

        if not base:
            out.append(w)
            continue

        fijo = aplicar_casing_fijo(w)
        if fijo != w:
            out.append(fijo)
            continue

        if es_letra_modelo_una_letra(tokens, idx):
            out.append(reemplazar_base_token(w, base.upper()))
            continue

        if low in UNIDADES_PROTEGIDAS:
            out.append(w)
            continue

        if base.isupper() or any(c.isdigit() for c in base):
            out.append(w)
            continue

        if idx != 0 and low in menores:
            out.append(reemplazar_base_token(w, low))
            continue

        out.append(reemplazar_base_token(w, base[:1].upper() + base[1:]))

    return " ".join(out)

# ─────────── TRADUCCIÓN CON PROTECCIÓN DE MARCA/MODELO ───────────

def separar_marca_inicial(texto: str):
    palabras = texto.split()
    prefijo = []

    while palabras and palabras[0].strip(".,;:").lower() in MARCAS_INICIO:
        prefijo.append(palabras.pop(0))

    return " ".join(prefijo), " ".join(palabras)

def crear_placeholder(c: int) -> str:
    return f"{PH_PREFIX}{c:04d}{PH_SUFFIX}"

def proteger(texto: str):
    mapa = {}
    nuevos = []
    c = 0

    tokens = texto.split()

    for idx, tok in enumerate(tokens):
        base = base_token(tok)
        base_low = base.lower()

        debe_proteger = (
            base_low in NO_TRADUCIR
            or base_low in UNIDADES_PROTEGIDAS
            or base.isupper()
            or any(ch.isdigit() for ch in base)
            or es_letra_modelo_una_letra(tokens, idx)
        )

        if debe_proteger:
            ph = crear_placeholder(c)
            mapa[ph] = tok
            nuevos.append(ph)
            c += 1
        else:
            nuevos.append(tok)

    return " ".join(nuevos), mapa

def restaurar(texto: str, mapa: dict) -> str:
    for ph, original in mapa.items():
        texto = re.sub(re.escape(ph), original, texto, flags=re.IGNORECASE)

    return texto

@st.cache_data(show_spinner=False)
def _traducir(texto: str, origen: str, destino: str) -> str:
    try:
        return GoogleTranslator(source=origen, target=destino).translate(texto)
    except Exception:
        return texto

def traducir_protegido(texto: str, origen: str, destino: str) -> str:
    if not texto or origen == destino:
        return texto

    prefijo, resto = separar_marca_inicial(texto)
    resto_prot, mapa = proteger(resto)

    traducido = _traducir(resto_prot, origen, destino)
    traducido = restaurar(traducido, mapa)

    traducido = reparar_modelos_traducidos(traducido, destino)

    return (prefijo + " " + traducido).strip() if prefijo else traducido

# ─────────── DIVISIÓN Y CORTE ───────────

def dividir_bloques_semanticos(titulo: str):
    if not titulo:
        return []

    titulo = normalizar_puntos_separadores(titulo)

    partes = re.split(r",\s+", titulo)
    bloques = []

    for p in partes:
        p = p.strip(" ,.")
        if p:
            bloques.append(p)

    return bloques

def cola_incompleta(texto: str, lang: str) -> str:
    if not texto:
        return ""

    palabras = texto.split()
    menores = MENORES.get(lang, set())

    while palabras:
        ultima_limpia = palabras[-1].strip(".,;:").lower()

        if ultima_limpia in menores:
            palabras.pop()
            continue

        break

    return " ".join(palabras).strip(" ,.")

def cortar_palabras(texto: str, limite: int, lang: str):
    palabras = texto.split()
    part = ""
    i = 0

    while i < len(palabras):
        cand = (part + " " + palabras[i]).strip()

        if len(cand) <= limite:
            part = cand
            i += 1
        else:
            break

    texto_total = " ".join(palabras)
    corte = len(part)

    for m in PATRON_VOLT_MULTIPLE.finditer(texto_total):
        if m.start() < corte < m.end():
            part = texto_total[:m.start()].strip(" ,.")
            resto = texto_total[m.start():].strip(" ,.")
            return cola_incompleta(part, lang), resto

    part = cola_incompleta(part, lang)
    resto = " ".join(palabras[i:]).strip(" ,.")

    return part, resto

def unir_bloque(part: str, bloque: str) -> str:
    return f"{part}, {bloque}" if part else bloque

def _rellenar_secuencial(part: str, bloques: list, limite: int, lang: str):
    restantes = []
    parar = False

    for b in bloques:
        b_norm = normalizar_semantica(b, lang)

        if not parar:
            candidato = unir_bloque(part, b_norm)
            candidato = normalizar_semantica(candidato, lang)
            candidato = reducir_si_no_cabe(candidato, limite, lang)

            if len(candidato) <= limite:
                part = candidato
                continue

            parar = True

        restantes.append(b_norm)

    return part.strip(" ,."), [b for b in restantes if b.strip(" ,.")]

def _rellenar(part: str, bloques: list, limite: int, lang: str):
    restantes = []

    for b in bloques:
        b_norm = normalizar_semantica(b, lang)
        candidato = unir_bloque(part, b_norm)
        candidato = normalizar_semantica(candidato, lang)

        if len(candidato) <= limite:
            part = candidato
        else:
            restantes.append(b_norm)

    return part.strip(" ,."), [b for b in restantes if b.strip(" ,.")]

# ─────────── RELLENO INTELIGENTE DEL TÍTULO ───────────

def es_relleno_valido_titulo(fragmento: str) -> bool:
    f = fragmento.strip(" ,.")

    if not f:
        return False

    if len(f) > 35:
        return False

    if PATRON_VOLT_MULTIPLE.search(f):
        return True

    patrones_relevantes = [
        PATRON_TEMP,
        PATRON_CLASE,
        PATRON_TECNOLOGIA_CORTA,
        PATRON_DIMENSION,
    ]

    if any(p.search(f) for p in patrones_relevantes):
        return True

    if PATRON_LITROS.search(f):
        return True

    return False

def candidatos_relleno_desde_bloque(bloque: str, lang: str):
    b = normalizar_semantica(bloque, lang).strip(" ,.")
    candidatos = []

    def add(valor: str):
        valor = normalizar_semantica(valor, lang).strip(" ,.")
        valor = capitalizar(valor, lang)

        if valor and valor not in candidatos and es_relleno_valido_titulo(valor):
            candidatos.append(valor)

    add(b)

    for m in PATRON_VOLT_MULTIPLE.finditer(b):
        add(m.group(0))

    for m in PATRON_TEMP.finditer(b):
        add(m.group(0))

    for m in PATRON_CLASE.finditer(b):
        add(m.group(0))

    for m in PATRON_TECNOLOGIA_CORTA.finditer(b):
        add(m.group(0))

    for m in PATRON_DIMENSION.finditer(b):
        add(m.group(0))

    for m in PATRON_LITROS.finditer(b):
        add(m.group(0))

    return candidatos

def quitar_fragmento_de_bloque(bloque: str, fragmento: str) -> str:
    b = bloque.strip(" ,.")
    f = fragmento.strip(" ,.")

    if not b:
        return ""

    if b.lower() == f.lower():
        return ""

    b2 = re.sub(re.escape(f), "", b, count=1, flags=re.IGNORECASE)
    b2 = re.sub(r"\s+", " ", b2)
    b2 = re.sub(r"\s+([.,])", r"\1", b2)
    b2 = re.sub(r",\s*,", ",", b2)
    b2 = b2.strip(" ,.-")

    return b2

def _rellenar_oportunista_titulo(part: str, bloques: list, limite: int, lang: str):
    if not part:
        return part, bloques

    bloques_actuales = [b for b in bloques if b.strip(" ,.")]
    cambio = True

    while cambio:
        cambio = False

        for idx, bloque in enumerate(bloques_actuales):
            candidatos = candidatos_relleno_desde_bloque(bloque, lang)

            elegido = None

            for cand in candidatos:
                candidato_titulo = unir_bloque(part, cand)
                candidato_titulo = normalizar_semantica(candidato_titulo, lang)
                candidato_titulo = capitalizar(candidato_titulo, lang)

                if len(candidato_titulo) <= limite:
                    elegido = cand
                    part = candidato_titulo
                    cambio = True
                    break

            if elegido:
                bloque_restante = quitar_fragmento_de_bloque(bloque, elegido)

                nuevos_bloques = []
                nuevos_bloques.extend(bloques_actuales[:idx])

                if bloque_restante:
                    nuevos_bloques.append(bloque_restante)

                nuevos_bloques.extend(bloques_actuales[idx + 1:])
                bloques_actuales = [b for b in nuevos_bloques if b.strip(" ,.")]
                break

    return part.strip(" ,."), bloques_actuales

def dividir(titulo: str, lang: str):
    bloques = dividir_bloques_semanticos(titulo)

    if not bloques:
        return "", "", ""

    primer_bloque = normalizar_semantica(bloques[0], lang)
    primer_bloque = reducir_si_no_cabe(primer_bloque, MAX_TITULO, lang)

    if len(primer_bloque) <= MAX_TITULO:
        titulo_part = primer_bloque
        resto = bloques[1:]
    else:
        titulo_part, sobra = cortar_palabras(primer_bloque, MAX_TITULO, lang)
        resto = ([sobra] if sobra else []) + bloques[1:]

    titulo_part, resto = _rellenar_secuencial(
        titulo_part,
        resto,
        MAX_TITULO,
        lang
    )

    titulo_part, resto = _rellenar_oportunista_titulo(
        titulo_part,
        resto,
        MAX_TITULO,
        lang
    )

    highlight_part, resto = _rellenar(
        "",
        resto,
        MAX_HIGHLIGHT,
        lang
    )

    if not highlight_part and resto:
        primer_highlight = normalizar_semantica(resto[0], lang)
        highlight_part, sobra_h = cortar_palabras(
            primer_highlight,
            MAX_HIGHLIGHT,
            lang
        )
        resto = ([sobra_h] if sobra_h else []) + resto[1:]

        highlight_part, resto = _rellenar(
            highlight_part,
            resto,
            MAX_HIGHLIGHT,
            lang
        )

    titulo_part = normalizar_puntos_separadores(titulo_part)
    highlight_part = normalizar_puntos_separadores(highlight_part)
    sobrante = normalizar_puntos_separadores(", ".join(resto))

    return titulo_part, highlight_part, sobrante

# ─────────── PROCESADO POR IDIOMA ───────────

def procesar_idioma(texto_origen: str, lang_origen: str, lang_salida: str):
    base = limpiar(texto_origen, lang_origen)
    base = normalizar_semantica(base, lang_origen)

    if lang_salida != lang_origen:
        base = traducir_protegido(base, lang_origen, lang_salida)
        base = limpiar(base, lang_salida)
        base = reparar_modelos_traducidos(base, lang_salida)
        base = normalizar_semantica(base, lang_salida)

    base = capitalizar(base, lang_salida)
    base = normalizar_semantica(base, lang_salida)

    titulo, highlight, sobrante = dividir(base, lang_salida)

    titulo = reparar_modelos_traducidos(titulo, lang_salida)
    highlight = reparar_modelos_traducidos(highlight, lang_salida)
    sobrante = reparar_modelos_traducidos(sobrante, lang_salida)

    titulo = capitalizar(titulo, lang_salida)
    highlight = capitalizar(highlight, lang_salida)
    sobrante = capitalizar(sobrante, lang_salida)

    suf = lang_salida.upper()

    return {
        f"titulo_{suf}": titulo,
        f"len_titulo_{suf}": len(titulo),
        f"highlight_{suf}": highlight,
        f"len_highlight_{suf}": len(highlight),
        f"sobrante_{suf}": sobrante,
        f"highlight_incompleto_{suf}": "SÍ" if sobrante else "",
        f"revisar_{suf}": "SÍ" if sobrante else "",
    }

# ─────────── INTERFAZ STREAMLIT ───────────

st.set_page_config(
    page_title="Optimizador de títulos Amazon",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Optimizador de títulos Amazon 75/125")
st.caption("Columnas esperadas: 1ª SKU · 2ª ASIN · 3ª Título a procesar")

archivo = st.file_uploader(
    "Sube tu Excel o CSV",
    type=["xlsx", "csv"]
)

idioma_in = st.selectbox(
    "Idioma de entrada del título",
    list(IDIOMAS.keys())
)

lang_in = IDIOMAS[idioma_in]

destinos = [lang_in]

if lang_in == "es":
    modo = st.radio(
        "¿Qué quieres hacer?",
        ["Solo optimizar ES", "Optimizar y además traducir"]
    )

    if modo == "Optimizar y además traducir":
        seleccion = st.multiselect(
            "Traducir a:",
            [
                "Francés (FR)",
                "Italiano (IT)",
                "Alemán (DE)",
                "Inglés (EN)",
            ]
        )
        destinos = ["es"] + [IDIOMAS[s] for s in seleccion]
else:
    st.info(f"Se optimizará manteniendo el idioma de salida en {idioma_in}.")

# ─────────── TEST MANUAL OPCIONAL ───────────

with st.expander("Probar un título manualmente"):
    titulo_prueba = st.text_area(
        "Pega un título para probar la lógica sin subir archivo",
        height=120
    )

    if st.button("Probar título manual"):
        if not titulo_prueba.strip():
            st.warning("Introduce un título para probar.")
        else:
            filas_prueba = []

            for lang_out in destinos:
                resultado_prueba = procesar_idioma(
                    titulo_prueba,
                    lang_in,
                    lang_out
                )
                resultado_prueba["idioma"] = lang_out.upper()
                filas_prueba.append(resultado_prueba)

            st.dataframe(
                pd.DataFrame(filas_prueba),
                use_container_width=True
            )

# ─────────── PROCESADO DE ARCHIVO ───────────

if archivo and st.button("🚀 Procesar archivo"):
    if archivo.name.lower().endswith(".csv"):
        df = pd.read_csv(archivo, dtype=str).fillna("")
    else:
        df = pd.read_excel(archivo, dtype=str).fillna("")

    if df.shape[1] < 3:
        st.error("El archivo debe tener al menos 3 columnas: SKU, ASIN y Título.")
        st.stop()

    col_sku, col_asin, col_tit = df.columns[0], df.columns[1], df.columns[2]

    filas = []
    barra = st.progress(0.0)

    total = len(df)

    for n, (_, fila) in enumerate(df.iterrows()):
        registro = {
            "sku": fila[col_sku],
            "asin": fila[col_asin],
            "titulo_original": fila[col_tit],
        }

        for lang_out in destinos:
            registro.update(
                procesar_idioma(
                    fila[col_tit],
                    lang_in,
                    lang_out
                )
            )

        filas.append(registro)

        if total:
            barra.progress((n + 1) / total)

    resultado = pd.DataFrame(filas)

    st.success(f"✅ Procesadas {len(resultado)} filas.")
    st.dataframe(resultado, use_container_width=True)

    buffer = io.BytesIO()
    resultado.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        "⬇️ Descargar resultado Excel",
        data=buffer,
        file_name="titulos_procesados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
