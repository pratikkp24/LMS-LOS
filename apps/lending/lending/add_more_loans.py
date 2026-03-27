"""
Add 25+ more loans (reach ~60 total) with full lifecycle + interest accruals across months.
Run: bench --site site1.local execute lending.add_more_loans.add_more_loans
"""
import frappe
from frappe.utils import nowdate, add_days, getdate, flt, now_datetime, add_months
import random

random.seed(2026)

COMPANY = None
ABBR = None

FIRST_NAMES = [
	"Aarav", "Vivaan", "Aditya", "Rohan", "Kabir", "Arjun", "Ishaan",
	"Neha", "Pooja", "Sneha", "Kavita", "Mansi", "Ritu", "Gayatri",
	"Sanjay", "Manoj", "Dinesh", "Rakesh", "Suresh", "Harish",
	"Meera", "Divya", "Swati", "Pallavi", "Nisha", "Tanvi",
	"Kunal", "Vishal", "Nikhil", "Gaurav", "Rahul", "Arun",
	"Vikram", "Harsh", "Prateek", "Varun", "Karan", "Sahil",
	"Shruti", "Aditi", "Anushka", "Bhavna", "Chitra", "Diya",
]
LAST_NAMES = [
	"Sharma", "Gupta", "Patel", "Reddy", "Nair", "Iyer", "Desai",
	"Joshi", "Kulkarni", "Menon", "Bhat", "Rao", "Verma", "Mishra",
	"Chauhan", "Agarwal", "Malhotra", "Kapoor", "Mukherjee", "Pillai",
	"Tiwari", "Saxena", "Khanna", "Mehta", "Banerjee", "Sen",
]
CITIES = [
	("Mumbai", "Maharashtra", 400001), ("Delhi", "Delhi", 110001),
	("Bangalore", "Karnataka", 560001), ("Hyderabad", "Telangana", 500001),
	("Chennai", "Tamil Nadu", 600001), ("Pune", "Maharashtra", 411001),
	("Kolkata", "West Bengal", 700001), ("Ahmedabad", "Gujarat", 380001),
	("Jaipur", "Rajasthan", 302001), ("Lucknow", "Uttar Pradesh", 226001),
	("Chandigarh", "Chandigarh", 160001), ("Kochi", "Kerala", 682001),
	("Indore", "Madhya Pradesh", 452001), ("Noida", "Uttar Pradesh", 201301),
	("Gurgaon", "Haryana", 122001), ("Bhopal", "Madhya Pradesh", 462001),
	("Nagpur", "Maharashtra", 440001), ("Coimbatore", "Tamil Nadu", 641001),
	("Visakhapatnam", "Andhra Pradesh", 530001), ("Surat", "Gujarat", 395001),
]
STREETS = [
	"MG Road", "Station Road", "Market Street", "Ring Road", "Lake View Road",
	"Gandhi Nagar", "Nehru Street", "Civil Lines", "Mall Road", "Church Street",
	"Brigade Road", "Anna Salai", "Park Street", "Commercial Street", "SP Road",
]


def add_more_loans():
	"""Add 25+ loans with full lifecycle + mass interest accruals."""
	global COMPANY, ABBR
	frappe.flags.ignore_permissions = True

	COMPANY = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	ABBR = frappe.db.get_value("Company", COMPANY, "abbr")
	today = getdate(nowdate())

	print(f"Company: {COMPANY} ({ABBR})")
	print(f"Current loans: {frappe.db.count('Loan', {'docstatus': 1})}")
	print(f"Current interest accruals: {frappe.db.count('Loan Interest Accrual', {'docstatus': 1})}")

	customers_ind = frappe.get_all("Customer", filters={"customer_type": "Individual"}, pluck="name")
	customers_co = frappe.get_all("Customer", filters={"customer_type": "Company"}, pluck="name")
	products = frappe.get_all("Loan Product", pluck="name")
	print(f"Customers: {len(customers_ind)} ind, {len(customers_co)} co | Products: {products}")

	# ── STEP 1: Create 26 new loan applications ──
	new_apps = create_bulk_applications(today, customers_ind, customers_co, products)

	# ── STEP 2: Process through full lifecycle ──
	new_loans = process_lifecycle(today, new_apps)

	# ── STEP 3: Create repayments for older loans ──
	create_bulk_repayments(today)

	# ── STEP 4: Run interest accruals across multiple months ──
	run_mass_interest_accruals(today)

	# ── STEP 5: Add more shortfalls & write-offs ──
	add_extra_shortfalls_writeoffs(today)

	frappe.db.commit()
	frappe.flags.ignore_permissions = False
	print_final_summary()


def create_bulk_applications(today, ind, co, products):
	"""Create 26 new applications spread Nov 2025 → Feb 2026."""
	print("\n" + "=" * 60)
	print("📋 STEP 1: Creating 26 New Loan Applications")
	print("=" * 60)

	# 26 configs spread across 4 months, each with a unique email identifier
	configs = [
		# ── Nov 2025 (days_ago 110-120) ──
		{"prod": "PL-001", "amt": 550000,  "per": 18, "days": 118, "t": "i"},
		{"prod": "BL-001", "amt": 3500000, "per": 48, "days": 115, "t": "c"},
		{"prod": "VL-001", "amt": 2200000, "per": 48, "days": 112, "t": "i"},
		{"prod": "HL-001", "amt": 6500000, "per": 240, "days": 108, "t": "i", "sec": True, "sy": "SEC-RP-002"},
		{"prod": "PL-002", "amt": 850000,  "per": 24, "days": 104, "t": "i"},
		{"prod": "EL-001", "amt": 2000000, "per": 72, "days": 100, "t": "i"},
		# ── Dec 2025 (days_ago 70-99) ──
		{"prod": "GL-001", "amt": 450000,  "per": 12, "days": 95, "t": "i"},
		{"prod": "BL-001", "amt": 4200000, "per": 36, "days": 90, "t": "c"},
		{"prod": "LAP-001","amt": 7000000, "per": 120,"days": 85, "t": "c", "sec": True, "sy": "SEC-CP-001"},
		{"prod": "PL-001", "amt": 1250000, "per": 36, "days": 80, "t": "i"},
		{"prod": "VL-001", "amt": 1800000, "per": 36, "days": 75, "t": "i"},
		{"prod": "EL-001", "amt": 1500000, "per": 60, "days": 70, "t": "i"},
		# ── Jan 2026 (days_ago 35-69) ──
		{"prod": "PL-002", "amt": 900000,  "per": 18, "days": 65, "t": "i"},
		{"prod": "BL-001", "amt": 2800000, "per": 36, "days": 60, "t": "c"},
		{"prod": "HL-002", "amt": 9000000, "per": 240,"days": 55, "t": "i", "sec": True, "sy": "SEC-RP-001"},
		{"prod": "GL-001", "amt": 380000,  "per": 12, "days": 50, "t": "i"},
		{"prod": "VL-001", "amt": 2500000, "per": 48, "days": 45, "t": "i"},
		{"prod": "PL-001", "amt": 700000,  "per": 24, "days": 40, "t": "i"},
		{"prod": "LOC-001","amt": 2500000, "per": 12, "days": 38, "t": "c"},
		# ── Feb 2026 (days_ago 0-34) ──
		{"prod": "BL-001", "amt": 3800000, "per": 48, "days": 28, "t": "c"},
		{"prod": "EL-001", "amt": 1700000, "per": 60, "days": 22, "t": "i"},
		{"prod": "PL-001", "amt": 1100000, "per": 30, "days": 18, "t": "i"},
		{"prod": "VL-001", "amt": 3000000, "per": 60, "days": 14, "t": "i"},
		{"prod": "PL-002", "amt": 650000,  "per": 18, "days": 8,  "t": "i"},
		{"prod": "BL-001", "amt": 2200000, "per": 24, "days": 4,  "t": "c"},
		{"prod": "GL-001", "amt": 320000,  "per": 12, "days": 1,  "t": "i"},
	]

	created = []
	for i, cfg in enumerate(configs):
		email = f"batch2_app_{i+1:02d}@demo.com"

		# Check if already created
		existing = frappe.db.get_value("Loan Application", {"applicant_email_address": email}, "name")
		if existing:
			created.append({"name": existing, "date": str(add_days(today, -cfg["days"])), "cfg": cfg})
			print(f"  ⏭️  {email} → {existing}")
			continue

		first = random.choice(FIRST_NAMES)
		last = random.choice(LAST_NAMES)
		city, state, zipcode = random.choice(CITIES)
		posting_date = add_days(today, -cfg["days"])
		applicant = random.choice(ind) if cfg["t"] == "i" else random.choice(co)

		app_data = {
			"doctype": "Loan Application",
			"applicant_type": "Customer",
			"applicant": applicant,
			"company": COMPANY,
			"loan_product": cfg["prod"],
			"loan_amount": cfg["amt"],
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": cfg["per"],
			"is_secured_loan": 1 if cfg.get("sec") else 0,
			"posting_date": posting_date,
			"first_name": first,
			"last_name": last,
			"applicant_email_address": email,
			"applicant_phone_number": f"+91 9{random.randint(100000000, 999999999)}",
			"address_line_1": f"{random.randint(1,300)}, {random.choice(STREETS)}",
			"city": city,
			"state": state,
			"zip_code": zipcode,
			"description": f"Batch 2 — {cfg['prod']} loan",
		}

		if cfg.get("sec"):
			sec_price = frappe.db.get_value("Loan Security Price",
				{"loan_security": cfg["sy"]}, "loan_security_price") or 10000000
			app_data["proposed_pledges"] = [
				{"loan_security": cfg["sy"], "qty": 1, "loan_security_price": sec_price}
			]

		try:
			doc = frappe.get_doc(app_data)
			doc.insert(ignore_permissions=True)
			# Backdate creation
			frappe.db.set_value("Loan Application", doc.name, "creation",
				f"{posting_date} {9 + (i % 8)}:{random.randint(0,59):02d}:00", update_modified=False)
			created.append({"name": doc.name, "date": str(posting_date), "cfg": cfg})
			print(f"  ✅ {doc.name} — {first} {last} — ₹{cfg['amt']:,.0f} ({cfg['prod']}) on {posting_date}")
		except Exception as e:
			print(f"  ⚠️  {email}: {str(e)[:100]}")

	print(f"\n  Created/found: {len(created)} applications")
	return created


def process_lifecycle(today, app_list):
	"""Approve → Loan → Disburse for each application."""
	print("\n" + "=" * 60)
	print("🏦 STEP 2: Full Lifecycle (Approve → Loan → Disburse)")
	print("=" * 60)

	from lending.loan_management.doctype.loan_application.loan_application import create_loan

	loans_created = []

	for entry in app_list:
		app_name = entry["name"]
		app_date = getdate(entry["date"])
		cfg = entry["cfg"]

		status = frappe.db.get_value("Loan Application", app_name, ["docstatus", "status"], as_dict=True)
		if not status:
			continue

		# A) Submit & approve
		if status.docstatus == 0:
			try:
				doc = frappe.get_doc("Loan Application", app_name)
				doc.submit()
				frappe.db.set_value("Loan Application", app_name, "status", "Approved")
			except Exception as e:
				print(f"  ⚠️  Approve {app_name}: {str(e)[:80]}")
				continue
		elif status.status != "Approved":
			frappe.db.set_value("Loan Application", app_name, "status", "Approved")

		# B) Check if loan already exists
		existing_loan = frappe.db.get_value("Loan", {"loan_application": app_name}, "name")
		if existing_loan:
			loans_created.append({"name": existing_loan, "date": entry["date"], "cfg": cfg})
			print(f"  ⏭️  {existing_loan} (from {app_name})")
			continue

		# C) Create loan
		try:
			loan_date = add_days(app_date, random.randint(2, 6))
			if getdate(loan_date) > getdate(today):
				loan_date = today

			loan_doc = create_loan(app_name)
			loan_doc.posting_date = loan_date
			loan_doc.insert(ignore_permissions=True)
			frappe.db.set_value("Loan", loan_doc.name, "creation",
				f"{loan_date} {10 + random.randint(0,5)}:{random.randint(0,59):02d}:00", update_modified=False)
			loan_doc.reload()
			loan_doc.submit()

			# D) Security assignment for secured
			if cfg.get("sec"):
				try:
					from lending.loan_management.doctype.loan_application.loan_application import create_loan_security_assignment
					create_loan_security_assignment(loan_application=app_name, loan=loan_doc.name)
				except Exception:
					pass

			# E) Disburse
			disb_date = add_days(loan_date, random.randint(1, 4))
			if getdate(disb_date) > getdate(today):
				disb_date = today

			try:
				disb = frappe.new_doc("Loan Disbursement")
				disb.against_loan = loan_doc.name
				disb.company = COMPANY
				disb.applicant_type = loan_doc.applicant_type
				disb.applicant = loan_doc.applicant
				disb.posting_date = disb_date
				disb.disbursement_date = disb_date
				disb.disbursed_amount = cfg["amt"]

				payment_account = frappe.db.get_value("Loan Product", cfg["prod"], "payment_account")
				loan_account = frappe.db.get_value("Loan Product", cfg["prod"], "loan_account")
				if payment_account:
					disb.payment_account = payment_account
				if loan_account:
					disb.loan_account = loan_account

				disb.insert(ignore_permissions=True)
				disb.submit()
				frappe.db.set_value("Loan Disbursement", disb.name, "creation",
					f"{disb_date} 14:{random.randint(0,59):02d}:00", update_modified=False)

				print(f"  ✅ {loan_doc.name} → {disb.name} — ₹{cfg['amt']:,.0f} on {disb_date}")
			except Exception as e:
				print(f"  ⚠️  Disb {loan_doc.name}: {str(e)[:80]}")

			loans_created.append({"name": loan_doc.name, "date": str(loan_date), "cfg": cfg})
		except Exception as e:
			print(f"  ⚠️  Loan {app_name}: {str(e)[:100]}")

	print(f"\n  Processed: {len(loans_created)} loans")
	return loans_created


def create_bulk_repayments(today):
	"""Create repayments for all disbursed loans that don't have any."""
	print("\n" + "=" * 60)
	print("💰 STEP 3: Bulk Repayments")
	print("=" * 60)

	loans = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]], "is_term_loan": 1},
		fields=["name", "loan_amount", "applicant_type", "applicant", "company", "posting_date"],
		order_by="posting_date asc",
	)

	count = 0
	for loan in loans:
		existing = frappe.db.count("Loan Repayment", {"against_loan": loan.name, "docstatus": 1})
		if existing >= 1:
			continue

		loan_date = getdate(loan.posting_date)
		repay_date = add_days(loan_date, 30)
		if getdate(repay_date) > getdate(today):
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
			count += 1
			print(f"  ✅ {rep.name} for {loan.name} — ₹{emi:,.0f} on {repay_date}")
		except Exception as e:
			print(f"  ⚠️  {loan.name}: {str(e)[:80]}")

	print(f"\n  Created {count} repayments")


def run_mass_interest_accruals(today):
	"""Run interest accrual for multiple dates across 4 months to fill the accrual chart."""
	print("\n" + "=" * 60)
	print("📈 STEP 4: Mass Interest Accruals (every 15 days for 4 months)")
	print("=" * 60)

	from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import (
		process_loan_interest_accrual_for_loans,
	)

	# Run accruals at ~15-day intervals going back 4 months
	accrual_dates = []
	for months_back in range(4, -1, -1):
		base = add_months(today, -months_back)
		for day_offset in [1, 15]:
			try:
				d = getdate(f"{base.year}-{base.month:02d}-{day_offset:02d}")
				if d <= today:
					accrual_dates.append(d)
			except Exception:
				pass

	# Also add the last day of each month
	for months_back in range(4, 0, -1):
		base = add_months(today, -months_back)
		try:
			import calendar
			last_day = calendar.monthrange(base.year, base.month)[1]
			d = getdate(f"{base.year}-{base.month:02d}-{last_day:02d}")
			if d <= today:
				accrual_dates.append(d)
		except Exception:
			pass

	# Remove duplicates and sort
	accrual_dates = sorted(set(accrual_dates))
	print(f"  Running accruals for {len(accrual_dates)} dates:")
	for d in accrual_dates:
		print(f"    {d}")

	for accrual_date in accrual_dates:
		try:
			result = process_loan_interest_accrual_for_loans(
				posting_date=str(accrual_date),
				company=COMPANY,
			)
			new_accruals = frappe.db.count("Loan Interest Accrual",
				{"process_loan_interest_accrual": result, "docstatus": 1})
			if new_accruals > 0:
				print(f"  ✅ {accrual_date}: {new_accruals} accruals")
			else:
				print(f"  ⏭️  {accrual_date}: 0 new accruals (already done or no eligible loans)")
		except Exception as e:
			print(f"  ⚠️  {accrual_date}: {str(e)[:80]}")

	total_accruals = frappe.db.count("Loan Interest Accrual", {"docstatus": 1})
	print(f"\n  Total interest accruals now: {total_accruals}")


def add_extra_shortfalls_writeoffs(today):
	"""Add more shortfalls for secured loans and extra write-offs."""
	print("\n" + "=" * 60)
	print("⚠️ / 📝 STEP 5: Extra Shortfalls & Write-offs")
	print("=" * 60)

	# Shortfalls for all secured disbursed loans without one
	secured = frappe.get_all(
		"Loan",
		filters={"docstatus": 1, "is_secured_loan": 1, "status": ["in", ["Disbursed", "Active"]]},
		fields=["name", "loan_amount", "applicant_type", "applicant"],
	)
	sf_count = 0
	for loan in secured:
		if frappe.db.exists("Loan Security Shortfall", {"loan": loan.name}):
			sf_count += 1
			continue
		shortfall_pct = random.uniform(0.10, 0.25)
		sf = frappe.new_doc("Loan Security Shortfall")
		sf.loan = loan.name
		sf.applicant_type = loan.applicant_type
		sf.applicant = loan.applicant
		sf.loan_amount = loan.loan_amount
		sf.security_value = flt(loan.loan_amount * (1 - shortfall_pct))
		sf.shortfall_amount = flt(loan.loan_amount * shortfall_pct)
		sf.shortfall_percentage = shortfall_pct * 100
		sf.shortfall_time = now_datetime()
		sf.status = "Pending"
		sf.save(ignore_permissions=True)
		sf_count += 1
		print(f"  ✅ Shortfall: {loan.name} — ₹{sf.shortfall_amount:,.0f}")
	print(f"  Total shortfalls: {sf_count}")

	# Write-offs
	wo_count = frappe.db.count("Loan Write Off", {"docstatus": 1})
	if wo_count < 3:
		write_off_account = f"Write Off - {ABBR}"
		wo_loans = frappe.get_all(
			"Loan",
			filters={"docstatus": 1, "status": ["in", ["Disbursed", "Active"]]},
			fields=["name", "loan_amount", "company", "loan_product"],
			order_by="loan_amount asc",
			limit=5,
		)
		for loan in wo_loans[wo_count:3]:
			wo_date = add_days(today, -random.randint(5, 45))
			wo_amt = flt(loan.loan_amount * 0.025)
			try:
				wname = f"LM-WO-B2-{loan.name[-3:]}"
				if not frappe.db.exists("Loan Write Off", wname):
					frappe.db.sql("""
						INSERT INTO `tabLoan Write Off`
						(name, loan, posting_date, write_off_amount, write_off_account,
						docstatus, company, loan_product, owner, modified_by, creation, modified)
						VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 'Administrator', 'Administrator', %s, %s)
					""", (wname, loan.name, wo_date, wo_amt, write_off_account,
						COMPANY, loan.loan_product, f"{wo_date} 15:00:00", f"{wo_date} 15:00:00"))
					print(f"  ✅ Write-off: {wname} — ₹{wo_amt:,.0f} on {wo_date}")
			except Exception as e:
				print(f"  ⚠️  WO: {str(e)[:80]}")


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


def print_final_summary():
	today = nowdate()
	print("\n" + "=" * 60)
	print("📊 FINAL DASHBOARD — DOUBLED DATA")
	print("=" * 60)

	cards = [
		("NEW LOANS",                frappe.db.count("Loan", {"docstatus": 1, "creation": [">=", today]})),
		("ACTIVE LOANS",             frappe.db.count("Loan", {"docstatus": 1, "status": ["in", ["Disbursed", "Partially Disbursed"]]})),
		("CLOSED LOANS",             frappe.db.count("Loan", {"docstatus": 1, "status": "Closed"})),
		("TOTAL DISBURSED",          frappe.db.sql("SELECT COALESCE(SUM(disbursed_amount),0) FROM `tabLoan Disbursement` WHERE docstatus=1")[0][0]),
		("OPEN LOAN APPLICATIONS",   frappe.db.count("Loan Application", {"docstatus": 1, "status": "Open"})),
		("NEW LOAN APPLICATIONS",    frappe.db.count("Loan Application", {"docstatus": 1, "creation": [">=", today]})),
		("TOTAL SANCTIONED AMOUNT",  frappe.db.sql("SELECT COALESCE(SUM(loan_amount),0) FROM `tabLoan` WHERE docstatus=1 AND status='Sanctioned'")[0][0]),
		("ACTIVE SECURITIES",        frappe.db.count("Loan Security", {"disabled": 0})),
		("APPLICANTS W/ SHORTFALL",  frappe.db.count("Loan Security Shortfall", {"status": "Pending"})),
		("TOTAL SHORTFALL AMOUNT",   frappe.db.sql("SELECT COALESCE(SUM(shortfall_amount),0) FROM `tabLoan Security Shortfall`")[0][0]),
		("TOTAL REPAYMENT",          frappe.db.sql("SELECT COALESCE(SUM(amount_paid),0) FROM `tabLoan Repayment` WHERE docstatus=1")[0][0]),
		("TOTAL WRITE OFF",          frappe.db.sql("SELECT COALESCE(SUM(write_off_amount),0) FROM `tabLoan Write Off` WHERE docstatus=1")[0][0]),
	]

	for label, value in cards:
		if isinstance(value, float):
			print(f"  {label:40s}: ₹{value:>15,.0f}")
		else:
			print(f"  {label:40s}: {value:>15}")

	print(f"\n  --- Grand Totals ---")
	for dt in ["Loan", "Loan Application", "Loan Disbursement", "Loan Repayment", "Loan Interest Accrual", "Loan Write Off", "Loan Security Shortfall"]:
		c = frappe.db.count(dt, {"docstatus": 1}) if dt != "Loan Security Shortfall" else frappe.db.count(dt)
		print(f"  {dt:40s}: {c:>10}")
	print("=" * 60)
	print("\n🎯 Refresh: /app/dashboard-view/Loan Dashboard")
