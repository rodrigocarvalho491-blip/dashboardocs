import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

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

# Função para extrair apenas a cidade da string de endereço do seu sistema
def extrair_cidade(endereco):
    if pd.isna(endereco):
        return "-"
    partes = str(endereco).split(',')
    if len(partes) >= 3:
        # Pega a penúltima parte (ex: 'TAUBATE' de '...,TAUBATE,São Paulo')
        return partes[-2].strip().title()
    return str(endereco).strip()

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

# --- SEÇÃO 2: PAINEL DE OCORRÊNCIAS (DASHBOARD) ---
st.subheader("2. Agenda Pendente de Visitas")

if arquivo_excel is not None:
    try:
        # Lê o Excel pulando as 11 primeiras linhas de cabeçalho do relatório exportado
        df = pd.read_excel(arquivo_excel, header=11)
        
        # Remove linhas totalmente vazias que possam vir no final do arquivo
        df = df.dropna(subset=[COL_OCORRENCIA])
        
        # 1. Filtro: Desconsiderar ocorrências que já possuem tratativa (Data de fechamento preenchida)
        df_pendentes = df[df[COL_FECHAMENTO].isna()].copy()
        
        # 2. Tratamento da coluna de Prazo de Atendimento para o formato de Data
        df_pendentes[COL_PRAZO] = pd.to_datetime(df_pendentes[COL_PRAZO], format="%d/%m/%Y %H:%M", errors='coerce')
        
        # Remove linhas onde o prazo não pôde ser lido
        df_pendentes = df_pendentes.dropna(subset=[COL_PRAZO])
        
        # 3. Extrair a Cidade do Endereço de Entrega
        df_pendentes['Cidade'] = df_pendentes[COL_ENDERECO].apply(extrair_cidade)
        
        # 4. Ordenação: Da data mais próxima para a mais distante
        df_pendentes = df_pendentes.sort_values(by=COL_PRAZO, ascending=True)
        
        # --- FILTRO PARA A SEMANA ---
        st.markdown("### Filtros de Visualização")
        mostrar_so_semana = st.toggle("📅 Mostrar apenas ocorrências com prazo para os próximos 7 dias", value=False)
        
        if mostrar_so_semana:
            hoje = datetime.now()
            daqui_uma_semana = hoje + timedelta(days=7)
            # Filtra do dia de hoje até daqui 7 dias (incluindo as atrasadas)
            df_pendentes = df_pendentes[df_pendentes[COL_PRAZO] <= daqui_uma_semana]
        
        # Formata a data para visualização amigável
        df_pendentes['Prazo Formatado'] = df_pendentes[COL_PRAZO].dt.strftime('%d/%m/%Y %H:%M')
        
        # Seleciona apenas as colunas práticas para exibir na tela
        df_exibicao = df_pendentes[[
            COL_OCORRENCIA, 
            COL_CLIENTE, 
            'Cidade', 
            'Prazo Formatado'
        ]]
        
        # --- MÉTRICAS DE RESUMO ---
        st.write("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Visitas Pendentes (Filtro Atual)", len(df_exibicao))
        with col_m2:
            st.metric("Cidades na Rota", df_exibicao['Cidade'].nunique())
        with col_m3:
            mais_urgente = df_exibicao['Prazo Formatado'].iloc[0] if not df_exibicao.empty else "-"
            st.metric("Próximo Vencimento", mais_urgente)
        
        st.write("---")
        
        # --- TABELA DE DADOS INTERATIVA ---
        st.markdown("**Lista de Ocorrências Ordenadas:**")
        
        if df_exibicao.empty:
            st.success("✅ Excelente! Não há nenhuma ocorrência pendente no período selecionado.")
        else:
            # Garante que o número da ocorrência seja exibido sem casas decimais (.0)
            df_exibicao[COL_OCORRENCIA] = df_exibicao[COL_OCORRENCIA].astype(int).astype(str)
            
            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True,
                column_config={
                    COL_OCORRENCIA: st.column_config.TextColumn("Nº Ocorrência", width="small"),
                    COL_CLIENTE: st.column_config.TextColumn("Nome do Cliente", width="large"),
                    'Cidade': st.column_config.TextColumn("Cidade", width="medium"),
                    'Prazo Formatado': st.column_config.TextColumn("Prazo de Atendimento", width="medium"),
                }
            )

    except Exception as e:
        st.error(f"⚠️ Ocorreu um erro ao processar o arquivo. Certifique-se de ser o relatório padrão do sistema. Erro técnico: {e}")

else:
    st.info("👆 Por favor, faça o upload da planilha atualizada de ocorrências acima para visualizar a agenda.")

st.divider()

# --- BOTÃO FLUTUANTE DE REFRESH ---
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("🔄 Atualizar Tela"):
        st.rerun()Com base na análise do arquivo Excel que você enviou (`Minhas Ocorrências (Pós-Vendas)-2026-10-01-09-04-41.xlsx`), identifiquei três detalhes importantes para o funcionamento perfeito do seu Dashboard:

1. **Cabeçalho deslocado:** No seu sistema (CSI/CRM), o relatório é exportado com um cabeçalho de 11 linhas. O código já foi ajustado para pular essas linhas iniciais e ler os dados corretamente (`header=11`).
2. **Coluna de Cidade:** A cidade não vem em uma coluna isolada, ela vem dentro de `Endereço de Entrega` (ex: *57711|Padrão,JARDIM DAS NACOES,TAUBATE,São Paulo*). Criei uma função no código que extrai automaticamente apenas a cidade (TAUBATE) para deixar a visualização limpa.
3. **Regra de Tratativa:** Você mencionou *"As ocorrências que tiverem preenchimento na coluna de prazo de atendimento, desconsidere"*, mas também pediu para *"ordenar por prazo de atendimento"*. Como não é possível ordenar por uma coluna vazia, assumi que a coluna que define se o chamado já teve tratativa no seu relatório é a **`Data/Hora de fechamento`** (ou `Solução`). Deixei isso configurado no código.

Aqui está o código completo da nova tela, mantendo a identidade visual e adicionando o filtro semanal solicitado:

```python
import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

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

# Função para extrair apenas a cidade da string de endereço do seu sistema
def extrair_cidade(endereco):
    if pd.isna(endereco):
        return "-"
    partes = str(endereco).split(',')
    if len(partes) >= 3:
        # Pega a penúltima parte (ex: 'TAUBATE' de '...,TAUBATE,São Paulo')
        return partes[-2].strip().title()
    return str(endereco).strip()

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

# --- SEÇÃO 2: PAINEL DE OCORRÊNCIAS (DASHBOARD) ---
st.subheader("2. Agenda Pendente de Visitas")

if arquivo_excel is not None:
    try:
        # Lê o Excel pulando as 11 primeiras linhas de cabeçalho do relatório exportado
        df = pd.read_excel(arquivo_excel, header=11)
        
        # Remove linhas totalmente vazias que possam vir no final do arquivo
        df = df.dropna(subset=[COL_OCORRENCIA])
        
        # 1. Filtro: Desconsiderar ocorrências que já possuem tratativa (Data de fechamento preenchida)
        df_pendentes = df[df[COL_FECHAMENTO].isna()].copy()
        
        # 2. Tratamento da coluna de Prazo de Atendimento para o formato de Data
        df_pendentes[COL_PRAZO] = pd.to_datetime(df_pendentes[COL_PRAZO], format="%d/%m/%Y %H:%M", errors='coerce')
        
        # Remove linhas onde o prazo não pôde ser lido
        df_pendentes = df_pendentes.dropna(subset=[COL_PRAZO])
        
        # 3. Extrair a Cidade do Endereço de Entrega
        df_pendentes['Cidade'] = df_pendentes[COL_ENDERECO].apply(extrair_cidade)
        
        # 4. Ordenação: Da data mais próxima para a mais distante
        df_pendentes = df_pendentes.sort_values(by=COL_PRAZO, ascending=True)
        
        # --- FILTRO PARA A SEMANA ---
        st.markdown("### Filtros de Visualização")
        mostrar_so_semana = st.toggle("📅 Mostrar apenas ocorrências com prazo para os próximos 7 dias", value=False)
        
        if mostrar_so_semana:
            hoje = datetime.now()
            daqui_uma_semana = hoje + timedelta(days=7)
            # Filtra do dia de hoje até daqui 7 dias (incluindo as atrasadas)
            df_pendentes = df_pendentes[df_pendentes[COL_PRAZO] <= daqui_uma_semana]
        
        # Formata a data para visualização amigável
        df_pendentes['Prazo Formatado'] = df_pendentes[COL_PRAZO].dt.strftime('%d/%m/%Y %H:%M')
        
        # Seleciona apenas as colunas práticas para exibir na tela
        df_exibicao = df_pendentes[[
            COL_OCORRENCIA, 
            COL_CLIENTE, 
            'Cidade', 
            'Prazo Formatado'
        ]]
        
        # --- MÉTRICAS DE RESUMO ---
        st.write("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Visitas Pendentes (Filtro Atual)", len(df_exibicao))
        with col_m2:
            st.metric("Cidades na Rota", df_exibicao['Cidade'].nunique())
        with col_m3:
            mais_urgente = df_exibicao['Prazo Formatado'].iloc[0] if not df_exibicao.empty else "-"
            st.metric("Próximo Vencimento", mais_urgente)
        
        st.write("---")
        
        # --- TABELA DE DADOS INTERATIVA ---
        st.markdown("**Lista de Ocorrências Ordenadas:**")
        
        if df_exibicao.empty:
            st.success("✅ Excelente! Não há nenhuma ocorrência pendente no período selecionado.")
        else:
            # Garante que o número da ocorrência seja exibido sem casas decimais (.0)
            df_exibicao[COL_OCORRENCIA] = df_exibicao[COL_OCORRENCIA].astype(int).astype(str)
            
            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True,
                column_config={
                    COL_OCORRENCIA: st.column_config.TextColumn("Nº Ocorrência", width="small"),
                    COL_CLIENTE: st.column_config.TextColumn("Nome do Cliente", width="large"),
                    'Cidade': st.column_config.TextColumn("Cidade", width="medium"),
                    'Prazo Formatado': st.column_config.TextColumn("Prazo de Atendimento", width="medium"),
                }
            )

    except Exception as e:
        st.error(f"⚠️ Ocorreu um erro ao processar o arquivo. Certifique-se de ser o relatório padrão do sistema. Erro técnico: {e}")

else:
    st.info("👆 Por favor, faça o upload da planilha atualizada de ocorrências acima para visualizar a agenda.")

st.divider()

# --- BOTÃO FLUTUANTE DE REFRESH ---
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("🔄 Atualizar Tela"):
        st.rerun()

```
