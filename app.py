
import json
import os
from pathlib import Path
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "moneymate-dev-key")

# Lokasi penyimpanan JSON:
# Lokal: folder data/transactions.json
# Vercel: folder sementara /tmp/transactions.json
if os.environ.get("VERCEL"):
    DATA_FILE = Path("/tmp/transactions.json")
else:
    DATA_FILE = Path(__file__).parent / "data" / "transactions.json"

CATEGORIES = [
    "Gaji", "Uang Saku", "Makanan", "Transportasi",
    "Pendidikan", "Hiburan", "Belanja", "Lainnya"
]


def load_data():
    """Membaca data transaksi dan target tabungan dari JSON."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        save_data({"transactions": [], "savings_goals": []})

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = {"transactions": [], "savings_goals": []}

    if not isinstance(data, dict):
        data = {"transactions": [], "savings_goals": []}

    data.setdefault("transactions", [])
    data.setdefault("savings_goals", [])

    return data


def save_data(data):
    """Menyimpan data ke file JSON."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def calculate_summary(transactions):
    income = sum(
        int(item.get("amount", 0))
        for item in transactions
        if item.get("type") == "income"
    )

    expense = sum(
        int(item.get("amount", 0))
        for item in transactions
        if item.get("type") == "expense"
    )

    return income, expense, income - expense


def parse_positive_amount(value, allow_zero=False):
    amount = int(value)

    if amount < 0 or (amount == 0 and not allow_zero):
        raise ValueError("Jumlah harus lebih besar dari nol.")

    return amount


def valid_date(value):
    date.fromisoformat(value)
    return value


@app.route("/")
def dashboard():
    data = load_data()
    transactions = data["transactions"]
    savings_goals = data["savings_goals"]

    total_income, total_expense, balance = calculate_summary(transactions)

    latest_transactions = sorted(
        transactions,
        key=lambda item: item.get("date", ""),
        reverse=True
    )[:5]

    total_savings_target = sum(
        int(goal.get("target_amount", 0))
        for goal in savings_goals
    )

    total_saved = sum(
        int(goal.get("saved_amount", 0))
        for goal in savings_goals
    )

    monthly_data = {}

    for item in transactions:
        month = item.get("date", "")[:7]

        if len(month) != 7:
            continue

        monthly_data.setdefault(
            month, {"income": 0, "expense": 0}
        )

        if item.get("type") == "income":
            monthly_data[month]["income"] += int(
                item.get("amount", 0)
            )
        elif item.get("type") == "expense":
            monthly_data[month]["expense"] += int(
                item.get("amount", 0)
            )

    chart_labels = sorted(monthly_data.keys())[-6:]
    chart_income = [
        monthly_data[month]["income"] for month in chart_labels
    ]
    chart_expense = [
        monthly_data[month]["expense"] for month in chart_labels
    ]

    return render_template(
        "dashboard.html",
        transactions=latest_transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        total_savings_target=total_savings_target,
        total_saved=total_saved,
        chart_labels=chart_labels,
        chart_income=chart_income,
        chart_expense=chart_expense,
    )


@app.route("/transactions")
def transactions_page():
    data = load_data()

    transactions = sorted(
        data["transactions"],
        key=lambda item: item.get("date", ""),
        reverse=True
    )

    return render_template(
        "transactions.html",
        transactions=transactions
    )


@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        transaction_type = request.form.get("type", "")
        category = request.form.get("category", "")
        transaction_date = request.form.get("date", "")
        amount_input = request.form.get("amount", "").strip()

        if not all([
            name, transaction_type, category,
            transaction_date, amount_input
        ]):
            flash("Semua kolom wajib diisi.")
            return redirect(url_for("add_transaction"))

        if (
            transaction_type not in ("income", "expense")
            or category not in CATEGORIES
        ):
            flash("Jenis atau kategori transaksi tidak valid.")
            return redirect(url_for("add_transaction"))

        try:
            amount = parse_positive_amount(amount_input)
            valid_date(transaction_date)
        except (ValueError, TypeError):
            flash("Tanggal atau jumlah transaksi tidak valid.")
            return redirect(url_for("add_transaction"))

        data = load_data()

        new_id = max(
            (int(item.get("id", 0)) for item in data["transactions"]),
            default=0
        ) + 1

        data["transactions"].append({
            "id": new_id,
            "name": name,
            "type": transaction_type,
            "category": category,
            "date": transaction_date,
            "amount": amount,
        })

        save_data(data)
        flash("Transaksi berhasil disimpan!")
        return redirect(url_for("dashboard"))

    return render_template(
        "add_transaction.html",
        today=date.today().isoformat()
    )


@app.route("/edit-transaction/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    data = load_data()

    transaction = next(
        (
            item for item in data["transactions"]
            if item.get("id") == transaction_id
        ),
        None
    )

    if transaction is None:
        flash("Transaksi tidak ditemukan.")
        return redirect(url_for("transactions_page"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        transaction_type = request.form.get("type", "")
        category = request.form.get("category", "")
        transaction_date = request.form.get("date", "")
        amount_input = request.form.get("amount", "").strip()

        if not all([
            name, transaction_type, category,
            transaction_date, amount_input
        ]):
            flash("Semua kolom wajib diisi.")
            return redirect(
                url_for("edit_transaction", transaction_id=transaction_id)
            )

        if (
            transaction_type not in ("income", "expense")
            or category not in CATEGORIES
        ):
            flash("Jenis atau kategori transaksi tidak valid.")
            return redirect(
                url_for("edit_transaction", transaction_id=transaction_id)
            )

        try:
            amount = parse_positive_amount(amount_input)
            valid_date(transaction_date)
        except (ValueError, TypeError):
            flash("Tanggal atau jumlah transaksi tidak valid.")
            return redirect(
                url_for("edit_transaction", transaction_id=transaction_id)
            )

        transaction.update({
            "name": name,
            "type": transaction_type,
            "category": category,
            "date": transaction_date,
            "amount": amount,
        })

        save_data(data)
        flash("Transaksi berhasil diperbarui!")
        return redirect(url_for("transactions_page"))

    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )


@app.route("/delete-transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    data = load_data()
    original_count = len(data["transactions"])

    data["transactions"] = [
        item for item in data["transactions"]
        if item.get("id") != transaction_id
    ]

    if len(data["transactions"]) == original_count:
        flash("Transaksi tidak ditemukan.")
    else:
        save_data(data)
        flash("Transaksi berhasil dihapus.")

    return redirect(url_for("transactions_page"))


@app.route("/savings", methods=["GET", "POST"])
def savings_page():
    data = load_data()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        target_input = request.form.get("target_amount", "").strip()
        saved_input = request.form.get("saved_amount", "0").strip() or "0"

        if not name:
            flash("Nama target wajib diisi.")
            return redirect(url_for("savings_page"))

        try:
            target_amount = parse_positive_amount(target_input)
            saved_amount = parse_positive_amount(
                saved_input, allow_zero=True
            )
        except (ValueError, TypeError):
            flash("Jumlah target atau tabungan tidak valid.")
            return redirect(url_for("savings_page"))

        new_id = max(
            (int(goal.get("id", 0)) for goal in data["savings_goals"]),
            default=0
        ) + 1

        data["savings_goals"].append({
            "id": new_id,
            "name": name,
            "target_amount": target_amount,
            "saved_amount": saved_amount,
        })

        save_data(data)
        flash("Target tabungan berhasil dibuat!")
        return redirect(url_for("savings_page"))

    return render_template(
        "savings.html",
        savings_goals=data["savings_goals"]
    )


@app.route("/add-savings/<int:goal_id>", methods=["POST"])
def add_savings(goal_id):
    data = load_data()

    goal = next(
        (
            item for item in data["savings_goals"]
            if item.get("id") == goal_id
        ),
        None
    )

    if goal is None:
        flash("Target tabungan tidak ditemukan.")
        return redirect(url_for("savings_page"))

    try:
        amount = parse_positive_amount(
            request.form.get("amount", "")
        )
    except (ValueError, TypeError):
        flash("Jumlah tabungan harus berupa angka lebih besar dari nol.")
        return redirect(url_for("savings_page"))

    goal["saved_amount"] = int(goal.get("saved_amount", 0)) + amount

    save_data(data)
    flash("Tabungan berhasil ditambahkan!")
    return redirect(url_for("savings_page"))


@app.route("/delete-savings/<int:goal_id>", methods=["POST"])
def delete_savings(goal_id):
    data = load_data()
    original_count = len(data["savings_goals"])

    data["savings_goals"] = [
        goal for goal in data["savings_goals"]
        if goal.get("id") != goal_id
    ]

    if len(data["savings_goals"]) == original_count:
        flash("Target tabungan tidak ditemukan.")
    else:
        save_data(data)
        flash("Target tabungan berhasil dihapus.")

    return redirect(url_for("savings_page"))


if __name__ == "__main__":
    app.run(debug=True)
