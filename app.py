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
}

MARCAS_INICIO = {"cecotec"}

NO_TRADUCIR = {
    "cecotec",
    "bolero",
    "coolmarket",
    "minicooling",
    "nofrost",
    "totalnofrost",
    "inverter",
    "fresh",
    "flex",
    "green",
    "hub",
    "capri",
    "airflow",
    "multi",
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
    "airflow": "AirFlow",
    "multi": "Multi",
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
    r"\b(?:Alto|Alta|Altura|Ancho|Ancha|Profundo|Profunda|Profundidad)"
    r"\s+\d+(?:[,.]\d+)?\s*cm\b",
    flags=re.IGNORECASE
)

PATRON_CLASE = re.compile(
    r"\bClase\s+[A-G]\b",
    flags=re.IGNORECASE
)

PATRON_TECNOLOGIA_CORTA = re.compile(
    r"\b(?:Total\s+)?NoFrost\b"
    r"|\bMotor\s+Inverter\b"
    r"|\bCompresor\s+Inverter\b"
    r"|\bInverter\b"
    r"|\bSistema\s+Multi\s+AirFlow\b"
    r"|\bMulti\s+AirFlow\b"
    r"|\bModo\s+Inteligente\b",
    flags=re.IGNORECASE
)


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
    """
    Detecta letras de modelo o clase como:
    - Dark E, 409 L
    - White Glass C, 409 L
    - Clase C

    Evita que 'E' se convierta en 'e' aunque 'e' sea conjunción en español.
    """

    actual = base_token(tokens[idx])

    if len(actual) != 1 or not actual.isalpha():
        return False

    previo = anterior_token_base(tokens, idx)
    siguiente = siguiente_token_base(tokens, idx)

    previo_low = previo.lower()

    # Clase energética: Clase C, Classe C, Klasse C, etc.
    if previo_low in {"clase", "classe", "class", "klasse"}:
        return True

    # Modelo de una letra seguido de número: E, 409 / C, 409
    if any(ch.isdigit() for ch in siguiente):
        return True

    # Modelo de una letra cerca de una referencia numérica
    if any(ch.isdigit() for ch in previo):
        return True

    return False


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
    """
    Cambia puntos separadores por comas.

    Ejemplos:
    - Capri Black. Funciona a 12V -> Capri Black, Funciona a 12V
    - Dark E. 409 L -> Dark E, 409 L
    - White Glass C. 409 L -> White Glass C, 409 L

    No cambia puntos decimales:
    - 4.5 L se conserva como 4.5 L
    """

    if not texto:
        return ""

    out = []
    i = 0

    while i < len(texto):
        ch = texto[i]

        if ch == ".":
            prev_char = texto[i - 1] if i > 0 else ""
            next_char_direct = texto[i + 1] if i + 1 < len(texto) else ""

            # No convertir puntos decimales: 4.5
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
    """
    Compacta solo lo que no cambia el sentido.

    Sí:
    - 409 Litros -> 409 L
    - 12 V -> 12V
    - Rango de 7 a 50 Grados -> 7-50 ºC
    - Capri Black. Funciona -> Capri Black, Funciona
    - Dark E. 409 L -> Dark E, 409 L
    - Altura 184,6 cm -> Alto 184,6 cm

    No:
    - Funciona a 12V y 220V -> 12V y 220V
    """

    if not texto:
        return ""

    t = texto

    # Puntos separadores a comas, incluidos modelos de una letra:
    # E. 409 L -> E, 409 L
    t = normalizar_puntos_separadores(t)

    # Corrección habitual en traducciones tipo "Mini - Réfrigérateur"
    t = re.sub(
        r"\bMini\s*-\s*(Réfrigérateur|Refrigerador|Frigorífico|Frigorifero|Kühlschrank)\b",
        r"Mini \1",
        t,
        flags=re.IGNORECASE
    )

    # 409 Litros / 409 litres / 409 liter / 409 litri -> 409 L
    t = re.sub(
        r"\b(\d+(?:[,.]\d+)?)\s*(litros?|litres?|liter|litri)\b\.?",
        r"\1 L",
        t,
        flags=re.IGNORECASE
    )

    # MiniCooling 4 L -> MiniCooling 4L
    # Solo une cantidades pequeñas para evitar 409 L -> 409L.
    t = re.sub(
        r"\b(\d{1,2})\s+L\b",
        r"\1L",
        t,
        flags=re.IGNORECASE
    )

    # 12 V -> 12V, pero NO elimina "Funciona a"
    t = re.sub(
        r"\b(\d+)\s*V\b",
        r"\1V",
        t,
        flags=re.IGNORECASE
    )

    # Rango de 7 a 50 Grados -> 7-50 ºC
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

    # Dimensiones:
    # Altura 184,6 cm -> Alto 184,6 cm
    # Ancho 59,5 cm -> Ancho 59,5 cm
    # Profundidad 65 cm -> Profundo 65 cm
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

    # Limpieza final
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    t = re.sub(r",\s*,", ",", t)

    return t.strip(" ,.")


def reducir_si_no_cabe(texto: str, limite: int, lang: str) -> str:
    """
    Reducciones conservadoras para que el título quepa.
    Solo elimina redundancias claras.
    """

    t = texto

    if len(t) <= limite:
        return t

    reglas = [
        (r"\bRéfrigérateur Combiné\s+(?=.*\bCombi\b)", "Réfrigérateur "),
        (r"\bFrigorífico Combi\s+(?=.*\bCombi\b)", "Frigorífico "),
        (r"\bFrigorifero Combinato\s+(?=.*\bCombi\b)", "Frigorifero "),
        (r"\bKühl\s*-\s*Gefrierkombination\s+(?=.*\bCombi\b)", "Kühlschrank "),
        (r"\bKühlgefrierkombination\s+(?=.*\bCombi\b)", "Kühlschrank "),
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
    """
    Capitalización con protección de:
    - marcas/modelos
    - unidades
    - letras de modelo de una sola letra: E, C, etc.
    - clases energéticas: Clase C
    """

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

        # 1. Casing comercial/técnico fijo
        fijo = aplicar_casing_fijo(w)
        if fijo != w:
            out.append(fijo)
            continue

        # 2. Letras de modelo/clase de una sola letra:
        # Dark E, 409 L / White Glass C, 409 L / Clase C
        if es_letra_modelo_una_letra(tokens, idx):
            out.append(reemplazar_base_token(w, base.upper()))
            continue

        # 3. Unidades protegidas
        if low in UNIDADES_PROTEGIDAS:
            out.append(w)
            continue

        # 4. Siglas o tokens con números
        if base.isupper() or any(c.isdigit() for c in base):
            out.append(w)
            continue

        # 5. Palabras menores
        # Importante: una 'E' de modelo no llega aquí porque queda protegida arriba.
        if idx != 0 and low in menores:
            out.append(reemplazar_base_token(w, low))
            continue

        # 6. Capitalización normal
        out.append(reemplazar_base_token(w, base[:1].upper() + base[1:]))

    return " ".join(out)


# ─────────── TRADUCCIÓN CON PROTECCIÓN DE MARCA/MODELO ───────────

def separar_marca_inicial(texto: str):
    palabras = texto.split()
    prefijo = []

    while palabras and palabras[0].strip(".,;:").lower() in MARCAS_INICIO:
        prefijo.append(palabras.pop(0))

    return " ".join(prefijo), " ".join(palabras)


def proteger(texto: str):
    mapa = {}
    nuevos = []
    c = 0

    for tok in texto.split():
        base = base_token(tok)
        base_low = base.lower()

        debe_proteger = (
            base_low in NO_TRADUCIR
            or base_low in UNIDADES_PROTEGIDAS
            or base.isupper()
            or any(ch.isdigit() for ch in base)
        )

        if debe_proteger:
            ph = f"__NT{c}__"
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

    return (prefijo + " " + traducido).strip() if prefijo else traducido


# ─────────── DIVISIÓN Y CORTE ───────────

def dividir_bloques_semanticos(titulo: str):
    """
    Divide por comas.
    Los puntos separadores ya se convierten antes a comas.
    """

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
    """
    Evita que el título termine en conectores, preposiciones o tokens colgados.
    """

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
    """
    Corta por palabras, pero evita cortar dentro de frases críticas como:
    'Funciona a 12V y 220V'.
    """

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
    """
    TÍTULO:
    Añade bloques en orden.
    Si el primer bloque que toca no cabe, se detiene.
    """

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
    """
    HIGHLIGHT:
    Añade todos los bloques que quepan.
    Puede saltar bloques grandes para aprovechar espacio.
    """

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
    """
    Extrae candidatos breves y relevantes de un bloque.
    """

    b = normalizar_semantica(bloque, lang).strip(" ,.")
    candidatos = []

    def add(valor: str):
        valor = normalizar_semantica(valor, lang).strip(" ,.")
        valor = capitalizar(valor, lang)

        if valor and valor not in candidatos and es_relleno_valido_titulo(valor):
            candidatos.append(valor)

    # Bloque completo si es corto y relevante
    add(b)

    # Frases completas de voltaje
    for m in PATRON_VOLT_MULTIPLE.finditer(b):
        add(m.group(0))

    # Temperatura
    for m in PATRON_TEMP.finditer(b):
        add(m.group(0))

    # Clase energética
    for m in PATRON_CLASE.finditer(b):
        add(m.group(0))

    # Tecnologías cortas
    for m in PATRON_TECNOLOGIA_CORTA.finditer(b):
        add(m.group(0))

    # Dimensiones
    for m in PATRON_DIMENSION.finditer(b):
        add(m.group(0))

    # Litros
    for m in PATRON_LITROS.finditer(b):
        add(m.group(0))

    return candidatos


def quitar_fragmento_de_bloque(bloque: str, fragmento: str) -> str:
    """
    Elimina del bloque el fragmento que se ha subido al título,
    para evitar duplicados en highlight/sobrante.
    """

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
    """
    Si el título queda corto, busca en los bloques restantes una especificación breve
    que quepa dentro de los 75 caracteres.
    """

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

    # Relleno secuencial normal
    titulo_part, resto = _rellenar_secuencial(
        titulo_part,
        resto,
        MAX_TITULO,
        lang
    )

    # Relleno oportunista con specs breves
    titulo_part, resto = _rellenar_oportunista_titulo(
        titulo_part,
        resto,
        MAX_TITULO,
        lang
    )

    # Highlight
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
        base = normalizar_semantica(base, lang_salida)

    base = capitalizar(base, lang_salida)
    base = normalizar_semantica(base, lang_salida)

    titulo, highlight, sobrante = dividir(base, lang_salida)

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
            ["Francés (FR)", "Italiano (IT)", "Alemán (DE)"]
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
