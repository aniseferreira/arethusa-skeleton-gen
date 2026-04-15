import streamlit as st
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Arethusa XML Skeleton", layout="centered")

# --- A FUNÇÃO (O NOME AQUI É: generate_xml) ---
def generate_xml(texto_sujo, name, email, urn, subdoc_base):
    root = ET.Element("treebank")
    root.set("xmlns:saxon", "http://saxon.sf.net/")
    root.set("xml:lang", "grc")
    root.set("version", "1.5")
    root.set("direction", "ltr")
    root.set("format", "smyth3")

    date_node = ET.SubElement(root, "date")
    date_node.text = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    uris = ["http://github.com/latin-language-toolkit/arethusa", 
            "http://services2.perseids.org/llt/segtok", 
            "http://github.com/latin-language-toolkit/arethusa"]
    
    for uri in uris:
        ann = ET.SubElement(root, "annotator")
        ET.SubElement(ann, "short")
        ET.SubElement(ann, "name")
        ET.SubElement(ann, "address")
        ET.SubElement(ann, "uri").text = uri

    ann_user = ET.SubElement(root, "annotator")
    short_name = name.split()[0].lower() if name else "user"
    ET.SubElement(ann_user, "short").text = short_name
    ET.SubElement(ann_user, "name").text = name
    ET.SubElement(ann_user, "address").text = email
    ET.SubElement(ann_user, "uri").text = f"http://data.perseus.org/sosol/users/{short_name}"

    lines = [l.strip() for l in texto_sujo.split('\n') if l.strip()]
    
    for i, line in enumerate(lines, 1):
        match = re.match(r'^(\d+)\s+(.*)', line)
        if match:
            line_num, line_text = match.groups()
        else:
            line_num, line_text = str(i), line

        # REGEX ATUALIZADA: Agora inclui ' e \u2019 (corônis/apóstrofo curvo) como parte da palavra
        tokens = re.findall(r"[\w\u0370-\u03FF\u1F00-\u1FFF'’]+|[.,;:·!?]", line_text)
        
        # Uso dos novos campos de URN e Subdoc
        sentence_subdoc = f"{subdoc_base}.{i}" if subdoc_base else f"1-{i}"
        sentence = ET.SubElement(root, "sentence", id=str(i), document_id=urn, subdoc=sentence_subdoc, span="")
        
        # Word 1: Número da linha/referência
        ET.SubElement(sentence, "word", id="1", form=line_num, lemma="", postag="", relation="", sg="", head="")
        
        for j, token in enumerate(tokens, 2):
            is_end = token in [".", "·", ";", "!", "·"]
            ET.SubElement(sentence, "word", id=str(j), form=token, lemma="", postag="", relation="AuxK" if is_end else "", sg="", head="0" if is_end else "")

    return ET.tostring(root, encoding='utf-8')

# --- INTERFACE ---
st.title("🏛️ Arethusa Skeleton Generator")

with st.expander("👤 Configurações do Anotador e Documento"):
    u_name = st.text_input("Nome:", value="Seu nome")
    u_email = st.text_input("E-mail:", value="seu email")
    st.divider()
    u_urn = st.text_input("URN / Document ID:", value="urn:cts:greekLit:arethusa.skeleton")
    u_subdoc = st.text_input("Subdoc / Passagem inicial (opcional):", placeholder="Ex: 1.3")

input_text = st.text_area("Cole as sentenças gregas, uma por linha:", height=300)

if st.button("GERAR XML 🚀"):
    if input_text:
        # Passando os novos parâmetros para a função
        result = generate_xml(input_text, u_name, u_email, u_urn, u_subdoc)
        
        st.download_button(
            label="📥 Baixar XML",
            data=result,
            file_name="skeleton.xml",
            mime="application/xml",
            use_container_width=True
        )
        
        # Tabela de conferência (também atualizada com a nova regex)
        preview_data = []
        for i, linha in enumerate(input_text.split('\n'), 1):
            if linha.strip():
                # Aplicando a mesma lógica de tokens aqui para a tabela ficar igual ao XML
                tokens = re.findall(r"[\w\u0370-\u03FF\u1F00-\u1FFF'’]+|[.,;:·!?]", linha)
                for t in tokens:
                    preview_data.append({"Sentença": i, "Palavra": t})
        
        st.write("### Prévia dos Tokens:")
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
    else:
        st.error("Cole o texto grego primeiro!")
