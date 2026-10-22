import os
import json
import base64
import html as html_lib
import uuid
import tempfile
import pandas as pd
import numpy as np
import streamlit as st
import requests
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import streamlit.components.v1 as components

# --- FORÇAR TEMA CLARO NATIVO NO STREAMLIT ---
os.makedirs(".streamlit", exist_ok=True)
config_path = os.path.join(".streamlit", "config.toml")
if not os.path.exists(config_path):
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(
            '[theme]\n'
            'base="light"\n'
            'primaryColor="#0055A5"\n'
            'backgroundColor="#FFFFFF"\n'
            'secondaryBackgroundColor="#F8FAFC"\n'
            'textColor="#1E293B"\n'
        )

# --- CONFIGURAÇÃO GLOBAL DA PÁGINA ---
st.set_page_config(
    page_title="Sistema Integrado | Consigaz", 
    page_icon="🔥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(DIRETORIO_ATUAL, "logo.png")
LOGO2_PATH = os.path.join(DIRETORIO_ATUAL, "logo2.png")

# =====================================================================
# IDENTIDADE VISUAL CONSIGAZ - TEMA CLARO, LIMPO E COM BORDAS DELICADAS
# =====================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
  background-color: #FFFFFF !important;
  color: #1E293B !important;
}

[data-testid="stHeader"] { display: none !important; visibility: hidden !important; }
#MainMenu, footer { visibility: hidden; }

/* Forçar estilo limpo com bordas delicadas em inputs, caixas e uploader */
div.stTextInput > div > div > input,
div.stNumberInput > div > div > input,
div.stSelectbox > div > div > div,
div.stTextArea > div > div > textarea {
  background-color: #FFFFFF !important;
  color: #1E293B !important;
  border: 1px solid rgba(120, 140, 160, 0.25) !important;
  border-radius: 8px !important;
}

div[data-testid="stFileUploader"] {
  background-color: #FFFFFF !important;
  border: 1px dashed rgba(120, 140, 160, 0.4) !important;
  border-radius: 10px !important;
  padding: 10px;
}

/* Cabeçalho Consigaz */
.cg-header { 
  display: flex; 
  align-items: center; 
  gap: 1.5rem; 
  position: relative;
  padding-bottom: 1.2rem; 
  margin-bottom: 2rem; 
  border-bottom: 2px solid #E2E8F0; 
}
.cg-header::after { 
  content: ""; 
  position: absolute; 
  left: 0; 
  bottom: -2px; 
  width: 140px; 
  height: 4px; 
  border-radius: 4px; 
  background: linear-gradient(90deg, #0055A5 0%, #F28C28 100%); 
}

.cg-logo-wrapper {
  background: #FFFFFF;
  padding: 6px 12px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #E2E8F0;
}
.cg-logo { height: 55px; width: auto; display: block; }

.cg-header-sep { width: 2px; align-self: stretch; background: #E2E8F0; }
.cg-title { font-size: 1.65rem; font-weight: 800; line-height: 1.2; color: #003366 !important; }
.cg-subtitle { font-size: 0.95rem; margin-top: 0.2rem; color: #64748B !important; font-weight: 500; }

/* Títulos de Seção */
.stApp h3 {
  font-size: 1.1rem !important;
  font-weight: 700 !important;
  color: #003366 !important;
  padding: 0.2rem 0 0.2rem 0.6rem !important;
  border-left: 4px solid #F28C28 !important;
  margin-top: 1.5rem !important;
  margin-bottom: 1rem !important;
}

/* Sidebar Estilizada */
[data-testid="stSidebar"] {
  background-color: #F8FAFC !important;
  border-right: 1px solid #E2E8F0;
}
.cg-side-brand { 
  padding: 0.8rem 0.5rem 1.2rem 0.5rem; 
  margin-bottom: 1rem; 
  border-bottom: 1px solid #E2E8F0; 
  text-align: center;
}
.cg-side-logo-wrapper {
  background: #FFFFFF;
  padding: 6px 10px;
  border-radius: 8px;
  display: inline-block;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.cg-side-logo { height: 38px; width: auto; display: inline-block; }
.cg-side-name { margin-top: 0.6rem; font-size: 0.7rem; font-weight: 700; color: #64748B !important; letter-spacing: 0.08em; text-transform: uppercase; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def _logo_base64(caminho):
    try:
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""

def _logo_html(classe_img, classe_wrapper=""):
    b64 = _logo_base64(LOGO_PATH)
    if not b64:
        return ""
    img_tag = f'<img class="{classe_img}" src="data:image/png;base64,{b64}" alt="Consigaz">'
    if classe_wrapper:
        return f'<div class="{classe_wrapper}">{img_tag}</div>'
    return img_tag

def cabecalho_pagina(titulo, subtitulo):
    logo = _logo_html("cg-logo", "cg-logo-wrapper")
    separador = '<div class="cg-header-sep"></div>' if logo else ""
    st.markdown(
        f'<div class="cg-header">{logo}{separador}<div>'
        f'<div class="cg-title">{html_lib.escape(titulo)}</div>'
        f'<div class="cg-subtitle">{html_lib.escape(subtitulo)}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

# --- MAPEAMENTO DAS COLUNAS DO EXCEL ---
COL_OCORRENCIA = "Número da ocorrência"
COL_CLIENTE = "Nome do cliente"
COL_ENDERECO = "Endereço de Entrega"
COL_ABERTURA = "Data/Hora de abertura"
COL_PRAZO = "Prazo de Atendimento"
COL_FECHAMENTO = "Data/Hora de fechamento"
COL_SUB_CLASSIF = "Subclassificação Ocorrência"

# Inicialização do Session State
if "tratadas_manualmente" not in st.session_state:
    st.session_state.tratadas_manualmente = set()

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

if "reset_counter_contrato" not in st.session_state:
    st.session_state.reset_counter_contrato = 0

if "eq_key_counter" not in st.session_state:
    st.session_state.eq_key_counter = 0

if "equipamentos" not in st.session_state:
    st.session_state.equipamentos = []

if "last_central" not in st.session_state:
    st.session_state.last_central = "Central"

if "last_tipo_cad" not in st.session_state:
    st.session_state.last_tipo_cad = "Equipamentos"

def resetar_dados_cliente():
    st.session_state.reset_counter += 1
    st.session_state.eq_key_counter = 0
    st.session_state.equipamentos = []
    st.session_state.last_central = "Central"
    st.session_state.last_tipo_cad = "Equipamentos"

def resetar_dados_contrato():
    st.session_state.reset_counter_contrato += 1

# Função para extrair cidade limpa
def extrair_cidade(endereco):
    if pd.isna(endereco):
        return "-"
    s = str(endereco).strip()
    s_norm = s.replace(';', ',').replace('|', ',')
    partes = [p.strip() for p in s_norm.split(',')]
    if len(partes) >= 2:
        cidade = partes[-2].strip()
        if cidade.isdigit() and len(partes) >= 3:
            cidade = partes[-3].strip()
        return cidade.title()
    return s.title()

def calcular_dias_uteis(data_inicio, data_fim):
    h = pd.Timestamp(data_inicio).normalize().date()
    p = pd.Timestamp(data_fim).normalize().date()
    if p > h:
        return int(np.busday_count(h, p))
    elif p < h:
        return -int(np.busday_count(p, h))
    else:
        return 0

def classificar_status_geral(dias_uteis):
    if dias_uteis < 0:
        return "🔴 Vencido"
    elif dias_uteis == 0:
        return "🔵 Vence Hoje"
    elif dias_uteis == 1:
        return "🟠 Vence Amanhã"
    elif 2 <= dias_uteis <= 5: 
        return "🟡 Vence na Semana"
    else:
        return "🟢 No Prazo"

# --- IPCA VIA API OFICIAL ---
IPCA_VALOR_RESERVA = 4.58

@st.cache_data(ttl=3600, show_spinner=False)
def obter_ipca_acumulado_12m():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sugestao.433/dados/ultimos/1?formato=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            if dados and len(dados) > 0:
                return float(str(dados[0].get("valor", 4.58)).replace(",", ".")), "recente"
    except Exception:
        pass
    return 4.58, "recente"

# --- MENU LATERAL DE NAVEGAÇÃO ---
side_logo_html = _logo_html("cg-side-logo", "cg-side-logo-wrapper")
st.sidebar.markdown(
    f'<div class="cg-side-brand">{side_logo_html}'
    f'<div class="cg-side-name">Central de Atendimentos</div></div>',
    unsafe_allow_html=True,
)
menu = st.sidebar.radio(
    "Selecione a página:",
    [
        "📊 Dashboard de Ocorrências",
        "📷 Visita de Transferência",
        "📝 Elaboração de Contrato",
        "🎂 Aniversário de Contrato"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()
if st.sidebar.button("🔄 Novo Cliente / Limpar"):
    resetar_dados_cliente()
    resetar_dados_contrato()
    st.rerun()


# =====================================================================
# TELA 0: DASHBOARD DE OCORRÊNCIAS COM MINI MAPA VISUAL
# =====================================================================
if menu == "📊 Dashboard de Ocorrências":
    cabecalho_pagina("Gestão de Ocorrências & Visitas", "Painel de organização de agenda ordenado por prazo de atendimento (Dias Úteis).")

    st.divider()

    st.subheader("1. Atualização de Dados")
    arquivo_excel = st.file_uploader("Faça o upload do relatório Excel (Pós-Vendas) 📂", type=["xlsx", "xls"])

    st.divider()

    if arquivo_excel is not None:
        try:
            df = pd.read_excel(arquivo_excel, header=11)
            df = df.dropna(subset=[COL_OCORRENCIA])
            
            df_pendentes = df[df[COL_FECHAMENTO].isna()].copy()
            df_pendentes[COL_OCORRENCIA] = df_pendentes[COL_OCORRENCIA].astype(int)
            df_pendentes = df_pendentes[~df_pendentes[COL_OCORRENCIA].isin(st.session_state.tratadas_manualmente)]
            
            df_pendentes['Prazo_DT'] = pd.to_datetime(df_pendentes[COL_PRAZO], format="%d/%m/%Y %H:%M", errors='coerce')
            df_pendentes = df_pendentes.dropna(subset=['Prazo_DT'])
            
            df_pendentes['Cidade'] = df_pendentes[COL_ENDERECO].apply(extrair_cidade)
            df_pendentes[COL_SUB_CLASSIF] = df_pendentes[COL_SUB_CLASSIF].fillna("-").astype(str)
            
            hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            df_pendentes['Dias Úteis Restantes'] = df_pendentes['Prazo_DT'].apply(lambda x: calcular_dias_uteis(hoje, x))
            df_pendentes['Status Geral'] = df_pendentes['Dias Úteis Restantes'].apply(classificar_status_geral)
            df_pendentes = df_pendentes.sort_values(by='Prazo_DT', ascending=True)
            
            st.subheader("2. Agenda Geral de Visitas Pendentes")
            
            st.markdown("### Filtros de Visualização")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                mostrar_so_hoje = st.toggle("📅 Mostrar apenas ocorrências com prazo PARA HOJE", value=False)
            with col_t2:
                mostrar_so_semana = st.toggle("🗓️ Mostrar apenas os próximos 5 dias úteis", value=False)
            
            cidades_unicas = sorted(list(df_pendentes['Cidade'].unique()))
            sub_class_unicas = sorted(list(df_pendentes[COL_SUB_CLASSIF].unique()))
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                cidades_selecionadas = st.multiselect("Filtrar por Cidade(s):", cidades_unicas, default=[], key="filtro_cidade")
            with col_f2:
                sub_class_selecionadas = st.multiselect("Filtrar por Sub-Classificação:", sub_class_unicas, default=[], key="filtro_sub")
            
            df_filtrado = df_pendentes.copy()
            
            if mostrar_so_hoje:
                hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                hoje_fim = hoje_inicio + timedelta(days=1) - timedelta(seconds=1)
                df_filtrado = df_filtrado[(df_filtrado['Prazo_DT'] >= hoje_inicio) & (df_filtrado['Prazo_DT'] <= hoje_fim)]
            elif mostrar_so_semana:
                df_filtrado = df_filtrado[(df_filtrado['Dias Úteis Restantes'] >= 0) & (df_filtrado['Dias Úteis Restantes'] <= 5)]
                
            if cidades_selecionadas:
                df_filtrado = df_filtrado[df_filtrado['Cidade'].isin(cidades_selecionadas)]
                
            if sub_class_selecionadas:
                df_filtrado = df_filtrado[df_filtrado[COL_SUB_CLASSIF].isin(sub_class_selecionadas)]
            
            df_filtrado['Data Atendimento'] = df_filtrado['Prazo_DT'].dt.strftime('%d/%m/%Y')
            
            # Métricas de Resumo
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Visitas Pendentes", len(df_filtrado))
            with col_m2:
                hoje_qt = len(df_filtrado[df_filtrado['Status Geral'] == "🔵 Vence Hoje"])
                st.metric("Vence Hoje", hoje_qt)
            with col_m3:
                amanha_qt = len(df_filtrado[df_filtrado['Status Geral'] == "🟠 Vence Amanhã"])
                st.metric("Vence Amanhã", amanha_qt)
            with col_m4:
                vencidas_qt = len(df_filtrado[df_filtrado['Status Geral'] == "🔴 Vencido"])
                st.metric("Ocorrências Vencidas", vencidas_qt)
            
            st.write("---")

            # --- MINI MAPA VISUAL / GRÁFICO POR CIDADE ---
            st.markdown("### 📊 Distribuição Geográfica por Cidade")
            df_cidades_qtd = df_filtrado['Cidade'].value_counts().reset_index()
            df_cidades_qtd.columns = ['Cidade', 'Quantidade']
            
            col_map1, col_map2 = st.columns([3, 2])
            with col_map1:
                st.markdown("**Volume de Ocorrências por Município:**")
                st.bar_chart(df_cidades_qtd.set_index('Cidade'), color="#0055A5")
                
            with col_map2:
                st.markdown("**Resumo Quantitativo:**")
                st.dataframe(
                    df_cidades_qtd, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "Cidade": st.column_config.TextColumn("Município / Cidade"),
                        "Quantidade": st.column_config.NumberColumn("Qtd. Ocorrências")
                    }
                )

            st.write("---")
            st.markdown("**Lista de Ocorrências Ordenadas (Mais Próxima para a Mais Distante):**")
            
            if df_filtrado.empty:
                st.success("✅ Excelente! Não há nenhuma ocorrência pendente para os filtros selecionados.")
            else:
                df_exibicao = df_filtrado[[
                    'Status Geral',
                    'Dias Úteis Restantes',
                    COL_OCORRENCIA, 
                    COL_CLIENTE, 
                    'Cidade', 
                    COL_SUB_CLASSIF,
                    'Data Atendimento'
                ]].copy()
                df_exibicao[COL_OCORRENCIA] = df_exibicao[COL_OCORRENCIA].astype(str)
                
                edited_df = st.data_editor(
                    df_exibicao.assign(Tratar=False),
                    column_config={
                        "Tratar": st.column_config.CheckboxColumn("✅ Marcar Tratada?", required=True),
                        'Status Geral': st.column_config.TextColumn("Status", width="small", disabled=True),
                        'Dias Úteis Restantes': st.column_config.NumberColumn("Dias Úteis Restantes", width="small", disabled=True),
                        COL_OCORRENCIA: st.column_config.TextColumn("Nº Ocorrência", width="small", disabled=True),
                        COL_CLIENTE: st.column_config.TextColumn("Nome do Cliente", width="large", disabled=True),
                        'Cidade': st.column_config.TextColumn("Cidade", width="small", disabled=True),
                        COL_SUB_CLASSIF: st.column_config.TextColumn("Sub-Classificação", width="medium", disabled=True),
                        'Data Atendimento': st.column_config.TextColumn("Data de Atendimento", width="medium", disabled=True),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="editor_geral"
                )
                
                ocorrencias_para_tratar = edited_df[edited_df["Tratar"] == True][COL_OCORRENCIA].tolist()
                
                if ocorrencias_para_tratar:
                    st.warning(f"⚠️ Você selecionou **{len(ocorrencias_para_tratar)}** ocorrência(s) para marcar como tratada(s).")
                    if st.button("🔒 Confirmar e Remover do Painel", type="primary"):
                        for oc in ocorrencias_para_tratar:
                            st.session_state.tratadas_manualmente.add(int(oc))
                        st.success("✅ Ocorrência(s) tratada(s) com sucesso e removida(s) do painel!")
                        st.rerun()

        except Exception as e:
            st.error(f"⚠️ Ocorreu um erro ao processar o ficheiro. Certifique-se de ser o relatório padrão do sistema. Erro técnico: {e}")

    else:
        st.info("👆 Por favor, faça o upload da folha de cálculo atualizada de ocorrências acima para carregar o dashboard.")


# =====================================================================
# TELA 1: VISITA DE TRANSFERÊNCIA
# =====================================================================
elif menu == "📷 Visita de Transferência":
    rc = st.session_state.reset_counter
    ekc = st.session_state.eq_key_counter

    cabecalho_pagina("Visita de Transferência & Relatório Técnico", "Gerador automatizado de relatórios técnicos e inspeções.")

    st.divider()

    st.subheader("1. Identificação do Cliente")
    s1_l1_c1, s1_l1_c2, s1_l1_c3 = st.columns(3)
    with s1_l1_c1:
        cod_cliente = st.text_input("Código do Cliente *", key=f"input_cod_{rc}")
    with s1_l1_c2:
        nome_cliente = st.text_input("Nome / Razão Social *", key=f"input_nome_{rc}")
    with s1_l1_c3:
        telefone = st.text_input("Telefone *", key=f"input_tel_{rc}")

    s1_l2_c1, s1_l2_c2, s1_l2_c3 = st.columns(3)
    with s1_l2_c1:
        contato = st.text_input("Contato *", key=f"input_contato_{rc}")
    with s1_l2_c2:
        departamento = st.text_input("Sobrenome ou Departamento *", key=f"input_depto_{rc}")
    with s1_l2_c3:
        st.write("")

    st.divider()

    st.subheader("2. Informações Contratuais")
    s2_l1_c1, s2_l1_c2, s2_l1_c3, s2_l1_c4 = st.columns(4)
    with s2_l1_c1:
        eq_contrato = st.radio("Equipamentos de acordo com contrato? *", ["Sim", "Não"], horizontal=True, index=None, key=f"eq_contrato_{rc}")
    with s2_l1_c2:
        desc_eq_contrato = st.text_input("Quais equipamentos disponíveis? *", key=f"desc_eq_contrato_{rc}")
    with s2_l1_c3:
        tem_freq = st.radio("Possui programação cadastrada? *", ["Sim", "Não"], horizontal=True, index=None, key=f"tem_freq_{rc}")
    with s2_l1_c4:
        desc_freq = ""
        if tem_freq == "Sim":
            desc_freq = st.text_input("Qual a programação? *", key=f"freq_cad_sim_{rc}")
        elif tem_freq == "Não":
            desc_freq = st.text_input("Nº OC de Cadastramento *", key=f"freq_cad_nao_{rc}")
        else:
            st.write("")

    s2_l2_c1, s2_l2_c2 = st.columns(2)
    with s2_l2_c1:
        consumo_previsto = st.text_input("Consumo Previsto (kg) *", key=f"cons_prev_{rc}")
    with s2_l2_c2:
        consumo_real = st.text_input("Consumo Real/Médio (kg) *", key=f"cons_real_{rc}")

    s2_l3_c1, s2_l3_c2 = st.columns(2)
    with s2_l3_c1:
        possui_art = st.radio("Possui ART? *", ["Sim", "Não"], horizontal=True, index=None, key=f"possui_art_{rc}")
    with s2_l3_c2:
        desc_art = ""
        if possui_art == "Sim":
            desc_art = st.text_input("Número da ART *", key=f"art_sim_{rc}")
        elif possui_art == "Não":
            desc_art = st.text_input("Nº OC de Solicitação de Laudo *", key=f"art_nao_{rc}")
        else:
            st.write("")

    s2_l4_c1, s2_l4_c2 = st.columns(2)
    with s2_l4_c1:
        possui_debitos = st.radio("Cliente possui débitos? *", ["Sim", "Não"], horizontal=True, index=None, key=f"possui_debitos_{rc}")
    with s2_l4_c2:
        desc_debitos = st.text_input("Detalhes dos Débitos (se houver)", key=f"desc_debitos_{rc}") if possui_debitos == "Sim" else ""

    s2_l5_c1, s2_l5_c2 = st.columns(2)
    with s2_l5_c1:
        central_norma = st.radio("Central dentro de norma? *", ["Sim", "Não"], horizontal=True, index=None, key=f"central_norma_{rc}")
    with s2_l5_c2:
        desc_central_norma = st.text_input("Motivo da Central fora de norma", key=f"desc_central_norma_{rc}") if central_norma == "Não" else ""

    s2_l6_c1, s2_l6_c2 = st.columns(2)
    with s2_l6_c1:
        rep2_correto = st.radio("Representante 2 está correto? *", ["Sim", "Não"], horizontal=True, index=None, key=f"rep2_correto_{rc}")
    with s2_l6_c2:
        desc_rep2 = st.text_input("Nº OC de Regularização", key=f"desc_rep2_{rc}") if rep2_correto == "Não" else ""

    st.divider()

    st.subheader("3. Cadastro de Instalação e Equipamentos")
    col_cent1, col_cent2 = st.columns(2)
    with col_cent1:
        qtd_centrais = st.number_input("Quantidade de Centrais no Cliente", min_value=1, value=1, step=1, key=f"qtd_centrais_{rc}")
    with col_cent2:
        if qtd_centrais > 1:
            opcoes_centrais = [f"Central {i:02d}" for i in range(1, int(qtd_centrais) + 1)]
            idx_central = 0
            if st.session_state.last_central in opcoes_centrais:
                idx_central = opcoes_centrais.index(st.session_state.last_central)
            central_selecionada = st.selectbox("Vincular item à qual Central?", opcoes_centrais, index=idx_central, key=f"sel_central_{rc}_{ekc}")
            st.session_state.last_central = central_selecionada
        else:
            central_selecionada = "Central"
            st.session_state.last_central = "Central"
            st.write("")

    opcoes_tipo = ["Equipamentos", "Cilindros", "Condomínio"]
    idx_tipo = 0
    if st.session_state.last_tipo_cad in opcoes_tipo:
        idx_tipo = opcoes_tipo.index(st.session_state.last_tipo_cad)
    tipo_cadastro = st.radio("Selecione o tipo que deseja adicionar:", opcoes_tipo, index=idx_tipo, horizontal=True, key=f"tipo_cad_{rc}_{ekc}")
    st.session_state.last_tipo_cad = tipo_cadastro

    if tipo_cadastro == "Equipamentos":
        col_qtd, col_eq, col_vaz, col_btn = st.columns([1, 2, 2, 1])
        with col_qtd:
            qtd_input = st.number_input("Quantidade", min_value=1, value=1, step=1, key=f"eq_qtd_{rc}_{ekc}")
        with col_eq:
            nome_eq_input = st.text_input("Equipamento", key=f"eq_nome_{rc}_{ekc}")
        with col_vaz:
            vazao_input = st.text_input("Vazão (kg/h)", key=f"eq_vazao_{rc}_{ekc}")
        with col_btn:
            st.write(" "); st.write(" ")
            if st.button("➕ Adicionar", key=f"btn_add_eq_{rc}_{ekc}"):
                if nome_eq_input.strip() and vazao_input.strip():
                    try:
                        vazao_unit = float(vazao_input.replace(",", ".").lower().replace("kg/h", "").strip())
                        qtd = int(qtd_input)
                        vazao_total_item = vazao_unit * qtd
                        vazao_formatada = f"{vazao_total_item:.2f}".replace(".", ",").rstrip("0").rstrip(",")

                        item_dict = {
                            "central": central_selecionada,
                            "tipo": "equipamento",
                            "qtd": qtd,
                            "nome": nome_eq_input.strip().title(),
                            "vazao_total_item": vazao_total_item,
                            "texto": f"{qtd:02d} - {nome_eq_input.strip().title()} - {vazao_formatada} kg/h"
                        }
                        st.session_state.equipamentos.append(item_dict)
                        st.session_state.eq_key_counter += 1
                        st.success("Item adicionado!")
                        st.rerun()
                    except ValueError:
                        st.error("Informe um número válido para a vazão.")
                else:
                    st.warning("Preencha o nome e a vazão.")

    elif tipo_cadastro == "Cilindros":
        col_qtd, col_mod, col_btn = st.columns([1, 4, 1])
        with col_qtd:
            qtd_input = st.number_input("Qtd", min_value=1, value=1, step=1, key=f"cil_qtd_{rc}_{ekc}")
        with col_mod:
            modelo_input = st.text_input("Modelo", key=f"cil_mod_{rc}_{ekc}")
        with col_btn:
            st.write(" "); st.write(" ")
            if st.button("➕ Adicionar", key=f"btn_add_cil_{rc}_{ekc}"):
                if modelo_input.strip():
                    qtd = int(qtd_input)
                    item_dict = {
                        "central": central_selecionada,
                        "tipo": "cilindro",
                        "qtd": qtd,
                        "nome": f"Cilindro {modelo_input.strip().upper()}",
                        "vazao_total_item": 0.0,
                        "texto": f"{qtd:02d} und {modelo_input.strip().upper()}"
                    }
                    st.session_state.equipamentos.append(item_dict)
                    st.session_state.eq_key_counter += 1
                    st.success("Cilindro adicionado!")
                    st.rerun()

    elif tipo_cadastro == "Condomínio":
        col_local, col_qtd, col_tipo, col_btn = st.columns([2, 1, 3, 1])
        with col_local:
            local_input = st.selectbox("Local", ["Apartamentos", "Área Comum"], key=f"cond_local_{rc}_{ekc}")
        with col_qtd:
            qtd_input = st.number_input("Qtd", min_value=1, value=1, step=1, key=f"cond_qtd_{rc}_{ekc}")
        with col_tipo:
            tipo_apt_input = st.selectbox("Instalação", ["Só Fogão", "Fogão + Aquecedor"], key=f"cond_tipo_{rc}_{ekc}")
        with col_btn:
            st.write(" "); st.write(" ")
            if st.button("➕ Adicionar", key=f"btn_add_cond_{rc}_{ekc}"):
                qtd = int(qtd_input)
                vazao_unit = 0.1 if tipo_apt_input == "Só Fogão" else 0.4
                vazao_total = vazao_unit * qtd
                texto = f"{qtd:02d} aps - {tipo_apt_input}" if local_input == "Apartamentos" else f"{qtd:02d} - Área Comum ({tipo_apt_input})"
                
                item_dict = {
                    "central": central_selecionada,
                    "tipo": "condominio",
                    "qtd": qtd,
                    "nome": f"Condomínio ({tipo_apt_input})",
                    "vazao_total_item": vazao_total,
                    "texto": texto
                }
                st.session_state.equipamentos.append(item_dict)
                st.session_state.eq_key_counter += 1
                st.success("Condomínio adicionado!")
                st.rerun()

    if st.session_state.equipamentos:
        st.write("**Itens Cadastrados:**")
        def get_c_name(item, q):
            return "Central" if q == 1 else item.get("central", "Central")
        
        centrais_presentes = sorted(list(set([get_c_name(item, qtd_centrais) for item in st.session_state.equipamentos])))
        for c_nome in centrais_presentes:
            st.markdown(f"**{c_nome.upper()}**")
            vazao_c = 0.0
            for idx, item in enumerate(st.session_state.equipamentos):
                if get_c_name(item, qtd_centrais) == c_nome:
                    vazao_c += item["vazao_total_item"]
                    c_txt, c_del = st.columns([5, 1])
                    c_txt.text(item["texto"])
                    if c_del.button("❌", key=f"del_{idx}_{rc}"):
                        st.session_state.equipamentos.pop(idx)
                        st.rerun()
            v_str = f"{vazao_c:.2f}".replace(".", ",").rstrip("0").rstrip(",") if vazao_c > 0 else "0"
            st.markdown(f"*Vazão Total {c_nome}: {v_str} kg/h*")

    st.divider()

    st.subheader("4. Satisfação & Observações")
    s4_l1_c1, s4_l1_c2 = st.columns(2)
    with s4_l1_c1:
        indica_negocios = st.radio("Indicou novos negócios? *", ["Sim", "Não"], horizontal=True, index=None, key=f"ind_neg_{rc}")
    with s4_l1_c2:
        cliente_satisfeito = st.radio("Cliente satisfeito com a Consigaz? *", ["Sim", "Não"], horizontal=True, index=None, key=f"cli_sat_{rc}")

    observacoes = st.text_area("Observações Gerais", key=f"obs_{rc}")

    st.divider()

    st.subheader("5. Relatório Fotográfico")
    def carregar_fotos(label, max_arq=None):
        fotos = st.file_uploader(label, type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"up_{label}_{rc}")
        if max_arq and fotos and len(fotos) > max_arq:
            return fotos[:max_arq]
        return fotos

    dic_fotos_final = {}
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        dic_fotos_final["FACHADA"] = carregar_fotos("FACHADA", 2)
    with col_f2:
        dic_fotos_final["CILINDROS"] = carregar_fotos("CILINDROS", 5)

    if qtd_centrais == 1:
        c1, c2, c3 = st.columns(3)
        with c1: dic_fotos_final["ABRIGO"] = carregar_fotos("ABRIGO", 10)
        with c2: dic_fotos_final["CENTRAL"] = carregar_fotos("CENTRAL", 5)
        with c3: dic_fotos_final["EQUIPAMENTOS"] = carregar_fotos("EQUIPAMENTOS")
    else:
        for i in range(1, int(qtd_centrais) + 1):
            st.markdown(f"**📸 CENTRAL {i:02d}**")
            c1, c2, c3 = st.columns(3)
            with c1: dic_fotos_final[f"ABRIGO CENTRAL {i:02d}"] = carregar_fotos(f"ABRIGO CENTRAL {i:02d}", 10)
            with c2: dic_fotos_final[f"CENTRAL {i:02d}"] = carregar_fotos(f"CENTRAL {i:02d}", 5)
            with c3: dic_fotos_final[f"EQUIPAMENTOS CENTRAL {i:02d}"] = carregar_fotos(f"EQUIPAMENTOS CENTRAL {i:02d}")

    st.divider()

    class RelatorioPDF(FPDF):
        def __init__(self, cod="", nome=""):
            super().__init__()
            self.cod = cod.replace(".", "").strip().upper()
            self.nome = nome.strip().upper()

        def header(self):
            if os.path.exists(LOGO2_PATH):
                self.image(LOGO2_PATH, x=10, y=8, w=45)
            if self.page_no() == 1:
                self.set_y(10)
                self.set_font("Arial", "B", 15)
                self.cell(0, 8, "RELATÓRIO FOTOGRÁFICO", align="C", ln=1)
                if self.cod or self.nome:
                    self.set_font("Arial", "B", 11)
                    self.cell(0, 6, f"{self.cod} | {self.nome}", align="C", ln=1)
                self.set_y(35)
            else:
                self.set_y(35)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def gerar_pdf(equipamentos, dic_fotos, cod, nome, qty_c):
        pdf = RelatorioPDF(cod, nome)
        pdf.set_margins(10, 35, 10)
        pdf.set_auto_page_break(auto=True, margin=20)

        for cat, arquivos in dic_fotos.items():
            if arquivos:
                pdf.add_page()
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 6, cat.upper(), ln=1, align="L")
                pdf.ln(2)
                for idx, arq in enumerate(arquivos):
                    t_path = None
                    try:
                        img = Image.open(arq)
                        if img.mode != "RGB": img = img.convert("RGB")

                        fd, t_path = tempfile.mkstemp(suffix=f"_{uuid.uuid4().hex}.jpg")
                        os.close(fd)
                        img.save(t_path, format="JPEG")

                        w_p, h_p = img.size
                        prop = h_p / w_p
                        w_alv = 130
                        h_alv = w_alv * prop
                        if h_alv > 110:
                            h_alv = 110
                            w_alv = h_alv / prop
                        pos_x = (210 - w_alv) / 2
                        if pdf.get_y() + h_alv > 270: pdf.add_page()
                        pdf.image(t_path, x=pos_x, y=pdf.get_y(), w=w_alv, h=h_alv)
                        pdf.set_y(pdf.get_y() + h_alv + 5)
                    except Exception:
                        pass
                    finally:
                        if t_path and os.path.exists(t_path):
                            try:
                                os.remove(t_path)
                            except OSError:
                                pass

        if equipamentos:
            pdf.add_page()
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 6, "LISTA DE ITENS E VAZÕES", ln=1, align="L")
            pdf.ln(2)
            
            def get_c_pdf(it): return "Central" if qty_c == 1 else it.get("central", "Central")
            centrais_p = sorted(list(set([get_c_pdf(it) for it in equipamentos])))
            
            for c_nome in centrais_p:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, c_nome.upper(), ln=1, align="L")
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(20, 7, "QTD", border=1, align="C", fill=True)
                pdf.cell(120, 7, "ITEM / EQUIPAMENTO", border=1, align="C", fill=True)
                pdf.cell(50, 7, "VAZÃO TOTAL", border=1, align="C", fill=True, ln=1)
                
                pdf.set_font("Arial", "", 10)
                tot_v = 0.0
                for it in equipamentos:
                    if get_c_pdf(it) == c_nome:
                        tot_v += it["vazao_total_item"]
                        v_disp = "-" if it.get("tipo") == "cilindro" else f"{it['vazao_total_item']:.2f}".replace(".", ",").rstrip("0").rstrip(",") + " kg/h"
                        pdf.cell(20, 6, f"{it['qtd']:02d}", border=1, align="C")
                        pdf.cell(120, 6, f"{it['nome']}", border=1, align="L")
                        pdf.cell(50, 6, v_disp, border=1, align="C", ln=1)
                
                v_tot_str = f"{tot_v:.2f}".replace(".", ",").rstrip("0").rstrip(",")
                pdf.set_font("Arial", "B", 10)
                pdf.cell(140, 7, f"VAZÃO TOTAL {c_nome.upper()}:", border=1, align="R", fill=True)
                pdf.cell(50, 7, f"{v_tot_str} kg/h", border=1, align="C", fill=True, ln=1)
                pdf.ln(4)

        pdf_output = pdf.output(dest="S")
        if isinstance(pdf_output, str):
            return pdf_output.encode("latin-1")
        return bytes(pdf_output)

    st.subheader("6. Ações Finais")
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        if not cod_cliente.strip() or not nome_cliente.strip():
            st.warning("⚠️ Preencha pelo menos o Código e o Nome do Cliente para habilitar o PDF.")
        else:
            pdf_bytes = gerar_pdf(st.session_state.equipamentos, dic_fotos_final, cod_cliente, nome_cliente, qtd_centrais)
            
            cod_limpo = "".join(filter(str.isalnum, cod_cliente))
            data_atual_str = datetime.now().strftime("%d-%m-%y")
            nome_arquivo_pdf = f"relatorio_{cod_limpo}_{data_atual_str}.pdf"

            st.download_button(
                label="📥 Baixar Relatório (PDF)",
                data=pdf_bytes,
                file_name=nome_arquivo_pdf,
                mime="application/pdf"
            )

    with col_a2:
        if st.button("📝 Gerar Texto para Sistema"):
            lista_eq_txt = ""
            if st.session_state.equipamentos:
                def get_c_txt(eq): return "Central" if qtd_centrais == 1 else eq.get("central", "Central")
                cps = sorted(list(set([get_c_txt(eq) for eq in st.session_state.equipamentos])))
                for c_n in cps:
                    lista_eq_txt += f"Equipamentos {c_n}\n"
                    v_c = 0.0
                    for eq in st.session_state.equipamentos:
                        if get_c_txt(eq) == c_n:
                            lista_eq_txt += f"{eq['texto']}\n"
                            v_c += eq["vazao_total_item"]
                    lista_eq_txt += f"\nTotal Vazão {c_n}: {f'{v_c:.2f}'.replace('.', ',')} kg/h\n\n"
            else:
                lista_eq_txt = "Nenhum item cadastrado.\n\n"

            texto_final = f"""Contato: {contato}
Sobrenome ou departamento: {departamento}
Telefone: {telefone}

Equipamentos de acordo com o contrato vigente? {eq_contrato} - {desc_eq_contrato}
Representante 2 está correto? {rep2_correto}
Possui programação cadastrada? {tem_freq} - {desc_freq}
Consumo mensal atual de acordo com o contrato vigente? Consumo previsto: {consumo_previsto} kg | Consumo médio: {consumo_real} kg
Laudo ART emitido? {possui_art} - {desc_art}
Central atende as normas? {central_norma} - {desc_central_norma}

Quais equipamentos disponíveis no cliente?

{lista_eq_txt}Indicação de novos negócios do cliente: {indica_negocios}
Cliente possui débitos? {possui_debitos} - {desc_debitos}
Cliente está satisfeito com o atendimento da Consigaz? {cliente_satisfeito}

Obs.: {observacoes}
"""
            st.success("✅ Texto gerado com sucesso! Copie abaixo:")
            st.text_area("Texto Gerado:", value=texto_final, height=250, key=f"txt_area_transf_{rc}")


# =====================================================================
# TELA 2: ELABORAÇÃO DE CONTRATO
# =====================================================================
elif menu == "📝 Elaboração de Contrato":
    rcc = st.session_state.reset_counter_contrato

    cabecalho_pagina("Elaboração de Contrato", "Formulário de preenchimento e geração do padrão de solicitação.")

    st.divider()

    tipo_fluxo = st.radio(
        "Selecione o objetivo da solicitação:", 
        ["Gerar Minuta", "Enviar para Assinatura"],
        horizontal=True,
        index=None,
        key=f"fluxo_c_{rcc}"
    )

    st.divider()

    st.subheader("1. Motivo")
    motivo_solicitacao = st.text_input("Motivo da solicitação", key=f"motivo_{rcc}")

    st.divider()

    st.subheader("2. Dados do Cliente")
    col_cli1, col_cli2, col_cli3 = st.columns(3)
    with col_cli1:
        contato_contrato = st.text_input("Contato", key=f"contato_c_{rcc}")
    with col_cli2:
        telefone_contrato = st.text_input("Telefone", key=f"tel_c_{rcc}")
    with col_cli3:
        email_contrato = st.text_input("E-mail", key=f"email_c_{rcc}")

    st.divider()

    st.subheader("3. Solicitação")
    tipo_contrato = st.radio("Contrato / Aditamento / Distrato", ["Contrato", "Aditamento", "Distrato"], horizontal=True, index=None, key=f"tp_cont_{rcc}")

    st.divider()

    st.subheader("4. Dados do Contrato")
    col_con1, col_con2 = st.columns(2)
    
    cnpj_campo_val, ie_campo_val = "", ""
    email_novo_prop = "n/a"

    with col_con1:
        endereco_padrao = st.text_input("Endereço padrão ou entrega?", key=f"end_padrao_{rcc}")
        mesmo_prop_opt = st.radio("Mesmo proprietário?", ["Sim", "Não"], horizontal=True, index=None, key=f"mesmo_prop_{rcc}")
        
        if mesmo_prop_opt == "Não":
            email_novo_prop = st.text_input("E-mail do novo proprietário que receberá o novo contrato", key=f"email_novo_{rcc}")

        mesmo_cnpj_opt = st.radio("Mesmo CNPJ?", ["Sim", "Não"], horizontal=True, index=None, key=f"mesmo_cnpj_{rcc}")
        
        if mesmo_cnpj_opt == "Sim":
            cnpj_campo_val = st.text_input("CNPJ", key=f"cnpj_val_{rcc}")
            ie_campo_val = st.text_input("I.E.", key=f"ie_val_{rcc}")
        elif mesmo_cnpj_opt == "Não":
            cnpj_campo_val = st.text_input("Novo CNPJ", key=f"novo_cnpj_val_{rcc}")
            ie_campo_val = st.text_input("Nova I.E.", key=f"nova_ie_val_{rcc}")

    with col_con2:
        cond_pagamento = st.text_input("Condição de pagamento", key=f"cond_pag_{rcc}")
        vigencia = st.text_input("Vigência", key=f"vigencia_{rcc}")
        qtd_entregas_c = st.number_input("Quantidade de endereços de entrega / centrais", min_value=1, value=1, step=1, key=f"qtd_ent_c_{rcc}")
        
        equipamentos_contrato = ""
        eq_dict_c = {}
        if qtd_entregas_c == 1:
            equipamentos_contrato = st.text_input("Equipamentos", key=f"eq_contrato_c_{rcc}")
        else:
            st.markdown("**Equipamentos por Endereço de Entrega:**")
            for i in range(1, int(qtd_entregas_c) + 1):
                eq_dict_c[i] = st.text_input(f"Equipamentos - [Entrega {i}]", key=f"eq_ent_{i}_{rcc}")

    st.divider()

    st.subheader("5. Comodato / Fornecimento")
    tipo_fornecimento = st.radio("Tipo de Fornecimento", ["Granel", "Cilindro"], horizontal=True, index=None, key=f"tp_forn_{rcc}")
    
    preco_granel, consumo_granel = "", ""
    p13_val, p20_val, p45_val = "", "", ""
    p13_qtd, p20_qtd, p45_qtd = 0, 0, 0
    consumo_cilindro_total = 0
    
    if tipo_fornecimento == "Granel":
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            preco_granel = st.text_input("Preço Granel", key=f"preco_granel_{rcc}")
        with col_g2:
            consumo_granel = st.text_input("Consumo mensal previsto (kgs)", key=f"cons_granel_{rcc}")
    elif tipo_fornecimento == "Cilindro":
        st.markdown("**Preços por Modelo de Cilindro:**")
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        with col_cp1:
            p13_val = st.text_input("Preço P13 (/und)", key=f"p13_v_{rcc}")
        with col_cp2:
            p20_val = st.text_input("Preço P20 (/und)", key=f"p20_v_{rcc}")
        with col_cp3:
            p45_val = st.text_input("Preço P45 (/und)", key=f"p45_v_{rcc}")

        st.markdown("**Consumo mensal previsto (qntd):**")
        col_cc1, col_cc2, col_cc3 = st.columns(3)
        with col_cc1:
            p13_qtd = st.number_input("Qtd Cilindros P13", min_value=0, value=0, step=1, key=f"p13_q_{rcc}")
        with col_cc2:
            p20_qtd = st.number_input("Qtd Cilindros P20", min_value=0, value=0, step=1, key=f"p20_q_{rcc}")
        with col_cc3:
            p45_qtd = st.number_input("Qtd Cilindros P45", min_value=0, value=0, step=1, key=f"p45_q_{rcc}")
        
        consumo_cilindro_total = (p13_qtd * 13) + (p20_qtd * 20) + (p45_qtd * 45)

    st.divider()

    st.subheader("6. Financeiro")
    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        possui_debito_fin = st.radio("Cliente possui débitos?", ["Sim", "Não"], horizontal=True, index=None, key=f"possui_deb_{rcc}")
        resp_pendentes = "n/a"
        if possui_debito_fin == "Sim":
            resp_pendentes = st.text_input("Quem será o responsável pelas NF's pendentes?", key=f"resp_pend_{rcc}")

    responsaveis_dados = []
    nome_testemunha, email_testemunha = "", ""

    if tipo_fluxo == "Enviar para Assinatura":
        st.markdown("---")
        st.subheader("Dados de Assinatura e Testemunhas")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            nome_testemunha = st.text_input("Nome da Testemunha", key=f"nome_test_{rcc}")
        with col_t2:
            email_testemunha = st.text_input("E-mail da Testemunha", key=f"email_test_{rcc}")

        st.markdown("---")
        qtd_responsaveis = st.selectbox("Quantidade de Responsáveis pela Assinatura", [1, 2, 3, 4], index=0, key=f"qtd_resp_{rcc}")
        for i in range(1, qtd_responsaveis + 1):
            st.markdown(f"**Responsável {i}**")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                nome_resp = st.text_input(f"Nome do Responsável {i}", key=f"nome_resp_{i}_{rcc}")
            with col_r2:
                email_resp = st.text_input(f"E-mail do Responsável {i}", key=f"email_resp_{i}_{rcc}")
            responsaveis_dados.append({"nome": nome_resp, "email": email_resp})

    st.divider()

    st.subheader("7. Condomínio CONTA SIM")
    conta_sim = st.radio("Condomínio CONTA SIM?", ["Sim", "Não"], horizontal=True, index=None, key=f"conta_sim_{rcc}")

    num_unidades, qtd_torres, qtd_blocos, preco_religue, preco_servico = "", "", "", "", ""
    if conta_sim == "Sim":
        col_cs1, col_cs2, col_cs3 = st.columns(3)
        with col_cs1:
            num_unidades = st.text_input("N° Unid autônomas", key=f"num_unid_{rcc}")
            qtd_torres = st.text_input("Qtd Torres", key=f"qtd_torres_{rcc}")
        with col_cs2:
            qtd_blocos = st.text_input("Qtd Blocos", key=f"qtd_blocos_{rcc}")
            preco_religue = st.text_input("Valor preço de religue", key=f"preco_rel_{rcc}")
        with col_cs3:
            preco_servico = st.text_input("Valor preço de serviço", key=f"preco_servico_{rcc}")

    observacoes_contrato = st.text_area("Obs.", key=f"obs_c_{rcc}")

    st.divider()
    if st.button("📝 Gerar Texto Padrão do Contrato", type="primary"):
        sel_granel = "[x]" if tipo_fornecimento == "Granel" else "[ ]"
        sel_cilindro = "[x]" if tipo_fornecimento == "Cilindro" else "[ ]"
        
        texto_padrao_contrato = f"Motivo da solicitação: {motivo_solicitacao}"
        if tipo_fluxo == "Gerar Minuta":
            texto_padrao_contrato += "\n\n** FAVOR GERAR MINUTA EM PDF PARA ENVIO AO CLIENTE **"

        texto_padrao_contrato += f"""

Contato: {contato_contrato}
Telefone: {telefone_contrato}
E-mail: {email_contrato}
Contrato / Aditamento / Distrato: {tipo_contrato if tipo_contrato else ''}
Mesmo proprietário?: {mesmo_prop_opt if mesmo_prop_opt else ''}
E-mail do novo proprietário que receberá o novo contrato: {email_novo_prop}
Mesmo CNPJ?: {mesmo_cnpj_opt if mesmo_cnpj_opt else ''}
Endereço padrão ou entrega?: {endereco_padrao}
Tipo de Fornecimento: {sel_granel} Granel  {sel_cilindro} Cilindro"""

        if tipo_fornecimento == "Granel":
            texto_padrao_contrato += f"\nPreço Granel: {preco_granel} /kg\nConsumo mensal previsto: {consumo_granel}"
        elif tipo_fornecimento == "Cilindro":
            texto_padrao_contrato += f"\nConsumo mensal previsto: {consumo_cilindro_total} KGs"

        texto_padrao_contrato += f"\nCondição de pagamento: {cond_pagamento}\nVigência: {vigencia}"
        
        st.success("✅ Texto padrão gerado com sucesso! Copie abaixo:")
        st.text_area("Texto Gerado:", value=texto_padrao_contrato, height=250, key=f"txt_area_contrato_{rcc}")


# =====================================================================
# TELA 3: ANIVERSÁRIO DE CONTRATO
# =====================================================================
elif menu == "🎂 Aniversário de Contrato":
    rca = st.session_state.reset_counter_aniv if "reset_counter_aniv" in st.session_state else 0

    cabecalho_pagina("Aniversário de Contrato", "Tratativa de reajuste por IPCA acumulado de 12 meses.")

    st.divider()

    ipca_api, ipca_periodo = obter_ipca_acumulado_12m()
    if ipca_api is not None:
        ipca_vigente = ipca_api
        st.info(f"📊 **IPCA Acumulado de 12 meses (Referência IBGE):** **{ipca_vigente:.2f}%** (Obtido com sucesso do índice oficial)")
    else:
        st.warning(
            "⚠️ Não foi possível consultar o IPCA automaticamente. "
            "Informe o índice oficial manualmente abaixo para prosseguir com o cálculo."
        )
        ipca_vigente = st.number_input(
            "IPCA acumulado de 12 meses (%) - informado manualmente",
            min_value=0.0,
            value=float(IPCA_VALOR_RESERVA),
            step=0.01,
            format="%.2f",
            key=f"ipca_manual_{rca}"
        )

    col_an1, col_an2 = st.columns(2)
    with col_an1:
        preco_anterior_input = st.text_input("Preço Anterior (R$)", key=f"preco_ant_{rca}")
    with col_an2:
        st.write("")

    clausula_contrato = st.radio("Cliente possui cláusula em contrato?", ["Sim", "Não"], horizontal=True, index=None, key=f"clausula_{rca}")

    st.divider()

    p_aniv_str = "xx,xx"
    try:
        val_limpo = preco_anterior_input.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        p_ant = float(val_limpo)
        p_aniv = p_ant * (1 + (ipca_vigente / 100.0))
        p_aniv_str = f"{p_aniv:.4f}".replace(".", ",")
    except ValueError:
        pass

    if st.button("📝 Gerar Texto de Aniversário de Contrato", type="primary"):
        if clausula_contrato == "Não":
            st.warning("⚠️ **Atenção:** O cliente selecionado não possui cláusula de reajuste em contrato.")

        texto_aniversario = f"Aumento de Aniversário de contrato, IPCA - {ipca_vigente:.2f}%."

        if clausula_contrato == "Sim":
            texto_aniversario += "\n\nCliente possui cláusula em contrato."

        texto_aniversario += f"""

Preço anterior: R$ {preco_anterior_input if preco_anterior_input else 'xx,xx'}
Preço Aniversário: R$ {p_aniv_str}"""

        st.success("✅ Texto gerado com sucesso! Copie abaixo:")
        st.text_area("Texto Gerado:", value=texto_aniversario, height=180, key=f"txt_area_aniv_{rca}")
