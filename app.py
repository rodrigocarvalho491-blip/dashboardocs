import os
from PIL import Image
from fpdf import FPDF
import streamlit as st
import streamlit.components.v1 as components

# 1. Resolução de caminhos absolutos
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(DIRETORIO_ATUAL, "logo.png")
LOGO2_PATH = os.path.join(DIRETORIO_ATUAL, "logo2.png")

st.set_page_config(page_title="Relatório Fotográfico", page_icon="📷", layout="wide")

# --- IDENTIDADE VISUAL CONSIGAZ ---
CUSTOM_CSS = """

"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Inicializa as variáveis de controle no session_state
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

if "equipamentos" not in st.session_state:
    st.session_state.equipamentos = []

# Função MESTRE para limpar todos os dados e reiniciar o app
def resetar_dados():
    st.session_state.reset_counter += 1
    st.session_state.equipamentos = []

rc = st.session_state.reset_counter

# --- CABEÇALHO DO APP COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.caption("📷 *Adicione 'logo.png' na pasta do projeto*")

with col_titulo:
    st.title("Relatório Fotográfico & Equipamentos")
    st.markdown("Gerador automatizado de relatórios técnicos.")

st.divider()

# --- BOTÃO FLUTUANTE VIA JAVASCRIPT ---
st.button("🔄 Novo Cliente", on_click=resetar_dados)

# Injetamos JavaScript para forçar o botão "Novo Cliente" a flutuar no canto inferior direito
JS_FLUTUANTE = """

"""
components.html(JS_FLUTUANTE, height=0, width=0)

# --- SEÇÃO 1: DADOS DO CLIENTE ---
st.subheader("1. Identificação do Cliente")
col_c1, col_c2 = st.columns(2)

with col_c1:
    cod_cliente = st.text_input("Código do Cliente", placeholder="Ex: 87.653", key=f"input_cod_{rc}")
with col_c2:
    nome_cliente = st.text_input("Nome / Razão Social", placeholder="Ex: SABOR DA TERRA ALIMENTACAO CORPORATIVA", key=f"input_nome_{rc}")

st.divider()

# --- SEÇÃO 2: UPLOAD DE FOTOS ---
def carregar_fotos(label, max_arquivos=None):
    fotos = st.file_uploader(label, type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"uploader_{label}_{rc}")
    if max_arquivos and fotos and len(fotos) > max_arquivos:
        st.error(f"⚠️ Limite excedido para {label}. Serão considerados apenas os primeiros {max_arquivos} arquivos.")
        return fotos[:max_arquivos]
    return fotos

st.subheader("2. Upload de Imagens do Relatório")
col_f1, col_f2 = st.columns(2)
with col_f1:
    fotos_fachada = carregar_fotos("FACHADA", max_arquivos=2)
    fotos_central = carregar_fotos("CENTRAL", max_arquivos=5)
    fotos_cilindros = carregar_fotos("CILINDROS", max_arquivos=5)
with col_f2:
    fotos_abrigo = carregar_fotos("ABRIGO", max_arquivos=10)
    fotos_equipamentos = carregar_fotos("EQUIPAMENTOS", max_arquivos=None)

st.divider()

# --- SEÇÃO 3: CADASTRO DE EQUIPAMENTOS ---
st.subheader("3. Cadastro de Equipamentos")

col_qtd, col_eq, col_vaz, col_btn = st.columns([1, 2, 2, 1])

with col_qtd:
    qtd_input = st.number_input("Quantidade", min_value=1, value=1, step=1, key=f"eq_qtd_{rc}")
with col_eq:
    nome_eq_input = st.text_input("Equipamento", placeholder="Ex: Forno Industrial", key=f"eq_nome_{rc}")
with col_vaz:
    vazao_input = st.text_input("Vazão Unitária (kg/h)", placeholder="Ex: 1 ou 1,6", key=f"eq_vazao_{rc}")

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("➕ Adicionar", key=f"btn_add_eq_{rc}"):
        if nome_eq_input.strip() and vazao_input.strip():
            try:
                vazao_clean_str = vazao_input.replace(",", ".").lower().replace("kg/h", "").strip()
                vazao_unit = float(vazao_clean_str)
                qtd = int(qtd_input)
                
                vazao_total_item = vazao_unit * qtd
                vazao_formatada = f"{vazao_total_item:.2f}".replace(".", ",").rstrip("0").rstrip(",")

                item_dict = {
                    "qtd": qtd,
                    "nome": nome_eq_input.strip().upper(),
                    "vazao_unit": vazao_unit,
                    "vazao_total_item": vazao_total_item,
                    "texto": f"{qtd:02d} - {nome_eq_input.strip().upper()} - {vazao_formatada} kg/h"
                }
                st.session_state.equipamentos.append(item_dict)
                st.success("Adicionado!")
            except ValueError:
                st.error("Informe um valor numérico válido para a vazão.")
        else:
            st.warning("Preencha o equipamento e a vazão.")

if st.session_state.equipamentos:
    st.write("**Lista de Equipamentos Cadastrados:**")
    total_vazao = 0.0
    
    for idx, item in enumerate(st.session_state.equipamentos):
        total_vazao += item["vazao_total_item"]
        
        c_txt, c_del = st.columns([5, 1])
        c_txt.text(item["texto"])
        if c_del.button("❌", key=f"del_{idx}_{rc}"):
            st.session_state.equipamentos.pop(idx)
            st.rerun()

    vazao_total_str = f"{total_vazao:.2f}".replace(".", ",").rstrip("0").rstrip(",")
    st.markdown(f"**VAZÃO TOTAL: {vazao_total_str} kg/h**")

st.divider()

# --- SEÇÃO 4: GERAÇÃO DO RELATÓRIO PDF ---
class RelatorioPDF(FPDF):
    def __init__(self, cod_cliente="", nome_cliente=""):
        super().__init__()
        self.cod_cliente = cod_cliente.replace(".", "").strip().upper() if cod_cliente else ""
        self.nome_cliente = nome_cliente.strip().upper() if nome_cliente else ""

    def header(self):
        if os.path.exists(LOGO2_PATH):
            self.image(LOGO2_PATH, x=10, y=8, w=45)

        if self.page_no() == 1:
            self.set_y(10)
            self.set_font("Arial", "B", 15)
            # Título principal do PDF em Azul
            self.set_text_color(0, 51, 160)
            self.cell(0, 8, "RELATÓRIO DE FOTOS", align="C", ln=1)
            
            info_cabecalho = f"{self.cod_cliente} | {self.nome_cliente}".strip(" |")
            if info_cabecalho:
                self.set_font("Arial", "B", 11)
                self.set_text_color(0, 0, 0)
                self.cell(0, 6, info_cabecalho, align="C", ln=1)
            
            self.set_y(35)
        else:
            self.set_y(35)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

def gerar_pdf(equipamentos, dic_fotos, cod_cliente, nome_cliente):
    pdf = RelatorioPDF(cod_cliente, nome_cliente)
    pdf.set_margins(10, 35, 10)
    pdf.set_auto_page_break(auto=True, margin=20)

    for categoria, arquivos in dic_fotos.items():
        if arquivos:
            pdf.add_page()
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(0, 51, 160) # Azul Consigaz nos Títulos
            pdf.cell(0, 6, categoria.upper(), ln=1, align="L")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
            
            for idx, arq in enumerate(arquivos):
                try:
                    img = Image.open(arq)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    temp_path = f"temp_{categoria}_{idx}.jpg"
                    img.save(temp_path)
                    
                    pdf.image(temp_path, x="C", w=130)
                    pdf.ln(3)
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception as e:
                    pdf.cell(0, 6, f"Erro ao processar imagem: {e}", ln=1, align="L")

    if equipamentos:
        pdf.add_page()
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(0, 51, 160)
        pdf.cell(0, 6, "LISTA DE EQUIPAMENTOS E VAZÕES", ln=1, align="L")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(0, 51, 160) # Azul no cabeçalho da tabela
        pdf.set_text_color(255, 255, 255) # Texto branco
        pdf.cell(20, 7, "QTD", border=1, align="C", fill=True)
        pdf.cell(120, 7, "EQUIPAMENTO", border=1, align="C", fill=True)
        pdf.cell(50, 7, "VAZÃO TOTAL (KG/H)", border=1, align="C", fill=True, ln=1)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0, 0, 0)
        total_vazao = 0.0
        for item in equipamentos:
            total_vazao += item["vazao_total_item"]
            vazao_item_str = f"{item['vazao_total_item']:.2f}".replace(".", ",").rstrip("0").rstrip(",")
            if not vazao_item_str or vazao_item_str == ",":
                vazao_item_str = "0"
            
            pdf.cell(20, 6, f"{item['qtd']:02d}", border=1, align="C")
            pdf.cell(120, 6, f"{item['nome']}", border=1, align="L")
            pdf.cell(50, 6, f"{vazao_item_str} kg/h", border=1, align="C", ln=1)
        
        vazao_total_str = f"{total_vazao:.2f}".replace(".", ",").rstrip("0").rstrip(",")
        if not vazao_total_str or vazao_total_str == ",":
            vazao_total_str = "0"

        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(140, 7, "VAZÃO TOTAL:", border=1, align="R", fill=True)
        pdf.cell(50, 7, f"{vazao_total_str} kg/h", border=1, align="C", fill=True, ln=1)

    if pdf.page_no() == 0:
        pdf.add_page()

    return bytes(pdf.output())

st.subheader("4. Geração do Relatório")

if st.button("📄 Gerar Relatório PDF"):
    dicionario_fotos = {
        "FACHADA": fotos_fachada,
        "ABRIGO": fotos_abrigo,
        "CENTRAL": fotos_central,
        "CILINDROS": fotos_cilindros,
        "EQUIPAMENTOS": fotos_equipamentos
    }
    
    pdf_out = gerar_pdf(
        st.session_state.equipamentos,
        dicionario_fotos,
        cod_cliente,
        nome_cliente
    )
    
    cod_formatado = cod_cliente.replace(".", "").strip().upper() if cod_cliente else ""
    nome_arquivo_pdf = f"fotos_{cod_formatado}.pdf" if cod_formatado else "fotos.pdf"

    st.success("✅ Relatório gerado com sucesso!")
    st.download_button(
        label="📥 Baixar Relatório (PDF)",
        data=pdf_out,
        file_name=nome_arquivo_pdf,
        mime="application/pdf"
    )
