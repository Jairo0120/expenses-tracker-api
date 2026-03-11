from api.models import Expense, Cycle, Budget, Income
from datetime import datetime, date, timedelta
from api import utils
from sqlmodel import Session, create_engine
import pandas as pd
import locale
import numpy as np


locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
sqlite_url = "sqlite:////home/jairo/Documents/database.db"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

with Session(engine) as session:
    for year in range(2022, 2025):
        for month in range(1, 13):
            try:
                print("Processing", year, month)
                date_cycle = datetime.strptime(f'{1}/{month}/{year}', '%d/%m/%Y')
                date_cycle = date_cycle + timedelta(hours=5)
                cycle = Cycle(
                    description=date_cycle.strftime('%b %Y').capitalize(),
                    start_date=utils.get_first_day_month(date(year, month, 1)),
                    end_date=utils.get_last_day_month(date(year, month, 1)),
                    is_active=False,
                    is_recurrent_incomes_created=True,
                    is_recurrent_expenses_created=True,
                    is_recurrent_savings_created=True,
                    is_recurrent_budgets_created=True,
                    user_id=8
                )
                session.add(cycle)
                budget_salidas = Budget(
                    description="Salidas",
                    val_budget=0,
                    cycle=cycle,
                )
                session.add(budget_salidas)
                budget_mercado = Budget(
                    description="Mercado",
                    val_budget=0,
                    cycle=cycle,
                )
                session.add(budget_mercado)
                budget_gasolina = Budget(
                    description="Gasolina",
                    val_budget=0,
                    cycle=cycle,
                )
                session.add(budget_gasolina)
                budget_general = Budget(
                    description="General",
                    val_budget=0,
                    cycle=cycle,
                )
                session.add(budget_general)
                # Extract incomes
                expenses = pd.read_excel(
                    '~/Downloads/Presupuestos.xlsx',
                    sheet_name=f'{date_cycle.strftime('%B').capitalize()} {year}'
                )
                income = Income(
                    description="Salario",
                    val_income=expenses.iloc[0, 2],
                    date_income=date_cycle,
                    cycle=cycle,
                )
                session.add(income)
                re_row = 7
                # Extract recurrent expenses
                while True:
                    description = expenses.iloc[re_row, 1]
                    value = expenses.iloc[re_row, 2]
                    if description == "Total":
                        break
                    re_row += 1
                    expense = Expense(
                        description=description,
                        val_expense=value,
                        date_expense=date_cycle,
                        cycle=cycle,
                        is_recurrent_expense=True,
                        budget_id=None
                    )
                    session.add(expense)
                if year == 2024 and month >= 3:
                    karen_expense = Expense(
                        description="Mesada Karen",
                        val_expense=1300000,
                        date_expense=date_cycle,
                        cycle=cycle,
                        is_recurrent_expense=True,
                        budget_id=None
                    )
                    session.add(karen_expense)
                # Extract expenses
                sa_expenses_row = 7
                while True:
                    description = expenses.iloc[sa_expenses_row, 4]
                    value = expenses.iloc[sa_expenses_row, 5]
                    if description is np.nan:
                        break
                    sa_expenses_row += 1
                    expense = Expense(
                        description=description,
                        val_expense=value,
                        date_expense=date_cycle + timedelta(hours=1),
                        cycle=cycle,
                        is_recurrent_expense=False,
                        budget=budget_salidas
                    )
                    session.add(expense)
                # Extract general expenses
                general_expenses_row = 7
                print("Processing general expenses")
                while True:
                    print("Processing row", general_expenses_row)
                    try:
                        description = expenses.iloc[general_expenses_row, 7]
                        value = expenses.iloc[general_expenses_row, 8]
                    except IndexError:
                        break
                    if description is np.nan:
                        break
                    general_expenses_row += 1
                    selected_budget = None
                    if "gasolina" in description.lower():
                        selected_budget = budget_gasolina
                    elif "mercado" in description.lower():
                        selected_budget = budget_mercado
                    else:
                        selected_budget = budget_general
                    expense = Expense(
                        description=description,
                        val_expense=value,
                        date_expense=date_cycle + timedelta(hours=1),
                        cycle=cycle,
                        is_recurrent_expense=False,
                        budget=selected_budget
                    )
                    session.add(expense)
                session.commit()
            except ValueError as ex:
                print(ex)
                if "not found" in str(ex):
                    continue
                raise ex
