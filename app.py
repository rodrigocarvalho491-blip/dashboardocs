import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(DIRETORIO_ATUAL, "logo.png")

st.set_page_config(page_title="Dashboard de Ocorrências", page_icon="📊", layout="wide")

# --- MAPEAMENTO DAS COLUNAS DO SEU EXCEL ---
COL_OCORRENCIA = "Número da ocorrência"
COL_CLIENTE = "Nome do cliente"
COL_ENDERECO = "Endereço de Entrega"
COL_PRAZO = "Prazo de Atendimento"
COL_FECHAMENTO = "Data/Hora de fechamento" # Usado para desconsiderar as já tratadas
COL_SUB_CLASSIF = "Subclassificação Ocorrência"

# Função robusta para extrair apenas o nome limpo da cidade do endereço de entrega
def extrair_cidade(endereco):
    if pd.isna(endereco):
        return "-"
    s = str(endereco).strip()
    # Normaliza separadores (substitui ponto e vírgula ou pipe por vírgula)
    s_norm = s.replace(';', ',').replace('|', ',')
    partes = [p.strip() for p in s_norm.split(',')]
    if len(partes) >= 2:
        cidade = partes[-2].strip()
        if cidade.isdigit() and len(partes) >= 3:
            cidade = partes[-3].strip()
        return cidade.title()
    return s.title()

# --- CABEÇALHO DO APP COM LOGO ---
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.caption("📷 *Adicione 'logo.png' na pasta do projeto*")

with col_titulo:
    st.title("Gestão de Ocorrências & Visitas")
    st.markdown("Painel de organização de agenda ordenado por prazo de atendimento.")

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
        # Lê o Excel pulando as 11 primeiras linhas de cabeçalho do relatório exportado
        df = pd.read_excel(arquivo_excel, header=11)
        
        # Remove linhas totalmente vazias que possam vir no final do arquivo
        df = df.dropna(subset=[COL_OCORRENCIA])
        
        # 1. Filtro base: Desconsiderar ocorrências que já possuem tratativa (Data de fechamento preenchida)
        df_pendentes = df[df[COL_FECHAMENTO].isna()].copy()
        
        # 2. Tratamento da coluna de Prazo de Atendimento para o formato de Data
        df_pendentes[COL_PRAZO] = pd.to_datetime(df_pendentes[COL_PRAZO], format="%d/%m/%Y %H:%M", errors='coerce')
        
        # Remove linhas onde o prazo não pôde ser lido
        df_pendentes = df_pendentes.dropna(subset=[COL_PRAZO])
        
        # 3. Extrair apenas o nome da Cidade do Endereço de Entrega
        df_pendentes['Cidade'] = df_pendentes[COL_ENDERECO].apply(extrair_cidade)
        
        # Garante que a coluna de Sub-Classificação está tratada como texto
        df_pendentes[COL_SUB_CLASSIF] = df_pendentes[COL_SUB_CLASSIF].fillna("-").astype(str)
        
        # 4. ORDENAÇÃO OBRIGATÓRIA: Da data mais próxima para a mais distante (do dia/atrasadas para o futuro)
        df_pendentes = df_pendentes.sort_values(by=COL_PRAZO, ascending=True)
        
        # --- SEÇÃO 2: PAINEL DE OCORRÊNCIAS (DASHBOARD GERAL) ---
        st.subheader("2. Agenda Geral de Visitas Pendentes")
        
        # ÁREA DE FILTROS DO DASHBOARD GERAL
        st.markdown("### Filtros de Visualização")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            mostrar_so_hoje = st.toggle("📅 Mostrar apenas ocorrências com prazo PARA HOJE", value=False)
        with col_t2:
            mostrar_so_semana = st.toggle("🗓️ Mostrar apenas os próximos 7 dias", value=False)
        
        cidades_unicas = sorted(list(df_pendentes['Cidade'].unique()))
        sub_class_unicas = sorted(list(df_pendentes[COL_SUB_CLASSIF].unique()))
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            cidades_selecionadas = st.multiselect("Filtrar por Cidade(s):", cidades_unicas, default=[], key="filtro_cidade")
        with col_f2:
            sub_class_selecionadas = st.multiselect("Filtrar por Sub-Classificação:", sub_class_unicas, default=[], key="filtro_sub")
        
        # Aplicação dos filtros na cópia do dataframe principal
        df_filtrado = df_pendentes.copy()
        
        if mostrar_so_hoje:
            hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            hoje_fim = hoje_inicio + timedelta(days=1) - timedelta(seconds=1)
            df_filtrado = df_filtrado[(df_filtrado[COL_PRAZO] >= hoje_inicio) & (df_filtrado[COL_PRAZO] <= hoje_fim)]
        elif mostrar_so_semana:
            hoje = datetime.now()
            daqui_uma_semana = hoje + timedelta(days=7)
            df_filtrado = df_filtrado[df_filtrado[COL_PRAZO] <= daqui_uma_semana]
            
        if cidades_selecionadas:
            df_filtrado = df_filtrado[df_filtrado['Cidade'].isin(cidades_selecionadas)]
            
        if sub_class_selecionadas:
            df_filtrado = df_filtrado[df_filtrado[COL_SUB_CLASSIF].isin(sub_class_selecionadas)]
        
        # Formata a data para visualização amigável
        df_filtrado['Prazo Formatado'] = df_filtrado[COL_PRAZO].dt.strftime('%d/%m/%Y %H:%M')
        
        # Seleção das colunas principais para a tabela
        df_exibicao = df_filtrado[[
            COL_OCORRENCIA, 
            COL_CLIENTE, 
            'Cidade', 
            COL_SUB_CLASSIF,
            'Prazo Formatado'
        ]]
        
        # Métricas de Resumo
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Visitas Pendentes (Filtro)", len(df_exibicao))
        with col_m2:
            st.metric("Cidades na Rota", df_exibicao['Cidade'].nunique())
        with col_m3:
            mais_urgente = df_exibicao['Prazo Formatado'].iloc[0] if not df_exibicao.empty else "-"
            st.metric("Próximo Vencimento", mais_urgente)
        
        st.write("---")
        st.markdown("**Lista de Ocorrências Ordenadas (Mais Próxima para a Mais Distante):**")
        
        if df_exibicao.empty:
            st.success("✅ Excelente! Não há nenhuma ocorrência pendente para os filtros selecionados.")
        else:
            df_exibicao[COL_OCORRENCIA] = df_exibicao[COL_OCORRENCIA].astype(int).astype(str)
            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True,
                column_config={
                    COL_OCORRENCIA: st.column_config.TextColumn("Nº Ocorrência", width="small"),
                    COL_CLIENTE: st.column_config.TextColumn("Nome do Cliente", width="large"),
                    'Cidade': st.column_config.TextColumn("Cidade", width="small"),
                    COL_SUB_CLASSIF: st.column_config.TextColumn("Sub-Classificação", width="medium"),
                    'Prazo Formatado': st.column_config.TextColumn("Prazo de Atendimento", width="medium"),
                }
            )

        st.divider()

        # --- SEÇÃO 3: RELATÓRIO SEPARADO DE COMODATO INATIVO ---
        st.subheader("3. Relatório Específico: Comodato Inativo")
        st.markdown("Separação exclusiva das ocorrências de **Comodato Inativo** ordenadas por prazo para planeamento de recolha/visitas.")

        df_comodato = df_pendentes[df_pendentes[COL_SUB_CLASSIF].str.contains("Comodato Inativo", case=False, na=False)].copy()

        if df_comodato.empty:
            st.info("ℹ️ Não foram encontradas ocorrências pendentes com a sub-classificação 'Comodato Inativo' no ficheiro enviado.")
        else:
            df_comodato['Prazo Formatado'] = df_comodato[COL_PRAZO].dt.strftime('%d/%m/%Y %H:%M')
            df_comodato_exibicao = df_comodato[[
                COL_OCORRENCIA, 
                COL_CLIENTE, 
                'Cidade', 
                COL_SUB_CLASSIF,
                'Prazo Formatado'
            ]]
            df_comodato_exibicao[COL_OCORRENCIA] = df_comodato_exibicao[COL_OCORRENCIA].astype(int).astype(str)

            st.metric("Total de Comodatos Inativos Pendentes", len(df_comodato_exibicao))
            
            st.dataframe(
                df_comodato_exibicao,
                use_container_width=True,
                hide_index=True,
                column_config={
                    COL_OCORRENCIA: st.column_config.TextColumn("Nº Ocorrência", width="small"),
                    COL_CLIENTE: st.column_config.TextColumn("Nome do Cliente", width="large"),
                    'Cidade': st.column_config.TextColumn("Cidade", width="small"),
                    COL_SUB_CLASSIF: st.column_config.TextColumn("Sub-Classificação", width="medium"),
                    'Prazo Formatado': st.column_config.TextColumn("Prazo de Atendimento", width="medium"),
                }
            )

            # Botão para exportar esta tabela específica para Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_comodato_exibicao.to_excel(writer, index=False, sheet_name='Comodato Inativo')
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
    st.info("👆 Por favor, faça o upload da folha de cálculo atualizada de ocorrências acima para carregar o dashboard.")

st.divider()

# --- BOTÃO FLUTUANTE DE REFRESH ---
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("🔄 Atualizar Ecrã"):
        st.rerun()
