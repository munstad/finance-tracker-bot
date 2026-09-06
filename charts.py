"""
charts.py — генерация графика расходов по категориям с помощью pandas + matplotlib.

Функция build_report_chart() возвращает путь к PNG-файлу с графиком,
который потом бот отправляет пользователю в Telegram.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # рисуем без графического интерфейса (нужно на сервере)
import matplotlib.pyplot as plt
import pandas as pd

CHART_PATH = Path(__file__).parent / "data" / "report.png"


def build_report_chart(expenses: list[dict], days: int) -> Path | None:
    """
    expenses — список словарей вида {"amount": .., "category": .., "created_at": ..}
    Возвращает путь к сохранённой картинке или None, если трат нет.
    """
    if not expenses:
        return None

    df = pd.DataFrame(expenses)
    by_category = df.groupby("category")["amount"].sum().sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Левый график — круговая диаграмма долей по категориям
    axes[0].pie(
        by_category.values,
        labels=by_category.index,
        autopct="%1.0f%%",
        startangle=90,
    )
    axes[0].set_title("Доля трат по категориям")

    # Правый график — столбики с суммой по категориям
    axes[1].bar(by_category.index, by_category.values, color="#4C72B0")
    axes[1].set_title(f"Сумма трат за {days} дн.")
    axes[1].set_ylabel("руб.")
    axes[1].tick_params(axis="x", rotation=30)

    total = by_category.sum()
    fig.suptitle(f"Итого потрачено: {total:.0f} руб.", fontsize=13, fontweight="bold")
    fig.tight_layout()

    CHART_PATH.parent.mkdir(exist_ok=True)
    fig.savefig(CHART_PATH, dpi=140)
    plt.close(fig)

    return CHART_PATH
