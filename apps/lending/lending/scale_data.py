"""
Scale up demo data 2x with dates spread across 4 months.
Run: bench --site site1.local execute lending.scale_data.scale_data
"""
import frappe
from frappe.utils import nowdate, add_days, getdate, flt, now_datetime, add_months
import random

random.seed(42)  # Reproducible

COMPANY = None
ABBR = None

# ── Indian names pool for realistic variety ──
FIRST_NAMES = [
	"Aarav", "Vivaan", "Aditya", "Rohan", "Kabir", "Arjun", "Ishaan",
	"Neha", "Pooja", "Sneha", "Kavita", "Mansi", "Ritu", "Gayatri",
	"Sanjay", "Manoj", "Dinesh", "Rakesh", "Suresh", "Harish",
	"Meera", "Divya", "Swati", "Pallavi", "Nisha", "Tanvi",
	"Kunal", "Vishal", "Nikhil", "Gaurav", "Rahul", "Arun"
]
LAST_NAMES = [
	"Sharma", "Gupta", "Patel", "Reddy", "Nair", "Iyer", "Desai",
	"Joshi", "Kulkarni", "Menon", "Bhat", "Rao", "Verma", "Mishra",
	"Chauhan", "Agarwal", "Malhotra", "Kapoor", "Mukherjee", "Pillai"
]
CITIES = [
	("Mumbai", "Maharashtra", 400001),
	("Delhi", "Delhi", 110001),
	("Bangalore", "Karnataka", 560001),
	("Hyderabad", "Telangana", 500001),
	("Chennai", "Tamil Nadu", 600001),
	("Pune", "Maharashtra", 411001),
	("Kolkata", "West Bengal", 700001),
	("Ahmedabad", "Gujarat", 380001),
	("Jaipur", "Rajasthan", 302001),
	("Lucknow", "Uttar Pradesh", 226001),
	("Chandigarh", "Chandigarh", 160001),
	("Kochi", "Kerala", 682001),
	("Indore", "Madhya Pradesh", 452001),
	("Noida", "Uttar Pradesh", 201301),
	("Gurgaon", "Haryana", 122001),
]

# This is the date spread: loans will be created -120 days to today
DATE_SPREAD_DAYS = 120


def scale_data():
	"""Main entry — double the data with date spread."""
	global COMPANY, ABBR
	frappe.flags.ignore_permissions = True

	COMPANY = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	ABBR = frappe.db.get_value("Company", COMPANY, "abbr")
	print(f"Company: {COMPANY} ({ABBR})")

	today = getdate(nowdate())

	# Get existing customers
	customers = frappe.get_all("Customer", fields=["name", "customer_type"], limit=20)
	individual_customers = [c.name for c in customers if c.customer_type == "Individual"]
	company_customers = [c.name for c in customers if c.customer_type == "Company"]
	print(f"Customers: {len(individual_customers)} individual, {len(company_customers)} company")

	# Get existing loan products
	products = frappe.get_all("Loan Product", fields=["name"], pluck="name")
	print(f"Loan Products: {products}")

	# STEP 1: Create ~20 new loan applications spread across dates
	new_apps = create_spread_applications(today, individual_customers, company_customers, products)

	# STEP 2: Approve + create loans + disburse (spread across dates)
	new_loans = process_spread_loans(today, new_apps)

	# STEP 3: Create additional repayments spread across dates
	create_spread_repayments(today)

	# STEP 4: Create additional shortfalls
	create_more_shortfalls(today)

	# STEP 5: Create more write-offs
	create_more_writeoffs(today)

	# STEP 6: Backdate some existing records for chart spread
	backdate_existing_records(today)

	frappe.db.commit()
	frappe.flags.ignore_permissions = False
	print_summary()


# ═══════════════════════════════════════════════════════════════
# STEP 1: New Applications Spread Across Dates
# ═══════════════════════════════════════════════════════════════
def create_spread_applications(today, individuals, companies, products):
	"""Create 20 new loan applications spread across the last 4 months."""
	print("\n" + "=" * 60)
	print("📋 STEP 1: Creating 20 New Loan Applications (date-spread)")
	print("=" * 60)

	# Define 20 new applications with staggered dates
	app_configs = [
		# ── Batch 1: 90-120 days ago ──
		{"product": "PL-001", "amount": 600000, "periods": 24, "days_ago": 115, "type": "ind"},
		{"product": "HL-001", "amount": 4500000, "periods": 180, "days_ago": 110, "type": "ind", "secured": True, "security": "SEC-RP-002"},
		{"product": "BL-001", "amount": 2500000, "periods": 36, "days_ago": 105, "type": "co"},
		{"product": "VL-001", "amount": 2800000, "periods": 48, "days_ago": 100, "type": "ind"},
		# ── Batch 2: 60-90 days ago ──
		{"product": "PL-002", "amount": 950000, "periods": 18, "days_ago": 88, "type": "ind"},
		{"product": "EL-001", "amount": 1800000, "periods": 60, "days_ago": 82, "type": "ind"},
		{"product": "GL-001", "amount": 350000, "periods": 0, "days_ago": 78, "type": "ind"},
		{"product": "LAP-001", "amount": 6000000, "periods": 96, "days_ago": 72, "type": "co", "secured": True, "security": "SEC-CP-001"},
		{"product": "BL-001", "amount": 4000000, "periods": 48, "days_ago": 65, "type": "co"},
		# ── Batch 3: 30-60 days ago ──
		{"product": "PL-001", "amount": 1100000, "periods": 30, "days_ago": 55, "type": "ind"},
		{"product": "VL-001", "amount": 1600000, "periods": 36, "days_ago": 48, "type": "ind"},
		{"product": "HL-002", "amount": 7500000, "periods": 240, "days_ago": 42, "type": "ind", "secured": True, "security": "SEC-RP-001"},
		{"product": "EL-001", "amount": 2200000, "periods": 72, "days_ago": 38, "type": "ind"},
		{"product": "BL-001", "amount": 3200000, "periods": 36, "days_ago": 32, "type": "co"},
		# ── Batch 4: 0-30 days ago ──
		{"product": "PL-001", "amount": 750000, "periods": 24, "days_ago": 25, "type": "ind"},
		{"product": "GL-001", "amount": 280000, "periods": 0, "days_ago": 20, "type": "ind"},
		{"product": "VL-001", "amount": 3200000, "periods": 60, "days_ago": 15, "type": "ind"},
		{"product": "PL-002", "amount": 1300000, "periods": 24, "days_ago": 10, "type": "ind"},
		{"product": "LOC-001", "amount": 2000000, "periods": 12, "days_ago": 5, "type": "co"},
		{"product": "BL-001", "amount": 1800000, "periods": 24, "days_ago": 2, "type": "co"},
	]

	created = []
	for i, cfg in enumerate(app_configs):
		email = f"scale_app_{i+1:02d}@demo.com"
		if frappe.db.exists("Loan Application", {"applicant_email_address": email}):
			existing = frappe.db.get_value("Loan Application", {"applicant_email_address": email}, "name")
			created.append({"name": existing, "date": str(add_days(today, -cfg["days_ago"])), "cfg": cfg})
			print(f"  ⏭️  {email} → {existing}")
			continue

		first = random.choice(FIRST_NAMES)
		last = random.choice(LAST_NAMES)
		city, state, zip_code = random.choice(CITIES)
		posting_date = add_days(today, -cfg["days_ago"])

		if cfg["type"] == "ind":
			applicant = random.choice(individuals)
		else:
			applicant = random.choice(companies)

		app_data = {
			"doctype": "Loan Application",
			"applicant_type": "Customer",
			"applicant": applicant,
			"company": COMPANY,
			"loan_product": cfg["product"],
			"loan_amount": cfg["amount"],
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": cfg["periods"] or 12,
			"is_secured_loan": 1 if cfg.get("secured") else 0,
			"posting_date": posting_date,
			"first_name": first,
			"last_name": last,
			"applicant_email_address": email,
			"applicant_phone_number": f"+91 9{random.randint(100000000, 999999999)}",
			"address_line_1": f"{random.randint(1,200)}, {random.choice(['MG Road','Station Road','Market Street','Ring Road','Lake View'])}",
			"city": city,
			"state": state,
			"zip_code": zip_code,
			"description": f"Loan application for {cfg['product']}",
		}

		# Add pledges for secured loans
		if cfg.get("secured"):
			sec = cfg["security"]
			sec_price = frappe.db.get_value("Loan Security Price", {"loan_security": sec}, "loan_security_price") or 10000000
			app_data["proposed_pledges"] = [{"loan_security": sec, "qty": 1, "loan_security_price": sec_price}]

		try:
			doc = frappe.get_doc(app_data)
			doc.insert(ignore_permissions=True)
			# Backdate the creation field
			frappe.db.set_value("Loan Application", doc.name, "creation", f"{posting_date} 10:{random.randint(0,59):02d}:00", update_modified=False)
			created.append({"name": doc.name, "date": str(posting_date), "cfg": cfg})
			print(f"  ✅ {doc.name} — {first} {last} — ₹{cfg['amount']:,.0f} on {posting_date}")
		except Exception as e:
			print(f"  ⚠️  {email}: {str(e)[:100]}")

	print(f"\n  Created/found {len(created)} applications")
	return created


# ═══════════════════════════════════════════════════════════════
# STEP 2: Process Loans (Approve → Create → Submit → Disburse)
# ═══════════════════════════════════════════════════════════════
def process_spread_loans(today, app_list):
	"""Take each application through the full lifecycle with date-appropriate timestamps."""
	print("\n" + "=" * 60)
	print("🏦 STEP 2: Full Lifecycle for New Applications")
	print("=" * 60)

	from lending.loan_management.doctype.loan_application.loan_application import create_loan
	from lending.loan_management.doctype.loan.loan import make_loan_disbursement
	from lending.loan_management.doctype.loan_application.loan_application import create_loan_security_assignment

	loans_created = []

	for entry in app_list:
		app_name = entry["name"]
		app_date = getdate(entry["date"])
		cfg = entry["cfg"]

		# Check current state
		app_status = frappe.db.get_value("Loan Application", app_name, ["docstatus", "status"], as_dict=True)
		if not app_status:
			continue

		# ── A. Submit & Approve the application ──
		if app_status.docstatus == 0:
			try:
				app_doc = frappe.get_doc("Loan Application", app_name)
				app_doc.submit()
				frappe.db.set_value("Loan Application", app_name, "status", "Approved")
				print(f"  ✅ Approved: {app_name}")
			except Exception as e:
				print(f"  ⚠️  Cannot approve {app_name}: {str(e)[:80]}")
				continue
		elif app_status.status != "Approved":
			frappe.db.set_value("Loan Application", app_name, "status", "Approved")

		# ── B. Create Loan ──
		existing_loan = frappe.db.get_value("Loan", {"loan_application": app_name}, "name")
		if existing_loan:
			loans_created.append({"name": existing_loan, "date": str(app_date), "cfg": cfg})
			print(f"  ⏭️  Loan exists: {existing_loan}")
			continue

		try:
			loan_date = add_days(app_date, random.randint(2, 7))  # Loan created a few days after app
			if getdate(loan_date) > getdate(today):
				loan_date = today

			loan_doc = create_loan(app_name)
			loan_doc.posting_date = loan_date
			loan_doc.insert(ignore_permissions=True)

			# Backdate creation
			frappe.db.set_value("Loan", loan_doc.name, "creation",
				f"{loan_date} 11:{random.randint(0,59):02d}:00", update_modified=False)

			# Submit the loan
			loan_doc.reload()
			loan_doc.submit()
			print(f"  ✅ Loan {loan_doc.name} — Sanctioned on {loan_date} — ₹{cfg['amount']:,.0f}")

			# ── C. Security Assignment for secured loans ──
			if cfg.get("secured"):
				try:
					assignment = create_loan_security_assignment(
						loan_application=app_name,
						loan=loan_doc.name,
					)
					print(f"      🔐 Security assigned")
				except Exception as e:
					print(f"      ⚠️  Security: {str(e)[:60]}")

			# ── D. Disburse ──
			try:
				disb_date = add_days(loan_date, random.randint(1, 5))
				if getdate(disb_date) > getdate(today):
					disb_date = today

				disb_doc = make_loan_disbursement(loan_doc.name)
				disb = frappe.get_doc(disb_doc)
				disb.posting_date = disb_date
				disb.disbursement_date = disb_date

				# For non-term (LOC) set amount explicitly
				if not loan_doc.is_term_loan:
					disb.disbursed_amount = cfg["amount"]

				disb.insert(ignore_permissions=True)
				disb.submit()

				# Backdate
				frappe.db.set_value("Loan Disbursement", disb.name, "creation",
					f"{disb_date} 14:{random.randint(0,59):02d}:00", update_modified=False)

				print(f"      💸 Disbursed on {disb_date}")
			except Exception as e:
				print(f"      ⚠️  Disbursement: {str(e)[:80]}")

			loans_created.append({"name": loan_doc.name, "date": str(loan_date), "cfg": cfg})

		except Exception as e:
			print(f"  ⚠️  Loan creation for {app_name}: {str(e)[:100]}")

	print(f"\n  Total loans created/processed: {len(loans_created)}")
	return loans_created


# ═══════════════════════════════════════════════════════════════
# STEP 3: Spread Repayments
# ═══════════════════════════════════════════════════════════════
def create_spread_repayments(today):
	"""Create repayments for loans at different dates."""
	print("\n" + "=" * 60)
	print("💰 STEP 3: Creating Spread Repayments")
	print("=" * 60)

	# Get all disbursed term loans
	loans = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]], "is_term_loan": 1},
		fields=["name", "loan_amount", "applicant_type", "applicant", "company", "creation"],
		order_by="creation asc",
	)

	repay_count = 0
	total_repaid = 0

	for loan in loans:
		# Skip if already has repayment
		existing_count = frappe.db.count("Loan Repayment", {"against_loan": loan.name, "docstatus": 1})
		if existing_count >= 2:
			continue

		# Create 1-2 repayments
		num_repayments = min(2 - existing_count, random.randint(1, 2))
		loan_create_date = getdate(loan.creation)

		for j in range(num_repayments):
			repay_date = add_days(loan_create_date, 30 * (j + 1 + existing_count))
			if getdate(repay_date) > getdate(today):
				continue

			emi = get_emi_amount(loan.name, loan.loan_amount)
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

				# Backdate creation
				frappe.db.set_value("Loan Repayment", rep.name, "creation",
					f"{repay_date} 16:{random.randint(0,59):02d}:00", update_modified=False)

				repay_count += 1
				total_repaid += emi
				print(f"  ✅ {rep.name} for {loan.name} — ₹{emi:,.0f} on {repay_date}")
			except Exception as e:
				print(f"  ⚠️  {loan.name}: {str(e)[:80]}")

	print(f"\n  Created {repay_count} repayments, Total: ₹{total_repaid:,.0f}")


def get_emi_amount(loan_name, loan_amount):
	"""Get EMI from schedule or calculate."""
	schedule = frappe.get_all(
		"Loan Repayment Schedule",
		filters={"loan": loan_name, "docstatus": 1},
		fields=["name"], limit=1,
	)
	if schedule:
		detail = frappe.get_all(
			"Repayment Schedule",
			filters={"parent": schedule[0].name},
			fields=["total_payment"],
			order_by="payment_date asc", limit=1,
		)
		if detail:
			return flt(detail[0].total_payment)
	return flt(loan_amount * 0.04, 0)


# ═══════════════════════════════════════════════════════════════
# STEP 4: More Shortfalls
# ═══════════════════════════════════════════════════════════════
def create_more_shortfalls(today):
	"""Add shortfall records for more secured loans."""
	print("\n" + "=" * 60)
	print("⚠️  STEP 4: Additional Shortfalls")
	print("=" * 60)

	secured = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "is_secured_loan": 1, "status": ["in", ["Disbursed", "Active"]]},
		fields=["name", "loan_amount", "applicant_type", "applicant"],
	)

	count = 0
	for loan in secured:
		if frappe.db.exists("Loan Security Shortfall", {"loan": loan.name, "status": "Pending"}):
			count += 1
			continue

		shortfall_pct = random.uniform(0.10, 0.25)
		shortfall = frappe.new_doc("Loan Security Shortfall")
		shortfall.loan = loan.name
		shortfall.applicant_type = loan.applicant_type
		shortfall.applicant = loan.applicant
		shortfall.loan_amount = loan.loan_amount
		shortfall.security_value = flt(loan.loan_amount * (1 - shortfall_pct))
		shortfall.shortfall_amount = flt(loan.loan_amount * shortfall_pct)
		shortfall.shortfall_percentage = shortfall_pct * 100
		shortfall.shortfall_time = now_datetime()
		shortfall.status = "Pending"
		shortfall.save(ignore_permissions=True)
		count += 1
		print(f"  ✅ Shortfall for {loan.name} — ₹{shortfall.shortfall_amount:,.0f}")

	print(f"  Total pending shortfalls: {count}")


# ═══════════════════════════════════════════════════════════════
# STEP 5: More Write-offs
# ═══════════════════════════════════════════════════════════════
def create_more_writeoffs(today):
	"""Create additional write-off records."""
	print("\n" + "=" * 60)
	print("📝 STEP 5: Additional Write-offs")
	print("=" * 60)

	existing_wo = frappe.db.count("Loan Write Off", {"docstatus": 1})
	if existing_wo >= 2:
		print(f"  ⏭️  Already have {existing_wo} write-offs")
		return

	# Get a loan for write-off
	loans = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]]},
		fields=["name", "loan_amount", "company", "loan_product"],
		order_by="loan_amount asc",
		limit=3,
	)

	write_off_account = f"Write Off - {ABBR}"
	if not frappe.db.exists("Account", write_off_account):
		expense_parent = frappe.db.get_value("Account", {
			"company": COMPANY, "root_type": "Expense", "is_group": 1,
			"parent_account": ["is", "set"],
		}, "name")
		try:
			frappe.get_doc({
				"doctype": "Account", "account_name": "Write Off",
				"parent_account": expense_parent, "company": COMPANY,
				"root_type": "Expense", "is_group": 0,
			}).insert(ignore_permissions=True)
		except Exception:
			pass

	for loan in loans[existing_wo:2]:
		wo_amount = flt(loan.loan_amount * 0.03)
		wo_date = add_days(today, -random.randint(5, 30))

		try:
			wo = frappe.new_doc("Loan Write Off")
			wo.loan = loan.name
			wo.posting_date = wo_date
			wo.write_off_account = write_off_account
			wo.write_off_amount = wo_amount
			wo.save(ignore_permissions=True)
			wo.submit()
			frappe.db.set_value("Loan Write Off", wo.name, "creation",
				f"{wo_date} 15:00:00", update_modified=False)
			print(f"  ✅ Write-off {wo.name} — ₹{wo_amount:,.0f} on {wo_date}")
		except Exception as e:
			print(f"  ⚠️  {str(e)[:100]}")
			# Direct insert fallback
			try:
				wname = f"LM-WO-{wo_date}-{loan.name[-3:]}"
				if not frappe.db.exists("Loan Write Off", wname):
					frappe.db.sql("""
						INSERT INTO `tabLoan Write Off`
						(name, loan, posting_date, write_off_amount, write_off_account,
						docstatus, company, loan_product, owner, modified_by, creation, modified)
						VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 'Administrator', 'Administrator', %s, %s)
					""", (wname, loan.name, wo_date, wo_amount, write_off_account,
						COMPANY, loan.loan_product, f"{wo_date} 15:00:00", f"{wo_date} 15:00:00"))
					print(f"  ✅ Direct: {wname} — ₹{wo_amount:,.0f}")
			except Exception as e2:
				print(f"  ❌ {str(e2)[:80]}")


# ═══════════════════════════════════════════════════════════════
# STEP 6: Backdate Existing Records for Chart Spread
# ═══════════════════════════════════════════════════════════════
def backdate_existing_records(today):
	"""Spread existing loan/disbursement creation dates across previous months for chart variety."""
	print("\n" + "=" * 60)
	print("📅 STEP 6: Spreading Existing Records Across Dates")
	print("=" * 60)

	# Get ALL loans ordered by name
	all_loans = frappe.get_all(
		"Loan", filters={"docstatus": 1}, fields=["name", "posting_date", "creation"],
		order_by="name asc"
	)

	# Only backdate if most loans have today's date
	today_loans = [l for l in all_loans if getdate(l.creation) == getdate(today)]
	if len(today_loans) < 5:
		print("  ⏭️  Records already spread — skipping")
		return

	# Spread the old loans across different dates
	# Pick original 12 loans and spread them
	original_loans = all_loans[:12]
	day_offsets = [95, 88, 80, 72, 65, 55, 45, 38, 28, 20, 12, 5]

	for i, loan in enumerate(original_loans):
		if i >= len(day_offsets):
			break

		new_date = add_days(today, -day_offsets[i])
		new_creation = f"{new_date} {10 + (i % 8)}:{(i * 7) % 60:02d}:00"

		# Update loan
		frappe.db.sql("""
			UPDATE `tabLoan`
			SET creation = %s, posting_date = %s, modified = %s
			WHERE name = %s
		""", (new_creation, new_date, new_creation, loan.name))

		# Update associated application
		app_name = frappe.db.get_value("Loan", loan.name, "loan_application")
		if app_name:
			app_date = add_days(new_date, -random.randint(3, 10))
			app_creation = f"{app_date} 09:{(i * 11) % 60:02d}:00"
			frappe.db.sql("""
				UPDATE `tabLoan Application`
				SET creation = %s, posting_date = %s, modified = %s
				WHERE name = %s
			""", (app_creation, app_date, app_creation, app_name))

		# Update associated disbursement
		disb_name = frappe.db.get_value("Loan Disbursement", {"against_loan": loan.name, "docstatus": 1}, "name")
		if disb_name:
			disb_date = add_days(new_date, random.randint(1, 5))
			if getdate(disb_date) > getdate(today):
				disb_date = today
			disb_creation = f"{disb_date} 14:{(i * 13) % 60:02d}:00"
			frappe.db.sql("""
				UPDATE `tabLoan Disbursement`
				SET creation = %s, posting_date = %s, disbursement_date = %s, modified = %s
				WHERE name = %s
			""", (disb_creation, disb_date, disb_date, disb_creation, disb_name))

		print(f"  📅 {loan.name}: {new_date} | App: {app_name or 'N/A'} | Disb: {disb_name or 'N/A'}")

	print(f"\n  Spread {min(len(original_loans), len(day_offsets))} loans across dates")


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
def print_summary():
	"""Print final dashboard summary."""
	today = nowdate()

	print("\n" + "=" * 60)
	print("📊 FINAL DASHBOARD CARD VALUES (2x Data)")
	print("=" * 60)

	cards = [
		("NEW LOANS", frappe.db.count("Loan", {"docstatus": 1, "creation": [">=", today]})),
		("ACTIVE LOANS", frappe.db.count("Loan", {"docstatus": 1, "status": ["in", ["Disbursed", "Partially Disbursed"]]})),
		("CLOSED LOANS", frappe.db.count("Loan", {"docstatus": 1, "status": "Closed"})),
		("TOTAL DISBURSED", frappe.db.sql("SELECT COALESCE(SUM(disbursed_amount),0) FROM `tabLoan Disbursement` WHERE docstatus=1")[0][0]),
		("OPEN LOAN APPLICATIONS", frappe.db.count("Loan Application", {"docstatus": 1, "status": "Open"})),
		("NEW LOAN APPLICATIONS", frappe.db.count("Loan Application", {"docstatus": 1, "creation": [">=", today]})),
		("TOTAL SANCTIONED AMOUNT", frappe.db.sql("SELECT COALESCE(SUM(loan_amount),0) FROM `tabLoan` WHERE docstatus=1 AND status='Sanctioned'")[0][0]),
		("ACTIVE SECURITIES", frappe.db.count("Loan Security", {"disabled": 0})),
		("APPLICANTS W/ SHORTFALL", frappe.db.count("Loan Security Shortfall", {"status": "Pending"})),
		("TOTAL SHORTFALL AMOUNT", frappe.db.sql("SELECT COALESCE(SUM(shortfall_amount),0) FROM `tabLoan Security Shortfall`")[0][0]),
		("TOTAL REPAYMENT", frappe.db.sql("SELECT COALESCE(SUM(amount_paid),0) FROM `tabLoan Repayment` WHERE docstatus=1")[0][0]),
		("TOTAL WRITE OFF", frappe.db.sql("SELECT COALESCE(SUM(write_off_amount),0) FROM `tabLoan Write Off` WHERE docstatus=1")[0][0]),
	]

	for label, value in cards:
		if isinstance(value, float):
			print(f"  {label:40s}: ₹{value:>15,.0f}")
		else:
			print(f"  {label:40s}: {value:>15}")

	# Additional counts
	print("\n  --- Additional Metrics ---")
	print(f"  {'Total Loans':40s}: {frappe.db.count('Loan', {'docstatus': 1}):>15}")
	print(f"  {'Total Loan Applications':40s}: {frappe.db.count('Loan Application', {'docstatus': 1}):>15}")
	print(f"  {'Total Disbursements':40s}: {frappe.db.count('Loan Disbursement', {'docstatus': 1}):>15}")
	print(f"  {'Total Repayments':40s}: {frappe.db.count('Loan Repayment', {'docstatus': 1}):>15}")
	print(f"  {'Total Interest Accruals':40s}: {frappe.db.count('Loan Interest Accrual', {'docstatus': 1}):>15}")
	print(f"  {'Total Repayment Schedules':40s}: {frappe.db.count('Loan Repayment Schedule', {'docstatus': 1}):>15}")
	print("=" * 60)
	print("\n🎯 Refresh: /app/dashboard-view/Loan Dashboard")
