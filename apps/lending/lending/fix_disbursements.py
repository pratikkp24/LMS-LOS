"""
Fix disbursements for loans that are stuck in Sanctioned status.
Run: bench --site site1.local execute lending.fix_disbursements.fix_disbursements
"""
import frappe
from frappe.utils import nowdate, add_days, getdate, flt
import random

random.seed(99)


def fix_disbursements():
	"""Disburse all sanctioned loans."""
	frappe.flags.ignore_permissions = True

	company = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	today = getdate(nowdate())

	# Get all sanctioned loans (submitted but not disbursed)
	sanctioned = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": "Sanctioned"},
		fields=["name", "loan_amount", "loan_application", "creation", "posting_date",
				"company", "applicant_type", "applicant", "loan_product",
				"is_secured_loan", "is_term_loan"],
		order_by="posting_date asc",
	)

	print(f"Found {len(sanctioned)} sanctioned loans to disburse")

	# Keep 2 as sanctioned for the dashboard card
	keep_sanctioned = sanctioned[-2:] if len(sanctioned) > 2 else []
	to_disburse = [l for l in sanctioned if l not in keep_sanctioned]

	print(f"Will disburse {len(to_disburse)}, keeping {len(keep_sanctioned)} as Sanctioned")

	for loan in to_disburse:
		loan_date = getdate(loan.posting_date)
		disb_date = add_days(loan_date, random.randint(1, 5))
		if getdate(disb_date) > today:
			disb_date = today

		try:
			# Create disbursement manually instead of using make_loan_disbursement
			disb = frappe.new_doc("Loan Disbursement")
			disb.against_loan = loan.name
			disb.company = loan.company
			disb.applicant_type = loan.applicant_type
			disb.applicant = loan.applicant
			disb.posting_date = disb_date
			disb.disbursement_date = disb_date
			disb.disbursed_amount = loan.loan_amount

			# Get payment account from loan product
			payment_account = frappe.db.get_value("Loan Product", loan.loan_product, "payment_account")
			if payment_account:
				disb.payment_account = payment_account

			# Get loan account
			loan_account = frappe.db.get_value("Loan Product", loan.loan_product, "loan_account")
			if loan_account:
				disb.loan_account = loan_account

			disb.insert(ignore_permissions=True)
			disb.submit()

			# Backdate creation
			frappe.db.set_value("Loan Disbursement", disb.name, "creation",
				f"{disb_date} 14:{random.randint(0,59):02d}:00", update_modified=False)

			print(f"  ✅ {disb.name} — {loan.name} — ₹{loan.loan_amount:,.0f} on {disb_date}")
		except Exception as e:
			print(f"  ⚠️  {loan.name}: {str(e)[:120]}")

	# Now create repayments for newly disbursed loans
	print("\n💰 Creating Repayments for newly disbursed loans")

	disbursed = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]], "is_term_loan": 1},
		fields=["name", "loan_amount", "applicant_type", "applicant", "company", "creation", "posting_date"],
		order_by="posting_date asc",
	)

	repay_count = 0
	for loan in disbursed:
		existing = frappe.db.count("Loan Repayment", {"against_loan": loan.name, "docstatus": 1})
		if existing >= 1:
			continue

		loan_date = getdate(loan.posting_date)
		repay_date = add_days(loan_date, 30)
		if getdate(repay_date) > today:
			continue

		emi = get_emi(loan.name, loan.loan_amount)
		if emi <= 0:
			continue

		try:
			rep = frappe.new_doc("Loan Repayment")
			rep.against_loan = loan.name
			rep.applicant_type = loan.applicant_type
			rep.applicant = loan.applicant
			rep.company = loan.company
			rep.posting_date = repay_date
			rep.payment_type = "Regular Payment"
			rep.amount_paid = emi
			rep.insert(ignore_permissions=True)
			rep.submit()

			frappe.db.set_value("Loan Repayment", rep.name, "creation",
				f"{repay_date} 16:{random.randint(0,59):02d}:00", update_modified=False)

			repay_count += 1
			print(f"  ✅ {rep.name} for {loan.name} — ₹{emi:,.0f} on {repay_date}")
		except Exception as e:
			print(f"  ⚠️  {loan.name}: {str(e)[:100]}")

	print(f"\n  Created {repay_count} new repayments")

	# Process interest accrual for new loans
	print("\n📊 Processing Interest Accrual for all loans")
	try:
		from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
			process_loan_interest_accrual_for_term_loans,
		)
		process_loan_interest_accrual_for_term_loans(posting_date=nowdate())
		accruals = frappe.db.count("Loan Interest Accrual", {"docstatus": 1})
		print(f"  ✅ Total accruals: {accruals}")
	except Exception as e:
		print(f"  ⚠️  Accrual: {str(e)[:100]}")

	# Add more shortfalls for newly secured loans
	print("\n⚠️  Creating Shortfalls for secured loans")
	secured = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "is_secured_loan": 1, "status": ["in", ["Disbursed", "Active"]]},
		fields=["name", "loan_amount", "applicant_type", "applicant"],
	)
	for loan in secured:
		if not frappe.db.exists("Loan Security Shortfall", {"loan": loan.name, "status": "Pending"}):
			shortfall = frappe.new_doc("Loan Security Shortfall")
			shortfall.loan = loan.name
			shortfall.applicant_type = loan.applicant_type
			shortfall.applicant = loan.applicant
			shortfall.loan_amount = loan.loan_amount
			shortfall.security_value = flt(loan.loan_amount * 0.75)
			shortfall.shortfall_amount = flt(loan.loan_amount * 0.20)
			shortfall.shortfall_percentage = 20.0
			shortfall.shortfall_time = frappe.utils.now_datetime()
			shortfall.status = "Pending"
			shortfall.save(ignore_permissions=True)
			print(f"  ✅ Shortfall: {loan.name} — ₹{shortfall.shortfall_amount:,.0f}")

	frappe.db.commit()
	frappe.flags.ignore_permissions = False

	# Final summary
	print("\n" + "=" * 60)
	print("📊 FINAL DASHBOARD CARD VALUES")
	print("=" * 60)

	print(f"  {'NEW LOANS':40s}: {frappe.db.count('Loan', {'docstatus': 1, 'creation': ['>=', nowdate()]})}")
	print(f"  {'ACTIVE LOANS':40s}: {frappe.db.count('Loan', {'docstatus': 1, 'status': ['in', ['Disbursed', 'Partially Disbursed']]})}")
	print(f"  {'CLOSED LOANS':40s}: {frappe.db.count('Loan', {'docstatus': 1, 'status': 'Closed'})}")
	td = frappe.db.sql("SELECT COALESCE(SUM(disbursed_amount),0) FROM `tabLoan Disbursement` WHERE docstatus=1")[0][0]
	print(f"  {'TOTAL DISBURSED':40s}: ₹{td:,.0f}")
	print(f"  {'OPEN LOAN APPLICATIONS':40s}: {frappe.db.count('Loan Application', {'docstatus': 1, 'status': 'Open'})}")
	print(f"  {'NEW LOAN APPLICATIONS':40s}: {frappe.db.count('Loan Application', {'docstatus': 1, 'creation': ['>=', nowdate()]})}")
	ts = frappe.db.sql("SELECT COALESCE(SUM(loan_amount),0) FROM `tabLoan` WHERE docstatus=1 AND status='Sanctioned'")[0][0]
	print(f"  {'TOTAL SANCTIONED AMOUNT':40s}: ₹{ts:,.0f}")
	print(f"  {'ACTIVE SECURITIES':40s}: {frappe.db.count('Loan Security', {'disabled': 0})}")
	print(f"  {'APPLICANTS W/ SHORTFALL':40s}: {frappe.db.count('Loan Security Shortfall', {'status': 'Pending'})}")
	tsh = frappe.db.sql("SELECT COALESCE(SUM(shortfall_amount),0) FROM `tabLoan Security Shortfall`")[0][0]
	print(f"  {'TOTAL SHORTFALL AMOUNT':40s}: ₹{tsh:,.0f}")
	tr = frappe.db.sql("SELECT COALESCE(SUM(amount_paid),0) FROM `tabLoan Repayment` WHERE docstatus=1")[0][0]
	print(f"  {'TOTAL REPAYMENT':40s}: ₹{tr:,.0f}")
	tw = frappe.db.sql("SELECT COALESCE(SUM(write_off_amount),0) FROM `tabLoan Write Off` WHERE docstatus=1")[0][0]
	print(f"  {'TOTAL WRITE OFF':40s}: ₹{tw:,.0f}")

	print(f"\n  --- Totals ---")
	print(f"  {'Loans':40s}: {frappe.db.count('Loan', {'docstatus': 1})}")
	print(f"  {'Applications':40s}: {frappe.db.count('Loan Application', {'docstatus': 1})}")
	print(f"  {'Disbursements':40s}: {frappe.db.count('Loan Disbursement', {'docstatus': 1})}")
	print(f"  {'Repayments':40s}: {frappe.db.count('Loan Repayment', {'docstatus': 1})}")
	print(f"  {'Interest Accruals':40s}: {frappe.db.count('Loan Interest Accrual', {'docstatus': 1})}")
	print("=" * 60)


def get_emi(loan_name, loan_amount):
	schedule = frappe.get_all("Loan Repayment Schedule",
		filters={"loan": loan_name, "docstatus": 1}, fields=["name"], limit=1)
	if schedule:
		detail = frappe.get_all("Repayment Schedule",
			filters={"parent": schedule[0].name}, fields=["total_payment"],
			order_by="payment_date asc", limit=1)
		if detail:
			return flt(detail[0].total_payment)
	return flt(loan_amount * 0.04, 0)
