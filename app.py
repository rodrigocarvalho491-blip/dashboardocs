import os
import pandas as pd
import numpy as np
import streamlit as st
import html as html_lib
import base64
from datetime import datetime, timedelta
from io import BytesIO

# --- CONFIGURAÇÃO GLOBAL DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Ocorrências | Consigaz", 
    page_icon="🔥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(DIRETORIO_ATUAL, "logo.png")

# =====================================================================
# IDENTIDADE VISUAL CONSIGAZ - PADRÃO "SISTEMA INTEGRADO"
# =====================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --cg-azul-principal: #003366;
  --cg-azul-vibrante: #0055A5;
  --cg-laranja: #F28C28;
  --cg-fundo: #F1F5FA;
  --cg-texto: #1B2A3A;
  --cg-texto-suave: #5B6B7C;
  --cg-borda: #D3DDEA;
}

html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

.stApp { background: var(--cg-fundo); color: var(--cg-texto); }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

/* Painel central / Container */
.block-container, [data-testid="stMainBlockContainer"] {
  max-width: 1180px !important;
  margin: 1.2rem auto 2rem auto !important;
  padding: 1.8rem 2.4rem 2.4rem 2.4rem !important;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(10,37,64,.06), 0 8px 28px rgba(10,37,64,.07);
}

/* Cabeçalho Consigaz */
.cg-header { 
  display: flex; 
  align-items: center; 
  gap: 1.2rem; 
  position: relative;
  padding-bottom: 1.2rem; 
  margin-bottom: 1.5rem; 
  border-bottom: 1px solid var(--cg-borda); 
}
.cg-header::after { 
  content: ""; 
  position: absolute; 
  left: 0; 
  bottom: -1px; 
  width: 140px; 
  height: 4px; 
  border-radius: 4px; 
  background: linear-gradient(90deg, var(--cg-azul-vibrante) 0%, var(--cg-laranja) 100%); 
}

.cg-logo-wrapper {
  background: #FFFFFF;
  padding: 6px 12px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--cg-borda);
}
.cg-logo { height: 48px; width: auto; display: block; }

.cg-header-sep { width: 1px; align-self: stretch; background: var(--cg-borda); }
.cg-title { font-size: 1.6rem; font-weight: 800; line-height: 1.2; color: var(--cg-azul-principal) !important; letter-spacing: -0.02em; }
.cg-subtitle { font-size: 0.92rem; margin-top: 0.25rem; color: var(--cg-texto-suave) !important; font-weight: 500; }

/* Títulos de Seção */
.stApp h1, .stApp h2 { color: var(--cg-azul-principal) !important; font-weight: 800 !important; }
.stApp h3 {
  font-size: 1.08rem !important;
  font-weight: 800 !important;
  color: var(--cg-azul-principal) !important;
  padding: 0 0 0 0.75rem !important;
  border-left: 4px solid var(--cg-azul-vibrante) !important;
  margin-top: 1.5rem !important;
  margin-bottom: 1rem !important;
  line-height: 1.3 !important;
}

/* Botões modernos */
.stButton > button, .stDownloadButton > button {
  border-radius: 10px !important;
  border: 1.5px solid var(--cg-azul-vibrante) !important;
  background: #FFFFFF !important;
  color: var(--cg-azul-vibrante) !important;
  font-weight: 700 !important;
  padding: 0.45rem 1.1rem !important;
  transition: all 0.15s ease-in-out !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: #E7EFF9 !important;
  color: var(--cg-azul-vibrante) !important;
}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"], .stDownloadButton > button {
  background: var(--cg-azul-vibrante) !important;
  color: #FFFFFF !important;
  border-color: var(--cg-azul-vibrante) !important;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover, .stDownloadButton > button:hover {
  background: #003060 !important;
  color: #FFFFFF !important;
}

/* Sidebar Estilizada */
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--cg-borda); }
.cg-side-brand { 
  padding: 0.5rem 0.2rem 1.2rem 0.2rem; 
  margin-bottom: 1rem; 
  border-bottom: 1px solid var(--cg-borda); 
  text-align: center;
}
.cg-side-logo-wrapper {
  background: #FFFFFF;
  padding: 6px 10px;
  border-radius: 8px;
  display: inline-block;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  border: 1px solid var(--cg-borda);
}
.cg-side-logo { height: 38px; width: auto; display: inline-block; }
.cg-side-name { margin-top: 0.6rem; font-size: 0.78rem; font-weight: 700; color: var(--cg-texto-suave) !important; letter-spacing: 0.08em; text-transform: uppercase; }

@media (max-width: 768px) {
  .block-container, [data-testid="stMainBlockContainer"] { padding: 1rem !important; border-radius: 0; margin: 0 auto !important; }
}
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

# --- MENU LATERAL DE NAVEGAÇÃO / LOGO NA SIDEBAR ---
side_logo_html = _logo_html("cg-side-logo", "cg-side-logo-wrapper")
st.sidebar.markdown(
    f'<div class="cg-side-brand">{side_logo_html}'
    f'<div class="cg-side-name">Central de Atendimentos</div></div>',
    unsafe_allow_html=True,
)

st.sidebar.divider()
if st.sidebar.button("🔄 Atualizar / Limpar Cache"):
    st.rerun()

# --- MAPEAMENTO DAS COLUNAS DO EXCEL ---
COL_OCORRENCIA = "Número da ocorrência"
COL_CLIENTE = "Nome do cliente"
COL_ENDERECO = "Endereço de Entrega"
COL_ABERTURA = "Data/Hora de abertura"
COL_PRAZO = "Prazo de Atendimento"
COL_FECHAMENTO = "Data/Hora de fechamento"
COL_SUB_CLASSIF = "Subclassificação Ocorrência"

# Inicializa a memória de ocorrências tratadas manualmente na sessão do Streamlit
if "tratadas_manualmente" not in st.session_state:
    st.session_state.tratadas_manualmente = set()

# Função robusta para extrair apenas o nome limpo da cidade do endereço de entrega
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

# Função para calcular dias úteis (dias de semana) entre duas datas
def calcular_dias_uteis(data_inicio, data_fim):
    h = pd.Timestamp(data_inicio).normalize().date()
    p = pd.Timestamp(data_fim).normalize().date()
    if p > h:
        return int(np.busday_count(h, p))
    elif p < h:
        return -int(np.busday_count(p, h))
    else:
        return 0

# Função de status para a planilha geral
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

# --- CABEÇALHO DO APLICATIVO ---
cabecalho_pagina("Dashboard de Ocorrências & Visitas", "Painel de organização de agenda ordenado por prazo de atendimento (Dias Úteis).")

st.divider()

# --- SEÇÃO 1: IMPORTAÇÃO DE DADOS ---
st.subheader("1. Atualização de Dados")

arquivo_excel = st.file_uploader(
    "Faça o upload do relatório Excel (Pós-Vendas) 📂", 
    type=["xlsx", "xls"]
)

st.divider()

if arquivo_excel is not None:
    try:
        df = pd.read_excel(arquivo_excel, header=11)
        df = df.dropna(subset=[COL_OCORRENCIA])
        
        df_pendentes = df[df[COL_FECHAMENTO].isna()].copy()
        
        df_pendentes[COL_OCORRENCIA] = df_pendentes[COL_OCORRENCIA].astype(int)
        df_pendentes = df_pendentes[~df_pendentes[COL_OCORRENCIA].isin(st.session_state.tratadas_manualmente)]
        
        df_pendentes['Prazo_DT'] = pd.to_datetime(df_pendentes[COL_PRAZO], format="%d/%m/%Y %H:%M", errors='coerce')
        df_pendentes['Abertura_DT'] = pd.to_datetime(df_pendentes[COL_ABERTURA], format="%d/%m/%Y %H:%M", errors='coerce')
        
        df_pendentes = df_pendentes.dropna(subset=['Prazo_DT'])
        
        df_pendentes['Cidade'] = df_pendentes[COL_ENDERECO].apply(extrair_cidade)
        df_pendentes[COL_SUB_CLASSIF] = df_pendentes[COL_SUB_CLASSIF].fillna("-").astype(str)
        
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        df_pendentes['Dias Úteis Restantes'] = df_pendentes['Prazo_DT'].apply(lambda x: calcular_dias_uteis(hoje, x))
        
        df_pendentes['Status Geral'] = df_pendentes['Dias Úteis Restantes'].apply(classificar_status_geral)
        
        df_pendentes = df_pendentes.sort_values(by='Prazo_DT', ascending=True)
        
        # --- SEÇÃO 2: PAINEL DE OCORRÊNCIAS (DASHBOARD GERAL) ---
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

st.divider()
