import io
import re
import pandas as pd
import streamlit as st
from deep_translator import GoogleTranslator

# ─────────── PARÁMETROS ───────────
MAX_TITULO = 75
MAX_HIGHLIGHT = 125

IDIOMAS = {"Español (ES)": "es", "Francés (FR)": "fr",
           "Italiano (IT)": "it", "Alemán (DE)": "de"}

# Palabras que NO se capitalizan (salvo si van al principio), por idioma
MENORES = {
    "es": {"de","del","la","el","los","las","un","una","unos","unas","lo","y","e",
           "o","u","a","al","ante","bajo","con","contra","desde","durante","en",
           "entre","hacia","hasta","para","por","según","sin","sobre","tras","que",
           "su","sus"},
    "fr": {"le","la","les","un","une","des","de","du","d","l","et","ou","à","au",
           "aux","en","dans","sur","sous","pour","par","avec","sans","ce","ces"},
    "it": {"il","lo","la","i","gli","le","un","uno","una","di","del","della","dei",
           "delle","e","o","a","da","in","con","su","per","tra","fra","che"},
    "de": {"der","die","das","den","dem","ein","eine","einen","und","oder","mit",
           "ohne","für","von","zu","im","in","auf","aus"},
}

# Términos promocionales prohibidos por idioma (se eliminan)
PROHIBIDOS = {
    "es": ["oferta","ofertas","envío gratis","envio gratis","gratis","mejor precio",
           "rebaja","descuento","promoción","promocion","100% original"],
    "fr": ["offre","gratuit","livraison gratuite","meilleur prix","promotion","remise"],
    "it": ["offerta","gratis","spedizione gratuita","miglior prezzo","sconto","promozione"],
    "de": ["angebot","gratis","kostenloser versand","bester preis","rabatt","aktion"],
}


def limpiar(texto: str, lang: str) -> str:
    if not isinstance(texto, str):
        return ""
    t = texto.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"\s*-\s*", " - ", t)
    t = re.sub(r"[^\w\s\-.,&/+%º°ªáéíóúüñÁÉÍÓÚÜÑàâçèéêëîïôûùÀÂÇÈÉÊËÎÏÔÛÙäöüßÄÖÜ\"'()]", "", t)
    for term in PROHIBIDOS.get(lang, []):
        t = re.sub(rf"\b{re.escape(term)}\b", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", t, flags=re.IGNORECASE)  # palabras repetidas
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    return t


def capitalizar(texto: str, lang: str) -> str:
    menores = MENORES.get(lang, set())
    palabras = texto.split()
    out = []
    for idx, w in enumerate(palabras):
        if (len(w) > 1 and w.isupper()) or any(c.isdigit() for c in w):
            out.append(w)                       # marcas/acrónimos y modelos: intactos
        elif idx != 0 and w.lower() in menores:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def dividir(titulo: str):
    palabras = titulo.split()
    t_part, i = "", 0
    while i < len(palabras):
        cand = (t_part + " " + palabras[i]).strip()
        if len(cand) <= MAX_TITULO:
            t_part = cand; i += 1
        else:
            break
    h_part = ""
    while i < len(palabras):
        cand = (h_part + " " + palabras[i]).strip()
        if len(cand) <= MAX_HIGHLIGHT:
            h_part = cand; i += 1
        else:
            break
    return t_part, h_part, " ".join(palabras[i:])


@st.cache_data(show_spinner=False)
def traducir(texto: str, origen: str, destino: str) -> str:
    if not texto or origen == destino:
        return texto
    try:
        return GoogleTranslator(source=origen, target=destino).translate(texto)
    except Exception:
        return texto  # si falla, devuelve el original para revisión manual


def procesar_idioma(texto_origen: str, lang_origen: str, lang_salida: str):
    """Limpia, (traduce si procede), capitaliza y divide. Devuelve dict de columnas."""
    base = limpiar(texto_origen, lang_origen)
    if lang_salida != lang_origen:
        base = traducir(base, lang_origen, lang_salida)
        base = limpiar(base, lang_salida)
    base = capitalizar(base, lang_salida)
    titulo, highlight, sobrante = dividir(base)
    suf = lang_salida.upper()
    return {
        f"titulo_{suf}": titulo,
        f"len_titulo_{suf}": len(titulo),
        f"highlight_{suf}": highlight,
        f"len_highlight_{suf}": len(highlight),
        f"sobrante_{suf}": sobrante,
        f"revisar_{suf}": "SÍ" if sobrante else "",
    }


# ─────────── INTERFAZ ───────────
st.set_page_config(page_title="Optimizador de títulos Amazon", page_icon="🛒")
st.title("🛒 Optimizador de títulos Amazon (75/125)")
st.caption("Columnas esperadas: 1ª SKU · 2ª ASIN · 3ª Título a procesar")

archivo = st.file_uploader("Sube tu Excel o CSV", type=["xlsx", "csv"])

idioma_in = st.selectbox("Idioma de entrada del título", list(IDIOMAS.keys()))
lang_in = IDIOMAS[idioma_in]

destinos = [lang_in]  # por defecto, salida en el mismo idioma
if lang_in == "es":
    modo = st.radio("¿Qué quieres hacer?",
                    ["Solo optimizar (ES)", "Optimizar y además traducir"])
    if modo == "Optimizar y además traducir":
        seleccion = st.multiselect("Traducir a:", ["Francés (FR)", "Italiano (IT)", "Alemán (DE)"])
        destinos = ["es"] + [IDIOMAS[s] for s in seleccion]
else:
    st.info(f"Se optimizará manteniendo el idioma de salida en {idioma_in}.")

if archivo and st.button("🚀 Procesar"):
    if archivo.name.lower().endswith(".csv"):
        df = pd.read_csv(archivo, dtype=str).fillna("")
    else:
        df = pd.read_excel(archivo, dtype=str).fillna("")

    if df.shape[1] < 3:
        st.error("El archivo debe tener al menos 3 columnas (SKU, ASIN, Título).")
        st.stop()

    col_sku, col_asin, col_tit = df.columns[0], df.columns[1], df.columns[2]
    filas = []
    barra = st.progress(0.0)
    for n, (_, fila) in enumerate(df.iterrows()):
        registro = {"sku": fila[col_sku], "asin": fila[col_asin]}
        for lang_out in destinos:
            registro.update(procesar_idioma(fila[col_tit], lang_in, lang_out))
        filas.append(registro)
        barra.progress((n + 1) / len(df))

    resultado = pd.DataFrame(filas)
    st.success(f"✅ Procesadas {len(resultado)} filas.")
    st.dataframe(resultado, use_container_width=True)

    buffer = io.BytesIO()
    resultado.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button("⬇️ Descargar resultado (Excel)",
                       data=buffer,
                       file_name="titulos_procesados.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
