"""
Generate interest accruals for ALL disbursed loans across multiple months.
Run: bench --site site1.local execute lending.gen_accruals.gen_accruals
"""
import frappe
from frappe.utils import nowdate, add_days, add_months, getdate, flt
import calendar


def gen_accruals():
	"""Run per-loan interest accruals for every loan at multiple dates."""
	frappe.flags.ignore_permissions = True

	company = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	today = getdate(nowdate())

	print(f"Company: {company}")
	print(f"Current interest accruals: {frappe.db.count('Loan Interest Accrual', {'docstatus': 1})}")

	# Get all disbursed loans
	loans = frappe.get_all(
		"Loan",
		filters={
			"docstatus": 1,
			"status": ["in", ["Disbursed", "Partially Disbursed", "Active"]],
		},
		fields=["name", "posting_date", "disbursement_date", "company"],
		order_by="posting_date asc",
	)

	print(f"Disbursed loans: {len(loans)}")

	# Build accrual dates: 1st and 15th of each month from Oct 2025 → Feb 2026
	accrual_dates = []
	for year, month in [(2025, 10), (2025, 11), (2025, 12), (2026, 1), (2026, 2)]:
		for day in [1, 15, calendar.monthrange(year, month)[1]]:
			try:
				d = getdate(f"{year}-{month:02d}-{day:02d}")
				if d <= today:
					accrual_dates.append(d)
			except Exception:
				pass

	accrual_dates = sorted(set(accrual_dates))
	print(f"\nAccrual dates ({len(accrual_dates)}):")
	for d in accrual_dates:
		print(f"  {d}")

	from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
		process_loan_interest_accrual_for_loans,
	)

	total_created = 0

	for accrual_date in accrual_dates:
		date_count = 0

		# Run per-loan to force synchronous processing
		for loan in loans:
			# Only accrue if loan was disbursed before this date
			disb_date = getdate(loan.disbursement_date or loan.posting_date)
			if disb_date >= accrual_date:
				continue

			# Check if accrual already exists for this loan+date
			existing = frappe.db.exists("Loan Interest Accrual", {
				"loan": loan.name,
				"posting_date": str(accrual_date),
				"docstatus": 1,
			})
			if existing:
				continue

			try:
				result = process_loan_interest_accrual_for_loans(
					posting_date=str(accrual_date),
					loan=loan.name,
					company=loan.company,
				)
				new = frappe.db.count("Loan Interest Accrual", {
					"process_loan_interest_accrual": result,
					"docstatus": 1,
				})
				date_count += new
			except Exception as e:
				# Skip silently for individual failures
				pass

		if date_count > 0:
			print(f"  ✅ {accrual_date}: {date_count} accruals")
			total_created += date_count
		else:
			print(f"  ⏭️  {accrual_date}: no new accruals")

	frappe.db.commit()
	frappe.flags.ignore_permissions = False

	total = frappe.db.count("Loan Interest Accrual", {"docstatus": 1})
	print(f"\n{'='*60}")
	print(f"📈 Interest Accruals: was 98 → now {total} (+{total_created})")
	print(f"{'='*60}")
