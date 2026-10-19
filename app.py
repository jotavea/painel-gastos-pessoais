from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Meu painel de gastos", page_icon="💸", layout="wide")

CATEGORY_RULES = {
    "Moradia": ["aluguel", "condominio", "condomínio", "energia", "luz", "internet", "agua", "água"],
    "Alimentação": ["mercado", "supermercado", "padaria", "restaurante", "ifood", "lanche", "cafe", "café"],
    "Transporte": ["uber", "99", "combustivel", "combustível", "posto", "metro", "metrô", "onibus", "ônibus", "estacionamento"],
    "Saúde": ["farmacia", "farmácia", "consulta", "hospital", "academia", "medico", "médico"],
    "Lazer": ["cinema", "streaming", "show", "viagem", "jogo", "spotify", "netflix"],
    "Educação": ["curso", "livro", "escola", "faculdade", "mensalidade"],
    "Compras": ["roupa", "loja", "amazon", "eletronico", "eletrônico"],
}


def infer_category(description: str) -> str:
    text = str(description).lower()
    for category, terms in CATEGORY_RULES.items():
        if any(term in text for term in terms):
            return category
    return "Outros"


def load_transactions(file) -> pd.DataFrame:
    suffix = Path(file.name).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        raw = pd.read_excel(file)
    else:
        content = file.getvalue()
        try:
            raw = pd.read_csv(BytesIO(content), sep=None, engine="python", encoding="utf-8-sig", decimal=",")
        except UnicodeDecodeError:
            raw = pd.read_csv(BytesIO(content), sep=None, engine="python", encoding="latin-1", decimal=",")
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    aliases = {
        "data": "date", "descricao": "description", "descrição": "description",
        "estabelecimento": "description", "categoria": "category", "valor": "amount",
        "tipo": "type", "natureza": "type",
    }
    raw = raw.rename(columns={c: aliases.get(c, c) for c in raw.columns})
    if "date" not in raw or "amount" not in raw:
        raise ValueError("O arquivo precisa ter pelo menos as colunas **data** e **valor** (ou date e amount).")
    if "description" not in raw:
        raw["description"] = "Sem descrição"
    raw["date"] = pd.to_datetime(raw["date"], dayfirst=True, errors="coerce")
    raw["amount"] = (raw["amount"].astype(str).str.replace(r"[^0-9,.-]", "", regex=True)
                      .str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    raw["amount"] = pd.to_numeric(raw["amount"], errors="coerce")
    raw = raw.dropna(subset=["date", "amount"]).copy()
    if "type" in raw:
        is_income = raw["type"].astype(str).str.lower().str.contains("receita|income|entrada", regex=True)
        raw.loc[is_income, "amount"] = raw.loc[is_income, "amount"].abs()
        raw.loc[~is_income, "amount"] = -raw.loc[~is_income, "amount"].abs()
    if "category" not in raw:
        raw["category"] = raw["description"].map(infer_category)
    else:
        blank = raw["category"].isna() | raw["category"].astype(str).str.strip().eq("")
        raw.loc[blank, "category"] = raw.loc[blank, "description"].map(infer_category)
    raw["category"] = raw["category"].astype(str).str.strip()
    raw["description"] = raw["description"].fillna("Sem descrição").astype(str)
    raw["month"] = raw["date"].dt.to_period("M").dt.to_timestamp()
    raw["expense"] = (-raw["amount"]).clip(lower=0)
    raw["income"] = raw["amount"].clip(lower=0)
    return raw.sort_values("date")


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.title("💸 Meu painel de gastos")
st.caption("Importe seu extrato CSV ou Excel para entender para onde vai seu dinheiro.")
with st.sidebar:
    st.header("Seus dados")
    uploaded = st.file_uploader("Envie um arquivo CSV ou Excel", type=["csv", "xlsx", "xls"])
    st.caption("Colunas necessárias: data e valor. Também aceita descrição, categoria e tipo.")
    st.download_button("Baixar CSV de exemplo", data=Path(__file__).with_name("exemplo_gastos.csv").read_bytes(),
                       file_name="exemplo_gastos.csv", mime="text/csv")

if uploaded is None:
    sample = Path(__file__).with_name("exemplo_gastos.csv")
    df = load_transactions(type("Upload", (), {"name": sample.name, "getvalue": sample.read_bytes})())
    st.info("Você está vendo dados de exemplo. Envie seu CSV ou Excel na barra lateral para analisar suas despesas.")
else:
    try:
        df = load_transactions(uploaded)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

with st.sidebar:
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    selected_range = st.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    categories = sorted(df["category"].unique())
    selected_categories = st.multiselect("Categorias", categories, default=categories)

if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
else:
    start_date = end_date = selected_range
filtered = df[df["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))]
filtered = filtered[filtered["category"].isin(selected_categories)]
if filtered.empty:
    st.warning("Não há transações para os filtros selecionados.")
    st.stop()

spent = filtered["expense"].sum()
income = filtered["income"].sum()
balance = income - spent
average = filtered.loc[filtered["expense"] > 0].groupby("date")["expense"].sum().mean() if (filtered["expense"] > 0).any() else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric("Despesas", brl(spent))
c2.metric("Receitas", brl(income))
c3.metric("Saldo no período", brl(balance), delta_color="normal")
c4.metric("Gasto médio por dia com despesas", brl(average))

left, right = st.columns(2)
with left:
    st.subheader("Gastos por categoria")
    by_category = filtered.groupby("category", as_index=False)["expense"].sum().query("expense > 0").sort_values("expense", ascending=False)
    if not by_category.empty:
        st.plotly_chart(px.pie(by_category, names="category", values="expense", hole=.48), use_container_width=True)
    else:
        st.info("Nenhuma despesa neste período.")
with right:
    st.subheader("Evolução mensal")
    monthly = filtered.groupby("month", as_index=False).agg(Despesas=("expense", "sum"), Receitas=("income", "sum"))
    monthly = monthly.melt(id_vars="month", var_name="Tipo", value_name="Valor")
    st.plotly_chart(px.bar(monthly, x="month", y="Valor", color="Tipo", barmode="group",
                           labels={"month": "Mês", "Valor": "Valor (R$)"}), use_container_width=True)

st.subheader("Transações")
show = filtered.sort_values("date", ascending=False)[["date", "description", "category", "amount"]].copy()
show["date"] = show["date"].dt.strftime("%d/%m/%Y")
show["amount"] = show["amount"].map(brl)
st.dataframe(show.rename(columns={"date": "Data", "description": "Descrição", "category": "Categoria", "amount": "Valor"}),
             use_container_width=True, hide_index=True)

csv = filtered.drop(columns=["month", "expense", "income"]).to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")
st.download_button("Exportar transações filtradas", data=csv, file_name="transacoes_filtradas.csv", mime="text/csv")
st.caption("Os dados ficam no seu computador durante a sessão. Categorias ausentes são sugeridas pelo texto da descrição.")
