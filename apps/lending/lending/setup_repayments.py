"""
Fill ALL Loan Dashboard Cards with Demo Data.
Run: bench --site site1.local execute lending.setup_repayments.setup_repayments
"""
import frappe
from frappe.utils import nowdate, add_days, getdate, flt, add_months, now_datetime


def setup_repayments():
	"""Fill every dashboard card with data."""
	frappe.flags.ignore_permissions = True

	company = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	abbr = frappe.db.get_value("Company", company, "abbr")
	print(f"Company: {company} ({abbr})")

	today = nowdate()

	# 1. Open Loan Applications (3 new submitted apps with status=Open)
	create_open_applications(company, today)

	# 2. Total Sanctioned Amount (2 new loans kept in Sanctioned status)
	create_sanctioned_loans(company, today)

	# 3. Total Repayment (repay some disbursed loans)
	create_loan_repayments(company, today)

	# 4. Closed Loans (close one fully-repaid loan)
	close_a_loan(company, today)

	# 5. Shortfall data (Applicants with Unpaid Shortfall + Total Shortfall Amount)
	create_shortfall_data(company, today)

	# 6. Total Write Off (write off a small loan)
	create_write_off(company, abbr, today)

	frappe.db.commit()
	frappe.flags.ignore_permissions = False

	print_dashboard_summary()


# ── 1. OPEN LOAN APPLICATIONS ──────────────────────────────────────
def create_open_applications(company, today):
	"""Create 3 submitted Loan Applications with status='Open'."""
	print("\n📋 Creating Open Loan Applications")

	individuals = frappe.get_all("Customer", filters={"customer_type": "Individual"}, pluck="name", limit=3)
	companies = frappe.get_all("Customer", filters={"customer_type": "Company"}, pluck="name", limit=2)

	apps = [
		{
			"applicant": individuals[0] if individuals else None,
			"loan_product": "PL-001",
			"loan_amount": 500000,
			"repayment_periods": 24,
			"desc": "Personal loan for home renovation",
			"email": "open_app_1@demo.com",
			"phone": "+91 9100000001",
			"city": "Mumbai",
			"state": "Maharashtra",
			"zip": 400001,
		},
		{
			"applicant": individuals[1] if len(individuals) > 1 else individuals[0],
			"loan_product": "EL-001",
			"loan_amount": 1200000,
			"repayment_periods": 48,
			"desc": "Education loan for MBA program",
			"email": "open_app_2@demo.com",
			"phone": "+91 9100000002",
			"city": "Pune",
			"state": "Maharashtra",
			"zip": 411001,
		},
		{
			"applicant": companies[0] if companies else individuals[0],
			"loan_product": "BL-001",
			"loan_amount": 3000000,
			"repayment_periods": 36,
			"desc": "Business expansion capital",
			"email": "open_app_3@demo.com",
			"phone": "+91 9100000003",
			"city": "Chennai",
			"state": "Tamil Nadu",
			"zip": 600001,
		},
	]

	count = 0
	for a in apps:
		if frappe.db.exists("Loan Application", {"applicant_email_address": a["email"]}):
			print(f"  ⏭️  {a['email']} already exists")
			continue
		if not a["applicant"]:
			continue
		try:
			doc = frappe.get_doc({
				"doctype": "Loan Application",
				"applicant_type": "Customer",
				"applicant": a["applicant"],
				"company": company,
				"loan_product": a["loan_product"],
				"loan_amount": a["loan_amount"],
				"repayment_method": "Repay Over Number of Periods",
				"repayment_periods": a["repayment_periods"],
				"is_secured_loan": 0,
				"posting_date": today,
				"first_name": "Open",
				"last_name": f"Applicant",
				"applicant_email_address": a["email"],
				"applicant_phone_number": a["phone"],
				"address_line_1": "Demo Address",
				"city": a["city"],
				"state": a["state"],
				"zip_code": a["zip"],
				"description": a["desc"],
			})
			doc.insert(ignore_permissions=True)
			doc.submit()
			frappe.db.set_value("Loan Application", doc.name, "status", "Open")
			count += 1
			print(f"  ✅ {doc.name} — Open — ₹{a['loan_amount']:,.0f}")
		except Exception as e:
			print(f"  ⚠️  {str(e)[:120]}")

	print(f"  Total open applications: {count}")


# ── 2. TOTAL SANCTIONED AMOUNT ─────────────────────────────────────
def create_sanctioned_loans(company, today):
	"""Create 2 loans that stay in Sanctioned status."""
	print("\n🏛️  Creating Sanctioned (un-disbursed) Loans")

	from lending.loan_management.doctype.loan_application.loan_application import create_loan

	individuals = frappe.get_all("Customer", filters={"customer_type": "Individual"}, pluck="name", limit=5)

	sanc_apps = [
		{
			"applicant": individuals[2] if len(individuals) > 2 else individuals[0],
			"loan_product": "PL-002",
			"loan_amount": 700000,
			"email": "sanc_app_1@demo.com",
			"phone": "+91 9200000001",
		},
		{
			"applicant": individuals[3] if len(individuals) > 3 else individuals[0],
			"loan_product": "VL-001",
			"loan_amount": 1500000,
			"email": "sanc_app_2@demo.com",
			"phone": "+91 9200000002",
		},
	]

	count = 0
	for sa in sanc_apps:
		if frappe.db.exists("Loan Application", {"applicant_email_address": sa["email"]}):
			print(f"  ⏭️  {sa['email']} already exists")
			# Check if loan exists
			app = frappe.db.get_value("Loan Application", {"applicant_email_address": sa["email"]}, "name")
			if app and frappe.db.exists("Loan", {"loan_application": app, "status": "Sanctioned"}):
				count += 1
			continue

		try:
			# Create and submit the application
			app_doc = frappe.get_doc({
				"doctype": "Loan Application",
				"applicant_type": "Customer",
				"applicant": sa["applicant"],
				"company": company,
				"loan_product": sa["loan_product"],
				"loan_amount": sa["loan_amount"],
				"repayment_method": "Repay Over Number of Periods",
				"repayment_periods": 36,
				"is_secured_loan": 0,
				"posting_date": today,
				"first_name": "Sanctioned",
				"last_name": "Borrower",
				"applicant_email_address": sa["email"],
				"applicant_phone_number": sa["phone"],
				"address_line_1": "Demo Address",
				"city": "Hyderabad",
				"state": "Telangana",
				"zip_code": 500001,
				"description": f"Loan pending disbursement",
			})
			app_doc.insert(ignore_permissions=True)
			app_doc.submit()
			frappe.db.set_value("Loan Application", app_doc.name, "status", "Approved")

			# Create and submit loan — stays as Sanctioned
			loan_doc = create_loan(app_doc.name)
			loan_doc.posting_date = today
			loan_doc.insert(ignore_permissions=True)
			loan_doc.submit()

			count += 1
			print(f"  ✅ {loan_doc.name} — Sanctioned — ₹{sa['loan_amount']:,.0f}")
		except Exception as e:
			print(f"  ⚠️  {str(e)[:120]}")

	# Count total sanctioned
	total_sanc = frappe.db.sql(
		"SELECT COALESCE(SUM(loan_amount),0) FROM `tabLoan` WHERE docstatus=1 AND status='Sanctioned'"
	)[0][0]
	print(f"  Total Sanctioned Amount: ₹{total_sanc:,.0f}")


# ── 3. TOTAL REPAYMENT ────────────────────────────────────────────
def create_loan_repayments(company, today):
	"""Create repayments for disbursed loans."""
	print("\n💰 Creating Loan Repayments")

	# Get disbursed term loans
	disbursed = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]], "is_term_loan": 1},
		fields=["name", "loan_amount", "applicant_type", "applicant", "company", "loan_product"],
		order_by="loan_amount asc",
		limit=5,
	)

	total_repaid = 0
	for loan in disbursed:
		# Skip if repayment already exists
		if frappe.db.exists("Loan Repayment", {"against_loan": loan.name, "docstatus": 1}):
			existing_amt = frappe.db.get_value("Loan Repayment", {"against_loan": loan.name, "docstatus": 1}, "amount_paid") or 0
			total_repaid += existing_amt
			print(f"  ⏭️  Repayment exists for {loan.name}")
			continue

		try:
			# Get repayment schedule EMI amount
			emi_amount = get_emi_amount(loan.name, loan.loan_amount)

			repayment = frappe.new_doc("Loan Repayment")
			repayment.against_loan = loan.name
			repayment.applicant_type = loan.applicant_type
			repayment.applicant = loan.applicant
			repayment.company = loan.company
			repayment.posting_date = today
			repayment.payment_type = "Regular Payment"
			repayment.amount_paid = emi_amount
			repayment.insert(ignore_permissions=True)
			repayment.submit()

			total_repaid += emi_amount
			print(f"  ✅ {repayment.name} for {loan.name} — ₹{emi_amount:,.0f}")
		except Exception as e:
			print(f"  ⚠️  {loan.name}: {str(e)[:120]}")

	print(f"  Total repaid: ₹{total_repaid:,.0f}")


def get_emi_amount(loan_name, loan_amount):
	"""Get EMI from repayment schedule or calculate a reasonable amount."""
	schedule = frappe.get_all(
		"Loan Repayment Schedule",
		filters={"loan": loan_name, "docstatus": 1},
		fields=["name"],
		limit=1,
	)
	if schedule:
		detail = frappe.get_all(
			"Repayment Schedule",
			filters={"parent": schedule[0].name},
			fields=["total_payment"],
			order_by="payment_date asc",
			limit=1,
		)
		if detail:
			return flt(detail[0].total_payment)
	# Fallback: ~5% of loan amount
	return flt(loan_amount * 0.05, 0)


# ── 4. CLOSED LOANS ───────────────────────────────────────────────
def close_a_loan(company, today):
	"""Close 1 small loan fully."""
	print("\n🔒 Closing a Loan")

	# Check if any loan is already closed
	if frappe.db.exists("Loan", {"docstatus": 1, "status": "Closed"}):
		print("  ⏭️  A closed loan already exists")
		return

	# Pick the smallest disbursed loan
	small_loan = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]], "is_term_loan": 1},
		fields=["name", "loan_amount", "applicant", "company", "loan_product"],
		order_by="loan_amount asc",
		limit=1,
	)

	if not small_loan:
		print("  ⚠️  No disbursed loans to close")
		return

	loan = small_loan[0]
	print(f"  Closing {loan.name} (₹{loan.loan_amount:,.0f})")

	try:
		from lending.loan_management.doctype.loan_repayment.loan_repayment import calculate_amounts

		amounts = calculate_amounts(loan.name, today)
		pending = (
			flt(amounts.get("pending_principal_amount", 0))
			+ flt(amounts.get("interest_amount", 0))
			+ flt(amounts.get("penalty_amount", 0))
			- flt(amounts.get("excess_amount_paid", 0))
		)

		if pending > 0:
			# Make a full repayment to close the loan
			repayment = frappe.new_doc("Loan Repayment")
			repayment.against_loan = loan.name
			repayment.applicant_type = "Customer"
			repayment.applicant = loan.applicant
			repayment.company = loan.company
			repayment.posting_date = today
			repayment.payment_type = "Loan Closure"
			repayment.amount_paid = pending
			repayment.insert(ignore_permissions=True)
			repayment.submit()
			print(f"  ✅ Full repayment: ₹{pending:,.0f}")

		# Request closure
		from lending.loan_management.doctype.loan.loan import request_loan_closure
		result = request_loan_closure(loan.name, posting_date=today, auto_close=1)
		print(f"  ✅ {result.get('message', 'Closed')}")
	except Exception as e:
		# If closure fails, force close via DB
		print(f"  ⚠️  Standard closure failed: {str(e)[:100]}")
		print(f"  Attempting direct close...")
		try:
			frappe.db.set_value("Loan", loan.name, {"status": "Closed", "closure_date": today})
			print(f"  ✅ Loan {loan.name} marked as Closed")
		except Exception as e2:
			print(f"  ❌ Could not close: {str(e2)[:100]}")


# ── 5. SHORTFALL DATA ─────────────────────────────────────────────
def create_shortfall_data(company, today):
	"""Create Loan Security Shortfall records for secured loans."""
	print("\n⚠️  Creating Shortfall Data")

	# Get secured disbursed loans
	secured_loans = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "is_secured_loan": 1, "status": ["in", ["Disbursed", "Active"]]},
		fields=["name", "loan_amount", "applicant_type", "applicant"],
	)

	if not secured_loans:
		print("  ℹ️  No secured disbursed loans found")
		return

	count = 0
	total_shortfall = 0

	for loan in secured_loans:
		# Check if shortfall exists
		if frappe.db.exists("Loan Security Shortfall", {"loan": loan.name, "status": "Pending"}):
			print(f"  ⏭️  Shortfall already exists for {loan.name}")
			count += 1
			continue

		# Create a shortfall (simulate security price drop)
		shortfall_amount = flt(loan.loan_amount * 0.15)  # 15% shortfall
		security_value = flt(loan.loan_amount * 0.70)  # 70% of loan value

		try:
			shortfall = frappe.new_doc("Loan Security Shortfall")
			shortfall.loan = loan.name
			shortfall.applicant_type = loan.applicant_type
			shortfall.applicant = loan.applicant
			shortfall.loan_amount = loan.loan_amount
			shortfall.security_value = security_value
			shortfall.shortfall_amount = shortfall_amount
			shortfall.shortfall_percentage = 15.0
			shortfall.shortfall_time = now_datetime()
			shortfall.status = "Pending"
			shortfall.save(ignore_permissions=True)

			count += 1
			total_shortfall += shortfall_amount
			print(f"  ✅ Shortfall for {loan.name} — ₹{shortfall_amount:,.0f}")
		except Exception as e:
			print(f"  ⚠️  {str(e)[:120]}")

	print(f"  Applicants with shortfall: {count}, Total: ₹{total_shortfall:,.0f}")


# ── 6. LOAN WRITE OFF ─────────────────────────────────────────────
def create_write_off(company, abbr, today):
	"""Create a loan write-off entry."""
	print("\n📝 Creating Write-Off")

	if frappe.db.exists("Loan Write Off", {"docstatus": 1}):
		print("  ⏭️  Write-off already exists")
		return

	# Find a disbursed loan to partially write off
	loan = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]]},
		fields=["name", "loan_amount", "company", "loan_product"],
		order_by="loan_amount asc",
		limit=1,
	)

	if not loan:
		print("  ⚠️  No loans available for write-off")
		return

	loan = loan[0]
	write_off_amount = flt(loan.loan_amount * 0.02)  # 2% write-off

	# Ensure write-off account exists
	write_off_account = f"Write Off - {abbr}"
	if not frappe.db.exists("Account", write_off_account):
		# Find expense parent
		expense_parent = frappe.db.get_value("Account", {
			"company": company, "root_type": "Expense", "is_group": 1,
			"parent_account": ["is", "set"],
		}, "name")
		try:
			acc = frappe.get_doc({
				"doctype": "Account",
				"account_name": "Write Off",
				"parent_account": expense_parent,
				"company": company,
				"root_type": "Expense",
				"is_group": 0,
			})
			acc.insert(ignore_permissions=True)
			print(f"  ✅ Created account: {write_off_account}")
		except Exception as e:
			print(f"  ⚠️  Account creation: {str(e)[:80]}")

	# Also set on company if needed
	company_wo = frappe.db.get_value("Company", company, "write_off_account")
	if not company_wo:
		frappe.db.set_value("Company", company, "write_off_account", write_off_account)

	try:
		wo = frappe.new_doc("Loan Write Off")
		wo.loan = loan.name
		wo.posting_date = today
		wo.write_off_account = write_off_account
		wo.write_off_amount = write_off_amount
		wo.save(ignore_permissions=True)
		wo.submit()
		print(f"  ✅ Write-off {wo.name} — ₹{write_off_amount:,.0f} for {loan.name}")
	except Exception as e:
		print(f"  ⚠️  Write-off failed: {str(e)[:150]}")
		# Try direct insert for dashboard purposes
		try:
			frappe.db.sql("""
				INSERT INTO `tabLoan Write Off` (name, loan, posting_date, write_off_amount, 
					write_off_account, docstatus, company, loan_product, owner, modified_by,
					creation, modified)
				VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 'Administrator', 'Administrator', NOW(), NOW())
			""", (f"LM-WO-{today}", loan.name, today, write_off_amount,
				write_off_account, company, loan.loan_product))
			print(f"  ✅ Write-off record inserted directly — ₹{write_off_amount:,.0f}")
		except Exception as e2:
			print(f"  ❌ Direct insert also failed: {str(e2)[:100]}")


# ── SUMMARY ────────────────────────────────────────────────────────
def print_dashboard_summary():
	"""Print what each dashboard card should show."""
	print("\n" + "=" * 60)
	print("📊 DASHBOARD CARD VALUES")
	print("=" * 60)

	today = nowdate()

	cards = [
		("NEW LOANS", frappe.db.count("Loan", {"docstatus": 1, "creation": [">=", today]})),
		("ACTIVE LOANS", frappe.db.count("Loan", {"docstatus": 1, "status": ["in", ["Disbursed", "Partially Disbursed"]]})),
		("CLOSED LOANS", frappe.db.count("Loan", {"docstatus": 1, "status": "Closed"})),
		("TOTAL DISBURSED", frappe.db.sql("SELECT COALESCE(SUM(disbursed_amount),0) FROM `tabLoan Disbursement` WHERE docstatus=1")[0][0]),
		("OPEN LOAN APPLICATIONS", frappe.db.count("Loan Application", {"docstatus": 1, "status": "Open"})),
		("NEW LOAN APPLICATIONS", frappe.db.count("Loan Application", {"docstatus": 1, "creation": [">=", today]})),
		("TOTAL SANCTIONED AMOUNT", frappe.db.sql("SELECT COALESCE(SUM(loan_amount),0) FROM `tabLoan` WHERE docstatus=1 AND status='Sanctioned'")[0][0]),
		("ACTIVE SECURITIES", frappe.db.count("Loan Security", {"disabled": 0})),
		("APPLICANTS WITH UNPAID SHORTFALL", frappe.db.count("Loan Security Shortfall", {"status": "Pending"})),
		("TOTAL SHORTFALL AMOUNT", frappe.db.sql("SELECT COALESCE(SUM(shortfall_amount),0) FROM `tabLoan Security Shortfall`")[0][0]),
		("TOTAL REPAYMENT", frappe.db.sql("SELECT COALESCE(SUM(amount_paid),0) FROM `tabLoan Repayment` WHERE docstatus=1")[0][0]),
		("TOTAL WRITE OFF", frappe.db.sql("SELECT COALESCE(SUM(write_off_amount),0) FROM `tabLoan Write Off` WHERE docstatus=1")[0][0]),
	]

	for label, value in cards:
		if isinstance(value, float):
			print(f"  {label:40s}: ₹{value:>15,.0f}")
		else:
			print(f"  {label:40s}: {value:>15}")

	print("=" * 60)
	print("\n🎯 Refresh dashboard at: /app/dashboard-view/Loan Dashboard")
