import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Configuração da página para ocupar todo o ecrã
st.set_page_config(page_title="Dashboard Consigaz - Ocorrências", layout="wide")

# ==========================================
# CONFIGURAÇÃO VISUAL - PADRÃO CONSIGAZ
# ==========================================
st.markdown(
    """
    
    """,
    unsafe_allow_html=True
)

st.title("📊 Painel de Ocorrências e Visitas")
st.markdown("Carregue o seu ficheiro Excel diário para atualizar os dados.")

uploaded_file = st.file_uploader("Escolha o ficheiro Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Ignora as 12 primeiras linhas (cabeçalho padrão do sistema)
        df = pd.read_excel(uploaded_file, skiprows=12, header=None)
        
        # Renomeia as colunas conforme a estrutura do ficheiro
        df.columns = [
            'discard1', 'Proprietario', 'Status', 'discard2', 'Cidade', 'Numero', 'Zendesk',
            'Cliente', 'Endereco', 'Subclassificacao', 'Data_Abertura', 'Prazo_Atendimento',
            'Data_Fechamento', 'Reabertura', 'Reincidencia', 'Solucao', 'Atendida_Prazo', 'No_Prazo'
        ]
        
        # Filtra apenas as colunas solicitadas
        df = df[['Cliente', 'Numero', 'Subclassificacao', 'Cidade', 'Prazo_Atendimento']]
        
        # Remove linhas sem número de ocorrência ou cliente (linhas vazias)
        df = df.dropna(subset=['Numero', 'Cliente'], how='all')
        
        # Remove o '.0' do número da ocorrência
        df['Numero'] = df['Numero'].astype(str).str.replace('.0', '', regex=False)
        
        # Converte a coluna 'Prazo_Atendimento' para formato data
        df['Prazo_Atendimento'] = pd.to_datetime(df['Prazo_Atendimento'], format='%d/%m/%Y %H:%M', errors='coerce')
        
        # Define as datas de hoje e o fim da semana (fuso de Brasília)
        fuso_br = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.now(fuso_br).replace(tzinfo=None)
        
        # Fim da semana = próximo domingo às 23:59:59
        dias_para_domingo = 6 - hoje.weekday() 
        fim_semana = hoje + timedelta(days=dias_para_domingo)
        fim_semana = fim_semana.replace(hour=23, minute=59, second=59)
        
        # Classificação da prioridade
        def definir_prioridade(data):
            if pd.isna(data):
                return '⚪ Sem prazo'
            elif data < hoje:
                return '🔴 Atrasado'
            elif data <= fim_semana:
                return '🟡 Para esta semana'
            else:
                return '🟢 No prazo (Próximas semanas)'
                
        df['Prioridade'] = df['Prazo_Atendimento'].apply(definir_prioridade)
        
        # Separação da base
        df_comodato = df[df['Subclassificacao'].str.contains('COMODATO INATIVO', na=False, case=False)]
        df_outros = df[~df['Subclassificacao'].str.contains('COMODATO INATIVO', na=False, case=False)]
        
        # ==========================================
        # VISUALIZAÇÃO NO DASHBOARD
        # ==========================================
        st.header("📌 Resumo Global")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Ocorrências", len(df))
        col2.metric("Comodato Inativo", len(df_comodato))
        col3.metric("Para Esta Semana", len(df[df['Prioridade'] == '🟡 Para esta semana']))
        col4.metric("Atrasadas", len(df[df['Prioridade'] == '🔴 Atrasado']))
        
        st.markdown("