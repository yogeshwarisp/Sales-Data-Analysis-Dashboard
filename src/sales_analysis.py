"""Step 2 of the pipeline: exploratory data analysis (EDA) with Python.

Reads  : data/cleaned_sales_data.csv
Writes : reports/*.csv   (summary tables)
         reports/*.png   (charts)
         reports/key_findings.md   (findings calculated from the data)

Every number printed or saved here is calculated from your dataset.
Nothing is hard-coded.
"""

import sys

import matplotlib

matplotlib.use("Agg")  # draw charts to files without opening windows
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils import (
    REPORTS_DIR,
    ensure_folders,
    format_money,
    format_number,
    load_cleaned_data,
)

PRIMARY_COLOR = "#1F4E79"
SECONDARY_COLOR = "#2E9CCA"
LOSS_COLOR = "#C0392B"
GAIN_COLOR = "#2E8B57"

sns.set_theme(style="whitegrid")


# ----------------------------------------------------------------------
# Calculations
# ----------------------------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> dict:
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_orders = df["order_id"].nunique()
    return {
        "total_records": len(df),
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "total_quantity": int(df["quantity"].sum()),
        "profit_margin_pct": total_profit / total_sales * 100 if total_sales else 0.0,
        "avg_order_value": total_sales / total_orders if total_orders else 0.0,
        "first_order_date": df["order_date"].min().date(),
        "last_order_date": df["order_date"].max().date(),
    }


def summarise(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    """Sales, profit, quantity, orders and margin for any grouping."""
    table = (
        df.groupby(group_columns)
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            total_quantity=("quantity", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .reset_index()
    )
    table["profit_margin_pct"] = table["total_profit"] / table["total_sales"] * 100
    return table.sort_values("total_sales", ascending=False).reset_index(drop=True)


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    table = (
        df.groupby("order_year_month")
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .reset_index()
        .sort_values("order_year_month")
        .reset_index(drop=True)
    )
    table["mom_change_pct"] = table["total_sales"].pct_change() * 100
    return table


def yearly_table(df: pd.DataFrame) -> pd.DataFrame:
    table = (
        df.groupby("order_year")
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .reset_index()
        .sort_values("order_year")
        .reset_index(drop=True)
    )
    table["yoy_change_pct"] = table["total_sales"].pct_change() * 100
    return table


def month_of_year_table(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales for each calendar month across all years (seasonality)."""
    return (
        df.groupby(["order_month", "order_month_name"])
        .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
        .reset_index()
        .sort_values("order_month")
        .reset_index(drop=True)
    )


def product_table(df: pd.DataFrame) -> pd.DataFrame:
    return summarise(df, ["product_name"])


def discount_table(df: pd.DataFrame) -> pd.DataFrame:
    table = (
        df.groupby(["discount_band_order", "discount_band"])
        .agg(
            records=("sales", "size"),
            avg_discount_pct=("discount", lambda s: s.mean() * 100),
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            loss_making_records=("profit", lambda s: (s < 0).sum()),
        )
        .reset_index()
        .sort_values("discount_band_order")
        .reset_index(drop=True)
    )
    table["profit_margin_pct"] = table["total_profit"] / table["total_sales"] * 100
    table["loss_making_pct"] = table["loss_making_records"] / table["records"] * 100
    return table


# ----------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------
def save_chart(fig, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_monthly_sales(monthly: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly["order_year_month"], monthly["total_sales"],
            marker="o", color=PRIMARY_COLOR, linewidth=2)
    ax.set_title("Monthly Sales Trend", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total Sales ($)")
    step = max(1, len(monthly) // 16)
    ax.set_xticks(range(0, len(monthly), step))
    ax.set_xticklabels(monthly["order_year_month"].iloc[::step], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "monthly_sales.png")


def chart_mom_change(monthly: pd.DataFrame) -> None:
    data = monthly.dropna(subset=["mom_change_pct"])
    if data.empty:
        return
    colors = [GAIN_COLOR if v >= 0 else LOSS_COLOR for v in data["mom_change_pct"]]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(data["order_year_month"], data["mom_change_pct"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Month-over-Month Sales Change (%)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Change vs previous month (%)")
    step = max(1, len(data) // 16)
    ax.set_xticks(range(0, len(data), step))
    ax.set_xticklabels(data["order_year_month"].iloc[::step], rotation=45, ha="right")
    save_chart(fig, "mom_sales_change.png")


def chart_yearly(yearly: pd.DataFrame) -> None:
    melted = yearly.melt(
        id_vars="order_year", value_vars=["total_sales", "total_profit"],
        var_name="Measure", value_name="Amount",
    )
    melted["Measure"] = melted["Measure"].map(
        {"total_sales": "Sales", "total_profit": "Profit"}
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=melted, x="order_year", y="Amount", hue="Measure",
                palette=[PRIMARY_COLOR, SECONDARY_COLOR], ax=ax)
    ax.set_title("Yearly Sales and Profit", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Amount ($)")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "yearly_sales_profit.png")


def chart_category(category: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.barplot(data=category, x="category", y="total_sales", color=PRIMARY_COLOR, ax=axes[0])
    axes[0].set_title("Sales by Category", fontweight="bold")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Total Sales ($)")
    colors = [LOSS_COLOR if v < 0 else GAIN_COLOR for v in category["total_profit"]]
    axes[1].bar(category["category"], category["total_profit"], color=colors)
    axes[1].set_title("Profit by Category", fontweight="bold")
    axes[1].set_ylabel("Total Profit ($)")
    for axis in axes:
        axis.yaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "category_analysis.png")


def chart_subcategory_profit(subcategory: pd.DataFrame) -> None:
    data = subcategory.sort_values("total_profit")
    colors = [LOSS_COLOR if v < 0 else GAIN_COLOR for v in data["total_profit"]]
    fig, ax = plt.subplots(figsize=(9, max(5, len(data) * 0.4)))
    ax.barh(data["sub_category"], data["total_profit"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Profit by Sub-Category", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Profit ($)")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "subcategory_profit.png")


def chart_region(region: pd.DataFrame) -> None:
    melted = region.melt(
        id_vars="region", value_vars=["total_sales", "total_profit"],
        var_name="Measure", value_name="Amount",
    )
    melted["Measure"] = melted["Measure"].map(
        {"total_sales": "Sales", "total_profit": "Profit"}
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=melted, x="region", y="Amount", hue="Measure",
                palette=[PRIMARY_COLOR, SECONDARY_COLOR], ax=ax)
    ax.set_title("Sales and Profit by Region", fontsize=14, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Amount ($)")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "regional_analysis.png")


def chart_top_states(state: pd.DataFrame) -> None:
    data = state.head(10).sort_values("total_sales")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(data["state"], data["total_sales"], color=PRIMARY_COLOR)
    ax.set_title("Top 10 States by Sales", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Sales ($)")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "top10_states.png")


def shorten(text: str, length: int = 45) -> str:
    return text if len(text) <= length else text[: length - 3] + "..."


def chart_top_products(products: pd.DataFrame) -> None:
    data = products.head(10).sort_values("total_sales")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.barh(data["product_name"].map(shorten), data["total_sales"], color=PRIMARY_COLOR)
    ax.set_title("Top 10 Products by Sales", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Sales ($)")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "top10_products.png")


def chart_least_profitable(products: pd.DataFrame) -> None:
    data = products.sort_values("total_profit").head(10).sort_values(
        "total_profit", ascending=False
    )
    colors = [LOSS_COLOR if v < 0 else SECONDARY_COLOR for v in data["total_profit"]]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.barh(data["product_name"].map(shorten), data["total_profit"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("10 Least Profitable Products", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Profit ($)")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:,.0f}")
    save_chart(fig, "least_profitable_products.png")


def chart_discount(df: pd.DataFrame, discount: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    colors = [LOSS_COLOR if v < 0 else GAIN_COLOR for v in discount["profit_margin_pct"]]
    axes[0].bar(discount["discount_band"], discount["profit_margin_pct"], color=colors)
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_title("Profit Margin % by Discount Band", fontweight="bold")
    axes[0].set_xlabel("Discount band")
    axes[0].set_ylabel("Profit margin (%)")
    axes[1].scatter(df["discount"] * 100, df["profit"], alpha=0.25, s=12, color=PRIMARY_COLOR)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title("Discount vs Profit (each dot = one record)", fontweight="bold")
    axes[1].set_xlabel("Discount (%)")
    axes[1].set_ylabel("Profit ($)")
    save_chart(fig, "discount_vs_profit.png")


def chart_heatmap(df: pd.DataFrame) -> None:
    pivot = df.pivot_table(index="order_year", columns="order_month",
                           values="sales", aggfunc="sum")
    fig, ax = plt.subplots(figsize=(12, max(3, len(pivot) * 0.9)))
    sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="Blues", ax=ax,
                cbar_kws={"label": "Total Sales ($)"})
    ax.set_title("Sales Heatmap: Year x Month", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month number")
    ax.set_ylabel("Year")
    save_chart(fig, "monthly_sales_heatmap.png")


# ----------------------------------------------------------------------
# Findings (calculated from the data, never typed in by hand)
# ----------------------------------------------------------------------
def build_findings(df, kpis, category, subcategory, region, state,
                   yearly, month_of_year, products, discount) -> list[str]:
    lines = []
    total_sales = kpis["total_sales"]

    lines.append(
        f"Dataset: {kpis['total_records']:,} records, {kpis['total_orders']:,} orders, "
        f"{kpis['first_order_date']} to {kpis['last_order_date']}."
    )
    lines.append(
        f"Totals: sales {format_money(total_sales)}, profit {format_money(kpis['total_profit'])}, "
        f"profit margin {kpis['profit_margin_pct']:.2f}%, quantity {kpis['total_quantity']:,}."
    )

    top_cat = category.iloc[0]
    lines.append(
        f"Highest-sales category: {top_cat['category']} "
        f"({format_money(top_cat['total_sales'])}, {top_cat['total_sales'] / total_sales * 100:.1f}% of sales)."
    )
    best_profit_cat = category.sort_values("total_profit", ascending=False).iloc[0]
    worst_margin_cat = category.sort_values("profit_margin_pct").iloc[0]
    lines.append(
        f"Highest-profit category: {best_profit_cat['category']} "
        f"({format_money(best_profit_cat['total_profit'])}). "
        f"Lowest margin category: {worst_margin_cat['category']} "
        f"({worst_margin_cat['profit_margin_pct']:.2f}%)."
    )

    losing_subs = subcategory[subcategory["total_profit"] < 0].sort_values("total_profit")
    if losing_subs.empty:
        lines.append("No sub-category has a negative total profit.")
    else:
        names = ", ".join(
            f"{row.sub_category} ({format_money(row.total_profit)})"
            for row in losing_subs.itertuples()
        )
        lines.append(f"Sub-categories with negative total profit: {names}.")

    top_region = region.iloc[0]
    best_profit_region = region.sort_values("total_profit", ascending=False).iloc[0]
    worst_margin_region = region.sort_values("profit_margin_pct").iloc[0]
    lines.append(
        f"Top region by sales: {top_region['region']} ({format_money(top_region['total_sales'])}). "
        f"Top region by profit: {best_profit_region['region']} "
        f"({format_money(best_profit_region['total_profit'])}). "
        f"Lowest regional margin: {worst_margin_region['region']} "
        f"({worst_margin_region['profit_margin_pct']:.2f}%)."
    )
    top_state = state.iloc[0]
    lines.append(f"Top state by sales: {top_state['state']} ({format_money(top_state['total_sales'])}).")

    best_year = yearly.sort_values("total_sales", ascending=False).iloc[0]
    lines.append(
        f"Best year by sales: {int(best_year['order_year'])} ({format_money(best_year['total_sales'])})."
    )
    for row in yearly.dropna(subset=["yoy_change_pct"]).itertuples():
        lines.append(
            f"Year-over-year sales change into {int(row.order_year)}: {row.yoy_change_pct:+.1f}%."
        )

    ranked_months = month_of_year.sort_values("total_sales", ascending=False)
    strongest = ", ".join(
        f"{r.order_month_name} ({format_money(r.total_sales)})"
        for r in ranked_months.head(3).itertuples()
    )
    weakest = ", ".join(
        f"{r.order_month_name} ({format_money(r.total_sales)})"
        for r in ranked_months.tail(3).itertuples()
    )
    lines.append(f"Strongest calendar months (all years combined): {strongest}.")
    lines.append(f"Weakest calendar months (all years combined): {weakest}.")

    losing_products = products[products["total_profit"] < 0].sort_values("total_profit")
    lines.append(
        f"Products with negative total profit: {len(losing_products):,} of {len(products):,} "
        f"({len(losing_products) / len(products) * 100:.1f}%), combined loss "
        f"{format_money(losing_products['total_profit'].sum())}."
    )
    if not losing_products.empty:
        worst = "; ".join(
            f"{r.product_name} ({format_money(r.total_profit)})"
            for r in losing_products.head(3).itertuples()
        )
        lines.append(f"Three largest product losses: {worst}.")

    band_text = "; ".join(
        f"{r.discount_band}: margin {r.profit_margin_pct:.2f}% over {r.records:,} records"
        for r in discount.itertuples()
    )
    lines.append(f"Profit margin by discount band: {band_text}.")
    losing_bands = discount[discount["total_profit"] < 0]
    if losing_bands.empty:
        lines.append("No discount band has a negative total profit.")
    else:
        lines.append(
            "Discount bands with negative total profit: "
            + ", ".join(losing_bands["discount_band"]) + "."
        )
    correlation = df["discount"].corr(df["profit"])
    lines.append(
        f"Correlation between discount and profit (per record): {correlation:.3f}. "
        "This shows association, not proof of cause."
    )

    total_loss = df.loc[df["profit"] < 0, "profit"].sum()
    if total_loss < 0:
        high_discount_loss = df.loc[
            (df["profit"] < 0) & (df["discount"] > 0.20), "profit"
        ].sum()
        lines.append(
            f"{high_discount_loss / total_loss * 100:.1f}% of all record-level losses "
            "come from records discounted by more than 20%."
        )
    return lines


def save_findings(lines: list[str]) -> None:
    text = "# Key Findings (calculated from the dataset)\n\n"
    text += "\n".join(f"- {line}" for line in lines) + "\n"
    (REPORTS_DIR / "key_findings.md").write_text(text, encoding="utf-8")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    try:
        df = load_cleaned_data()
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        return 1
    except ValueError as error:
        print(f"ERROR reading cleaned data: {error}")
        return 1

    ensure_folders()

    kpis = compute_kpis(df)
    category = summarise(df, ["category"])
    subcategory = summarise(df, ["category", "sub_category"])
    region = summarise(df, ["region"])
    state = summarise(df, ["region", "state"])
    monthly = monthly_table(df)
    yearly = yearly_table(df)
    month_of_year = month_of_year_table(df)
    products = product_table(df)
    discount = discount_table(df)

    # ---- Save tables -------------------------------------------------
    pd.DataFrame([kpis]).to_csv(REPORTS_DIR / "kpi_summary.csv", index=False)
    monthly.to_csv(REPORTS_DIR / "monthly_sales.csv", index=False)
    yearly.to_csv(REPORTS_DIR / "yearly_sales.csv", index=False)
    category.to_csv(REPORTS_DIR / "category_analysis.csv", index=False)
    subcategory.to_csv(REPORTS_DIR / "subcategory_analysis.csv", index=False)
    region.to_csv(REPORTS_DIR / "regional_analysis.csv", index=False)
    state.to_csv(REPORTS_DIR / "state_analysis.csv", index=False)
    products.head(10).to_csv(REPORTS_DIR / "top10_products.csv", index=False)
    products.sort_values("total_profit").head(10).to_csv(
        REPORTS_DIR / "least_profitable_products.csv", index=False
    )
    discount.to_csv(REPORTS_DIR / "discount_analysis.csv", index=False)

    # ---- Save charts -------------------------------------------------
    chart_monthly_sales(monthly)
    chart_mom_change(monthly)
    chart_yearly(yearly)
    chart_category(category)
    chart_subcategory_profit(subcategory)
    chart_region(region)
    chart_top_states(state)
    chart_top_products(products)
    chart_least_profitable(products)
    chart_discount(df, discount)
    chart_heatmap(df)

    # ---- Print results -----------------------------------------------
    print("\n" + "=" * 60)
    print("KEY PERFORMANCE INDICATORS")
    print("=" * 60)
    print(f"Records          : {format_number(kpis['total_records'])}")
    print(f"Total sales      : {format_money(kpis['total_sales'])}")
    print(f"Total profit     : {format_money(kpis['total_profit'])}")
    print(f"Total orders     : {format_number(kpis['total_orders'])}")
    print(f"Total quantity   : {format_number(kpis['total_quantity'])}")
    print(f"Profit margin    : {kpis['profit_margin_pct']:.2f}%")
    print(f"Avg order value  : {format_money(kpis['avg_order_value'])}")

    print("\nSales and profit by category:")
    print(category.round(2).to_string(index=False))
    print("\nSales and profit by region:")
    print(region.round(2).to_string(index=False))
    print("\nTop 10 products by sales:")
    print(products.head(10)[["product_name", "total_sales", "total_profit"]].round(2).to_string(index=False))
    print("\n10 least profitable products:")
    print(products.sort_values("total_profit").head(10)[["product_name", "total_sales", "total_profit"]].round(2).to_string(index=False))
    print("\nDiscount analysis:")
    print(discount.round(2).to_string(index=False))

    findings = build_findings(df, kpis, category, subcategory, region, state,
                              yearly, month_of_year, products, discount)
    save_findings(findings)
    print("\nKEY FINDINGS (calculated from your data)")
    print("-" * 60)
    for line in findings:
        print(f"- {line}")

    print(f"\nCharts, tables and key_findings.md saved in: {REPORTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
