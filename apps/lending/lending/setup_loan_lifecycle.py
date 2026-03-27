"""
Loan Lifecycle Demo Script
Creates the full loan lifecycle data: accounts → approved applications → loans → disbursements → interest accrual

Run:
    bench --site site1.local execute lending.setup_loan_lifecycle.setup_loan_lifecycle
"""
import frappe
from frappe.utils import nowdate, add_days, add_months, getdate, now_datetime, add_to_date, flt


def setup_loan_lifecycle():
	"""Main entry point — creates full lifecycle data for the dashboard."""
	frappe.flags.ignore_permissions = True

	company = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	if not company:
		print("❌ No company found. Run setup_demo_data first.")
		return

	print(f"Using company: {company}")
	abbr = frappe.db.get_value("Company", company, "abbr")
	print(f"Company abbreviation: {abbr}")

	# Step 1: Create GL Accounts
	accounts = create_gl_accounts(company, abbr)

	# Step 2: Update Loan Products with accounts
	update_loan_products_with_accounts(accounts)

	# Step 3: Submit and Approve Loan Applications
	approved_apps = submit_and_approve_applications()

	# Step 4: Create Loans from approved applications
	loans = create_loans_from_applications(approved_apps)

	# Step 5: Submit Loans
	submitted_loans = submit_loans(loans)

	# Step 5.5: Create Security Assignments for secured loans
	create_security_assignments(submitted_loans)

	# Step 6: Create and Submit Disbursements
	disbursements = create_disbursements(submitted_loans)

	# Step 7: Process Interest Accrual
	process_interest_accrual(company)

	frappe.db.commit()
	frappe.flags.ignore_permissions = False

	print_lifecycle_summary()


# =============================================================================
# Step 1: GL Accounts
# =============================================================================

def create_gl_accounts(company, abbr):
	"""Create necessary GL accounts for lending operations."""
	print("\n🏦 Creating GL Accounts")

	# Find parent groups
	asset_parent = frappe.db.get_value("Account", {
		"company": company,
		"root_type": "Asset",
		"is_group": 1,
		"parent_account": ["is", "set"],
		"account_name": ["like", "%Current Asset%"],
	}, "name")

	if not asset_parent:
		asset_parent = frappe.db.get_value("Account", {
			"company": company,
			"root_type": "Asset",
			"is_group": 1,
			"parent_account": ["is", "set"],
		}, "name")

	income_parent = frappe.db.get_value("Account", {
		"company": company,
		"root_type": "Income",
		"is_group": 1,
		"parent_account": ["is", "set"],
		"account_name": ["like", "%Direct Income%"],
	}, "name")

	if not income_parent:
		income_parent = frappe.db.get_value("Account", {
			"company": company,
			"root_type": "Income",
			"is_group": 1,
			"parent_account": ["is", "set"],
		}, "name")

	expense_parent = frappe.db.get_value("Account", {
		"company": company,
		"root_type": "Expense",
		"is_group": 1,
		"parent_account": ["is", "set"],
	}, "name")

	print(f"  Asset parent: {asset_parent}")
	print(f"  Income parent: {income_parent}")
	print(f"  Expense parent: {expense_parent}")

	accounts_to_create = [
		{
			"account_name": "Loan Account",
			"parent_account": asset_parent,
			"root_type": "Asset",
			"account_type": "",
			"key": "loan_account",
		},
		{
			"account_name": "Interest Income on Loans",
			"parent_account": income_parent,
			"root_type": "Income",
			"account_type": "Income Account",
			"key": "interest_income_account",
		},
		{
			"account_name": "Penalty Income on Loans",
			"parent_account": income_parent,
			"root_type": "Income",
			"account_type": "Income Account",
			"key": "penalty_income_account",
		},
		{
			"account_name": "Interest Accrued on Loans",
			"parent_account": asset_parent,
			"root_type": "Asset",
			"account_type": "",
			"key": "interest_accrual_account",
		},
		{
			"account_name": "Penalty Accrued on Loans",
			"parent_account": asset_parent,
			"root_type": "Asset",
			"account_type": "",
			"key": "penalty_accrual_account",
		},
	]

	# Get payment account (bank/cash)
	payment_account = frappe.db.get_value("Account", {
		"company": company,
		"is_group": 0,
		"account_type": "Bank",
	}, "name")

	if not payment_account:
		payment_account = frappe.db.get_value("Account", {
			"company": company,
			"is_group": 0,
			"account_type": "Cash",
		}, "name")

	result = {"payment_account": payment_account}

	for acc in accounts_to_create:
		account_name_full = f"{acc['account_name']} - {abbr}"
		if not frappe.db.exists("Account", account_name_full):
			doc = frappe.get_doc({
				"doctype": "Account",
				"account_name": acc["account_name"],
				"parent_account": acc["parent_account"],
				"company": company,
				"root_type": acc["root_type"],
				"account_type": acc.get("account_type", ""),
				"is_group": 0,
			})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ Created: {account_name_full}")
		else:
			print(f"  ⏭️  {account_name_full} already exists")
		result[acc["key"]] = account_name_full

	print(f"  Payment Account: {result['payment_account']}")
	return result


# =============================================================================
# Step 2: Update Loan Products
# =============================================================================

def update_loan_products_with_accounts(accounts):
	"""Update all loan products with the created GL accounts."""
	print("\n📦 Updating Loan Products with GL Accounts")

	products = frappe.get_all("Loan Product", fields=["name"])
	for prod in products:
		doc = frappe.get_doc("Loan Product", prod.name)
		updated = False

		if not doc.payment_account:
			doc.payment_account = accounts["payment_account"]
			updated = True
		if not doc.loan_account:
			doc.loan_account = accounts["loan_account"]
			updated = True
		if not doc.interest_income_account:
			doc.interest_income_account = accounts["interest_income_account"]
			updated = True
		if not doc.penalty_income_account:
			doc.penalty_income_account = accounts["penalty_income_account"]
			updated = True

		# Set interest accrual account if field exists
		if hasattr(doc, "interest_accrual_account") and not doc.interest_accrual_account:
			doc.interest_accrual_account = accounts.get("interest_accrual_account", "")
			updated = True

		if updated:
			doc.save(ignore_permissions=True)
			print(f"  ✅ Updated: {prod.name}")
		else:
			print(f"  ⏭️  {prod.name} already has accounts")


# =============================================================================
# Step 3: Submit & Approve Loan Applications
# =============================================================================

def submit_and_approve_applications():
	"""Submit all draft loan applications and mark them as approved."""
	print("\n📋 Submitting & Approving Loan Applications")

	applications = frappe.get_all(
		"Loan Application",
		filters={"docstatus": 0},
		fields=["name", "applicant", "loan_product", "loan_amount"],
		order_by="posting_date asc",
	)

	approved = []
	for app in applications:
		try:
			doc = frappe.get_doc("Loan Application", app.name)
			doc.submit()
			# After submit, set status to Approved
			frappe.db.set_value("Loan Application", app.name, "status", "Approved")
			approved.append(app.name)
			print(f"  ✅ {app.name} — {app.applicant} (₹{app.loan_amount:,.0f})")
		except Exception as e:
			print(f"  ⚠️  Could not submit {app.name}: {str(e)[:100]}")

	# Also check already submitted ones
	existing_approved = frappe.get_all(
		"Loan Application",
		filters={"docstatus": 1, "status": "Approved"},
		fields=["name"],
	)
	for ea in existing_approved:
		if ea.name not in approved:
			approved.append(ea.name)

	print(f"\n  Total approved: {len(approved)}")
	return approved


# =============================================================================
# Step 4: Create Loans from Applications
# =============================================================================

def create_loans_from_applications(approved_apps):
	"""Create Loan records from approved applications."""
	print("\n🏠 Creating Loans from Approved Applications")

	from lending.loan_management.doctype.loan_application.loan_application import create_loan

	loans = []
	for app_name in approved_apps:
		# Check if loan already exists for this application
		existing_loan = frappe.db.get_value("Loan", {"loan_application": app_name}, "name")
		if existing_loan:
			print(f"  ⏭️  Loan already exists for {app_name}: {existing_loan}")
			loans.append(existing_loan)
			continue

		try:
			loan_doc = create_loan(app_name)
			loan_doc.posting_date = frappe.db.get_value("Loan Application", app_name, "posting_date")
			loan_doc.insert(ignore_permissions=True)
			loans.append(loan_doc.name)
			print(f"  ✅ {loan_doc.name} from {app_name} (₹{loan_doc.loan_amount:,.0f})")
		except Exception as e:
			print(f"  ⚠️  Could not create loan for {app_name}: {str(e)[:120]}")

	return loans


# =============================================================================
# Step 5: Submit Loans
# =============================================================================

def submit_loans(loan_names):
	"""Submit created loans to make them active."""
	print("\n✍️  Submitting Loans")

	submitted = []
	for loan_name in loan_names:
		doc = frappe.get_doc("Loan", loan_name)
		if doc.docstatus == 1:
			print(f"  ⏭️  {loan_name} already submitted")
			submitted.append(loan_name)
			continue

		try:
			doc.submit()
			submitted.append(loan_name)
			print(f"  ✅ {loan_name} — Status: {doc.status}")
		except Exception as e:
			print(f"  ⚠️  Could not submit {loan_name}: {str(e)[:120]}")

	return submitted


# =============================================================================
# Step 5.5: Loan Security Assignments
# =============================================================================

def create_security_assignments(loan_names):
	"""Create loan security assignments for secured loans."""
	print("\n🔐 Creating Loan Security Assignments")

	from lending.loan_management.doctype.loan_application.loan_application import (
		create_loan_security_assignment,
	)

	for loan_name in loan_names:
		loan_doc = frappe.get_doc("Loan", loan_name)

		# Skip if not secured
		if not loan_doc.is_secured_loan:
			continue

		# Check if assignment already exists
		existing = frappe.db.get_value("Loan Security Assignment", {
			"loan": loan_name,
			"docstatus": 1,
		}, "name")

		if existing:
			print(f"  ⏭️  Assignment exists for {loan_name}: {existing}")
			continue

		try:
			# Get pledges from loan application
			app_name = loan_doc.loan_application
			if app_name:
				assignment = create_loan_security_assignment(
					loan_application=app_name,
					loan=loan_name,
				)
				print(f"  ✅ Security assigned for {loan_name} (from {app_name})")
			else:
				print(f"  ⚠️  No application for {loan_name}, skipping")
		except Exception as e:
			print(f"  ⚠️  Could not assign security for {loan_name}: {str(e)[:120]}")


# =============================================================================
# Step 6: Create Disbursements
# =============================================================================

def create_disbursements(loan_names):
	"""Create and submit loan disbursements."""
	print("\n💸 Creating Loan Disbursements")

	from lending.loan_management.doctype.loan.loan import make_loan_disbursement

	disbursements = []
	today = nowdate()

	for loan_name in loan_names:
		# Check if disbursement exists
		existing = frappe.db.get_value("Loan Disbursement", {
			"against_loan": loan_name,
			"docstatus": 1,
		}, "name")

		if existing:
			print(f"  ⏭️  Disbursement exists for {loan_name}: {existing}")
			disbursements.append(existing)
			continue

		try:
			loan_doc = frappe.get_doc("Loan", loan_name)
			disbursement_amount = loan_doc.loan_amount - flt(loan_doc.disbursed_amount)

			if disbursement_amount <= 0:
				print(f"  ⏭️  {loan_name} already fully disbursed")
				continue

			# Use today for disbursement to avoid date-related issues
			posting_date = today

			disb = make_loan_disbursement(
				loan=loan_name,
				disbursement_amount=disbursement_amount,
				posting_date=posting_date,
				disbursement_date=posting_date,
			)

			# Set repayment start date for term loans
			if loan_doc.is_term_loan:
				disb.repayment_start_date = add_months(getdate(posting_date), 1)
				disb.repayment_periods = loan_doc.repayment_periods

			disb.insert(ignore_permissions=True)
			disb.submit()

			disbursements.append(disb.name)
			print(f"  ✅ {disb.name} for {loan_name} — ₹{disbursement_amount:,.0f}")
		except Exception as e:
			print(f"  ⚠️  Could not disburse {loan_name}: {str(e)[:150]}")

	return disbursements


# =============================================================================
# Step 7: Interest Accrual
# =============================================================================

def process_interest_accrual(company):
	"""Process interest accrual for all active loans."""
	print("\n📊 Processing Interest Accrual")

	try:
		from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
			process_loan_interest_accrual_for_loans,
		)

		today = nowdate()
		active_loans = frappe.get_all(
			"Loan",
			filters={"docstatus": 1, "status": ["in", ["Disbursed", "Partially Disbursed", "Active"]]},
			fields=["name"],
		)

		if active_loans:
			try:
				process_loan_interest_accrual_for_loans(
					posting_date=today,
					loan_product=None,
					loan=None,
					accrual_type="Regular",
				)
				accruals = frappe.db.count("Loan Interest Accrual", {"docstatus": 1})
				print(f"  ✅ Interest accrued for {len(active_loans)} loans ({accruals} accrual records)")
			except Exception as e:
				print(f"  ⚠️  Interest accrual issue: {str(e)[:120]}")
		else:
			print("  ℹ️  No active loans for interest accrual")
	except Exception as e:
		print(f"  ⚠️  Could not process interest accrual: {str(e)[:120]}")


# =============================================================================
# Summary
# =============================================================================

def print_lifecycle_summary():
	"""Print a summary of all lifecycle data."""
	print("\n" + "=" * 60)
	print("📊 LOAN LIFECYCLE SUMMARY")
	print("=" * 60)

	doctypes = {
		"Loan Application (Approved)": ("Loan Application", {"docstatus": 1, "status": "Approved"}),
		"Loan Application (Open)": ("Loan Application", {"docstatus": 0}),
		"Loan (Submitted)": ("Loan", {"docstatus": 1}),
		"Loan (Sanctioned)": ("Loan", {"docstatus": 1, "status": "Sanctioned"}),
		"Loan (Disbursed)": ("Loan", {"docstatus": 1, "status": ["in", ["Disbursed", "Partially Disbursed", "Active"]]}),
		"Loan Disbursement": ("Loan Disbursement", {"docstatus": 1}),
		"Loan Interest Accrual": ("Loan Interest Accrual", {"docstatus": 1}),
		"Loan Repayment Schedule": ("Loan Repayment Schedule", {"docstatus": 1}),
		"Loan Security Assignment": ("Loan Security Assignment", {}),
	}

	for label, (doctype, filters) in doctypes.items():
		try:
			count = frappe.db.count(doctype, filters)
			print(f"  {label:40s}: {count}")
		except Exception:
			print(f"  {label:40s}: N/A")

	# Total amounts
	try:
		total_sanctioned = frappe.db.sql(
			"SELECT SUM(loan_amount) FROM `tabLoan` WHERE docstatus=1", as_list=True
		)[0][0] or 0
		total_disbursed = frappe.db.sql(
			"SELECT SUM(disbursed_amount) FROM `tabLoan Disbursement` WHERE docstatus=1", as_list=True
		)[0][0] or 0
		print(f"\n  {'Total Sanctioned Amount':40s}: ₹{total_sanctioned:,.0f}")
		print(f"  {'Total Disbursed Amount':40s}: ₹{total_disbursed:,.0f}")
	except Exception:
		pass

	print("=" * 60)
	print("\n🎯 Dashboard should now show data at: /app/loan-dashboard")
	print("   Workspace: /app/lending")
