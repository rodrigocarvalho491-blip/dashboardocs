import os
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(DIRETORIO_ATUAL, "logo.png")

st.set_page_config(
    page_title="ERP | Gestão de Ocorrências e Pós-Vendas", 
    page_icon="⚡", 
    layout="wide"
)

# --- DESIGN SYSTEM: ESTILO DE SISTEMA INTEGRADO (CSS INJETADO) ---
st.markdown("""
    <style>
        :root {
            --primary: #0F172A;
            --accent: #2563EB;
            --bg-card: #FFFFFF;
            --border: #E2E8F0;
            --text-main: #1E293B;
            --text-muted: #64748B;
        }

        .stApp {
            background-color: #F8FAFC;
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        div.metric-container, div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            transition: all 0.2s ease-in-out;
        }
        div[data-testid="stMetric"]:hover {
            border-color: #CBD5E1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        h1, h2, h3 {
            color: #0F172A;
            font-weight: 700;
            letter-spacing: -0.025em;
        }
        
        hr {
            margin: 1.5rem 0;
            border-color: #E2E8F0;
        }

        .stButton>button {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .stAlert {
            border-radius: 6px;
            border: 1px solid transparent;
        }
    </style>
""", unsafe_allow_html=True)

# --- MAPEAMENTO DAS COLUNAS DO SEU EXCEL ---
COL_OCORRENCIA = "Número da ocorrência"
COL_CLIENTE = "Nome do cliente"
COL_ENDERECO = "Endereço de Entrega"
COL_ABERTURA = "Data/Hora de abertura"
COL_PRAZO = "Prazo de Atendimento"
COL_FECHAMENTO = "Data/Hora de fechamento"
COL_SUB_CLASSIF = "Subclassificação Ocorrência"

# Base de coordenadas aproximadas para cidades padrão
COORDENADAS_CIDADES = {
    "São Paulo": {"lat": -23.5505, "lon": -46.6333},
    "Campinas": {"lat": -22.9056, "lon": -47.0608},
    "São José Dos Campos": {"lat": -23.1794, "lon": -45.8869},
    "Ribeirão Preto": {"lat": -21.1775, "lon": -47.8103},
    "Santos": {"lat": -23.9618, "lon": -46.3322},
    "Sorocaba": {"lat": -23.5015, "lon": -47.4526},
    "Bauru": {"lat": -22.3147, "lon": -49.0587},
    "Jundiaí": {"lat": -23.1857, "lon": -46.8978},
    "Piracicaba": {"lat": -22.7338, "lon": -47.6476},
    "São José Do Rio Preto": {"lat": -20.8113, "lon": -49.3762},
}

COORD_DEFAULT = {"lat": -23.5505, "lon": -46.6333}

# Inicializa a memória de ocorrências tratadas manualmente na sessão
if "tratadas_manualmente" not in st.session_state:
    st.session_state.tratadas_manualmente = set()

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

def classificar_status_comodato(dias_uteis):
    if dias_uteis < 0:
        return "🔴 Vencido"
    elif dias_uteis == 0:
        return "🔵 Vence Hoje"
    elif dias_uteis == 1:
        return "🟠 Vence Amanhã"
    elif dias_uteis <= 5:
        return "🔴 3ª Semana"
    elif dias_uteis <= 10:
        return "🟡 2ª Semana"
    else:
        return "🟢 1ª Semana"

# --- TOPBAR / CABEÇALHO DO SISTEMA INTEGRADO ---
col_logo, col_titulo, col_status_sis = st.columns([1, 6, 2])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120)
    else:
        st.markdown("🏢 **ERP CONNECT**")

with col_titulo:
    st.markdown("### **Módulo de Pós-Vendas & Atendimento**")
    st.caption("Sistema Integrado de Gestão de Ocorrências por Prazos, SLAs e Geografia")

with col_status_sis:
    st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;'>● Servidor Ativo</span></div>", unsafe_allow_html=True)

st.divider()

# --- SIDEBAR DE NAVEGAÇÃO E UPLOAD ---
with st.sidebar:
    st.markdown("### ⚙️ Painel de Controle")
    st.markdown("Gerencie os dados de entrada e parâmetros do sistema.")
    
    st.markdown("---")
    st.subheader("1. Importação de Dados")
    arquivo_excel = st.file_uploader(
        "Relatório Excel (.xlsx / .xls)", 
        type=["xlsx", "xls"]
    )
    
    st.markdown("---")
    st.markdown("### 📊 Status da Sessão")
    st.markdown(f"**Ocorrências Tratadas:** `{len(st.session_state.tratadas_manualmente)}`")
    if st.button("🗑️ Limpar Sessão / Cache", use_container_width=True):
        st.session_state.tratadas_manualmente = set()
        st.rerun()

    st.markdown("---")
    if st.button("🔄 Sincronizar / Atualizar", use_container_width=True):
        st.rerun()
        
    st.markdown("<div style='position: fixed; bottom: 20px; font-size: 11px; color: #94A3B8;'>ERP Core v2.5.2<br>© 2026 Sistema Integrado</div>", unsafe_allow_html=True)

# --- CORPO PRINCIPAL DO SISTEMA ---
if arquivo_excel is not None:
    try:
        df_raw = pd.read_excel(arquivo_excel, header=None)
        
        header_row = None
        for i, row in df_raw.iterrows():
            row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
            if "Número da ocorrência" in row_str:
                header_row = i
                break
        
        if header_row is not None:
            df = pd.read_excel(arquivo_excel, header=header_row)
        else:
            df = pd.read_excel(arquivo_excel, header=11)
            
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=[COL_OCORRENCIA])
        
        df_pendentes = df[df[COL_FECHAMENTO].isna()].copy()
        df_pendentes[COL_OCORRENCIA] = pd.to_numeric(df_pendentes[COL_OCORRENCIA], errors='coerce')
        df_pendentes = df_pendentes.dropna(subset=[COL_OCORRENCIA])
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
        df_pendentes['Status Comodato'] = df_pendentes['Dias Úteis Restantes'].apply(classificar_status_comodato)
        df_pendentes = df_pendentes.sort_values(by='Prazo_DT', ascending=True)
        
        tab_geral, tab_comodato = st.tabs(["📋 2. Agenda Geral de Visitas", "📦 3. Módulo Comodato Inativo"])

        with tab_geral:
            st.markdown("#### Filtros Operacionais do Módulo")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                mostrar_so_hoje = st.toggle("📅 Exibir apenas ocorrências com prazo PARA HOJE", value=False)
            with col_t2:
                mostrar_so_semana = st.toggle("🗓️ Exibir apenas os próximos 5 dias úteis", value=False)
            
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
            
            st.markdown("---")
            
            # --- SEÇÃO DO MINI MAPA E MÉTRICAS EXECUTIVAS ---
            col_metrics, col_map = st.columns([1.2, 1])
            
            with col_metrics:
                st.markdown("##### 📌 Indicadores de Volume")
                cm1, cm2 = st.columns(2)
                with cm1:
                    st.metric("Visitas Pendentes", len(df_filtrado))
                    hoje_qt = len(df_filtrado[df_filtrado['Status Geral'] == "🔵 Vence Hoje"])
                    st.metric("Vence Hoje", hoje_qt)
                with cm2:
                    amanha_qt = len(df_filtrado[df_filtrado['Status Geral'] == "🟠 Vence Amanhã"])
                    st.metric("Vence Amanhã", amanha_qt)
                    vencidas_qt = len(df_filtrado[df_filtrado['Status Geral'] == "🔴 Vencido"])
                    st.metric("Ocorrências Vencidas", vencidas_qt)
            
            with col_map:
                st.markdown("##### 🗺️ Distribuição Geográfica de Atendimentos")
                if not df_filtrado.empty:
                    df_mapa_agrup = df_filtrado.groupby('Cidade').size().reset_index(name='TotalOcorrencias')
                    
                    lats, lons, sizes = [], [], []
                    for _, row in df_mapa_agrup.iterrows():
                        cidade_nome = row['Cidade']
                        coord = COORDENADAS_CIDADES.get(cidade_nome, COORD_DEFAULT)
                        lats.append(coord['lat'])
                        lons.append(coord['lon'])
                        sizes.append(max(row['TotalOcorrencias'] * 30, 100))
                    
                    df_mapa_agrup['lat'] = lats
                    df_mapa_agrup['lon'] = lons
                    df_mapa_agrup['tamanho'] = sizes
                    
                    st.map(df_mapa_agrup, latitude='lat', longitude='lon', size='tamanho', zoom=6, use_container_width=True)
                    st.caption("💡 *O tamanho do círculo indica o volume de ocorrências por cidade.*")
                else:
                    st.info("Nenhum dado geográfico disponível para os filtros atuais.")

            st.markdown("---")
            st.markdown("**Fila de Execução Ordenada por SLA:**")
            
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

        with tab_comodato:
            st.markdown("#### Relatório Específico: Comodato Inativo")
            st.markdown("Separação exclusiva das ocorrências de **Comodato Inativo** com contagem regressiva em dias úteis e semanas.")

            df_comodato = df_pendentes[df_pendentes[COL_SUB_CLASSIF].str.contains("Comodato Inativo", case=False, na=False)].copy()

            if df_comodato.empty:
                st.info("ℹ️ Não foram encontradas ocorrências pendentes com a sub-classificação 'Comodato Inativo' no ficheiro enviado.")
            else:
                df_comodato['Data Atendimento'] = df_comodato['Prazo_DT'].dt.strftime('%d/%m/%Y')
                
                df_comodato_exibicao = df_comodato[[
                    'Status Comodato',
                    'Dias Úteis Restantes',
                    COL_OCORRENCIA, 
                    COL_CLIENTE, 
                    'Cidade', 
                    COL_SUB_CLASSIF,
                    'Data Atendimento'
                ]].copy()
                df_comodato_exibicao[COL_OCORRENCIA] = df_comodato_exibicao[COL_OCORRENCIA].astype(str)

                st.metric("Total de Comodatos Inativos Pendentes", len(df_comodato_exibicao))
                
                edited_comodato = st.data_editor(
                    df_comodato_exibicao.assign(Tratar=False),
                    column_config={
                        "Tratar": st.column_config.CheckboxColumn("✅ Marcar Tratada?", required=True),
                        'Status Comodato': st.column_config.TextColumn("Status Semanal", width="small", disabled=True),
                        'Dias Úteis Restantes': st.column_config.NumberColumn("Dias Úteis Restantes", width="small", disabled=True),
                        COL_OCORRENCIA: st.column_config.TextColumn("Nº Ocorrência", width="small", disabled=True),
                        COL_CLIENTE: st.column_config.TextColumn("Nome do Cliente", width="large", disabled=True),
                        'Cidade': st.column_config.TextColumn("Cidade", width="small", disabled=True),
                        COL_SUB_CLASSIF: st.column_config.TextColumn("Sub-Classificação", width="medium", disabled=True),
                        'Data Atendimento': st.column_config.TextColumn("Data de Atendimento", width="medium", disabled=True),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="editor_comodato"
                )
                
                comodatos_para_tratar = edited_comodato[edited_comodato["Tratar"] == True][COL_OCORRENCIA].tolist()
                if comodatos_para_tratar:
                    st.warning(f"⚠️ Você selecionou **{len(comodatos_para_tratar)}** comodato(s) inativo(s) para tratar.")
                    if st.button("🔒 Confirmar Tratativa de Comodato", type="primary", key="btn_comodato"):
                        for oc in comodatos_para_tratar:
                            st.session_state.tratadas_manualmente.add(int(oc))
                        st.success("✅ Comodato(s) tratado(s) com sucesso e removido(s) do painel!")
                        st.rerun()

                st.write("")
                df_comodato_download = df_comodato_exibicao.copy()
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_comodato_download.to_excel(writer, index=False, sheet_name='Comodato Inativo')
                processed_data = output.getvalue()

                st.download_button(
                    label="📥 Baixar Planilha Separada (Comodato Inativo)",
                    data=processed_data,
                    file_name="comodatos_inativos_pendentes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"⚠️ Ocorreu um erro ao processar o ficheiro. Certifique-se de ser o relatório padrão do sistema. Erro técnico: {e}")

else:
    st.info("👆 Por favor, utilize a barra lateral esquerda (**Painel de Controle**) para efetuar o upload do relatório Excel e iniciar a operação.")
    
    col_demo1, col_demo2, col_demo3 = st.columns(3)
    with col_demo1:
        st.markdown("#### ⚡ Alta Performance")
        st.caption("Cálculo automático de prazos em dias úteis desconsiderando fins de semana e feriados.")
    with col_demo2:
        st.markdown("#### 🎯 Visão Executiva & Geográfica")
        st.caption("Métricas em tempo real e mini mapa interativo para distribuição territorial dos chamados.")
    with col_demo3:
        st.markdown("#### 🔒 Controle de Sessão")
        st.caption("Marcação interativa de ocorrências tratadas e remoção dinâmica da fila ativa.")
