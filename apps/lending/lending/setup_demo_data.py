"""
Demo Data Setup Script for Lending Management System (LMS) & Loan Origination System (LOS)

Run this script using:
    bench execute lending.setup_demo_data.setup_demo_data

This will populate the system with realistic sample data for demo purposes.
The script is idempotent — it will skip records that already exist.
"""

import frappe
from frappe.utils import nowdate, add_days, add_months, getdate, now_datetime, add_to_date


def setup_demo_data():
	"""Main entry point — sets up all demo data."""
	frappe.flags.ignore_permissions = True

	company = get_or_create_company()
	create_loan_categories()
	create_loan_classifications()
	create_loan_security_types()
	create_loan_securities()
	create_loan_security_prices()
	create_loan_document_types()
	create_loan_demand_offset_orders()
	create_loan_products(company)
	customers = create_customers()
	create_loan_applications(company, customers)

	frappe.db.commit()
	frappe.flags.ignore_permissions = False
	print("\n✅ Demo data setup complete!")
	print_summary()


# =============================================================================
# Company
# =============================================================================

def get_or_create_company():
	"""Get the first existing company or create a demo company."""
	company = frappe.db.get_value("Company", filters={"is_group": 0}, fieldname="name")
	if company:
		print(f"  Using existing company: {company}")
		return company

	# If no company exists, create one
	company_name = "Aonami Finance Ltd"
	if not frappe.db.exists("Company", company_name):
		doc = frappe.get_doc({
			"doctype": "Company",
			"company_name": company_name,
			"default_currency": "INR",
			"country": "India",
			"chart_of_accounts": "Standard",
		})
		doc.insert(ignore_permissions=True)
		print(f"  ✅ Created company: {company_name}")
	return company_name


# =============================================================================
# Loan Categories (LMS)
# =============================================================================

LOAN_CATEGORIES = [
	{"loan_category_code": "TERM-UNSEC", "loan_category_name": "Term Loan - Unsecured"},
	{"loan_category_code": "TERM-SEC", "loan_category_name": "Term Loan - Secured"},
	{"loan_category_code": "DEMAND", "loan_category_name": "Demand Loan"},
	{"loan_category_code": "LOC", "loan_category_name": "Line of Credit"},
	{"loan_category_code": "LAP", "loan_category_name": "Loan Against Property"},
	{"loan_category_code": "GOLD", "loan_category_name": "Gold Loan"},
	{"loan_category_code": "VEH", "loan_category_name": "Vehicle Loan"},
	{"loan_category_code": "EDU", "loan_category_name": "Education Loan"},
]


def create_loan_categories():
	print("\n📁 Loan Categories")
	for cat in LOAN_CATEGORIES:
		if not frappe.db.exists("Loan Category", cat["loan_category_code"]):
			doc = frappe.get_doc({"doctype": "Loan Category", **cat})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {cat['loan_category_code']} — {cat['loan_category_name']}")
		else:
			print(f"  ⏭️  {cat['loan_category_code']} already exists")


# =============================================================================
# Loan Classifications (LMS)
# =============================================================================

LOAN_CLASSIFICATIONS = [
	{"classification_code": "STD", "classification_name": "Standard"},
	{"classification_code": "SMA-0", "classification_name": "Special Mention Account - 0"},
	{"classification_code": "SMA-1", "classification_name": "Special Mention Account - 1"},
	{"classification_code": "SMA-2", "classification_name": "Special Mention Account - 2"},
	{"classification_code": "SUB", "classification_name": "Sub-Standard"},
	{"classification_code": "DBT", "classification_name": "Doubtful"},
	{"classification_code": "LOSS", "classification_name": "Loss"},
]


def create_loan_classifications():
	print("\n🏷️  Loan Classifications")
	for cls in LOAN_CLASSIFICATIONS:
		if not frappe.db.exists("Loan Classification", cls["classification_code"]):
			doc = frappe.get_doc({"doctype": "Loan Classification", **cls})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {cls['classification_code']} — {cls['classification_name']}")
		else:
			print(f"  ⏭️  {cls['classification_code']} already exists")


# =============================================================================
# Loan Security Types (LMS)
# =============================================================================

LOAN_SECURITY_TYPES = [
	{"loan_security_type": "Residential Property", "haircut": 30, "loan_to_value_ratio": 70},
	{"loan_security_type": "Commercial Property", "haircut": 40, "loan_to_value_ratio": 60},
	{"loan_security_type": "Gold Jewelry", "haircut": 25, "loan_to_value_ratio": 75},
	{"loan_security_type": "Fixed Deposit", "haircut": 10, "loan_to_value_ratio": 90},
	{"loan_security_type": "Mutual Fund Units", "haircut": 50, "loan_to_value_ratio": 50},
	{"loan_security_type": "Listed Equity Shares", "haircut": 50, "loan_to_value_ratio": 50},
	{"loan_security_type": "Government Securities", "haircut": 15, "loan_to_value_ratio": 85},
	{"loan_security_type": "Motor Vehicle", "haircut": 35, "loan_to_value_ratio": 65},
]


def create_loan_security_types():
	print("\n🔒 Loan Security Types")
	for st in LOAN_SECURITY_TYPES:
		if not frappe.db.exists("Loan Security Type", st["loan_security_type"]):
			doc = frappe.get_doc({"doctype": "Loan Security Type", **st})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {st['loan_security_type']} (Haircut: {st['haircut']}%, LTV: {st['loan_to_value_ratio']}%)")
		else:
			print(f"  ⏭️  {st['loan_security_type']} already exists")


# =============================================================================
# Loan Securities (LMS)
# =============================================================================

LOAN_SECURITIES = [
	{
		"loan_security_code": "SEC-RP-001",
		"loan_security_name": "3BHK Flat - Andheri West, Mumbai",
		"loan_security_type": "Residential Property",
		"original_security_value": 12500000,
	},
	{
		"loan_security_code": "SEC-RP-002",
		"loan_security_name": "2BHK Apartment - Whitefield, Bangalore",
		"loan_security_type": "Residential Property",
		"original_security_value": 8500000,
	},
	{
		"loan_security_code": "SEC-CP-001",
		"loan_security_name": "Office Space - BKC, Mumbai",
		"loan_security_type": "Commercial Property",
		"original_security_value": 35000000,
	},
	{
		"loan_security_code": "SEC-GJ-001",
		"loan_security_name": "Gold Necklace & Bangles - 120g 22K",
		"loan_security_type": "Gold Jewelry",
		"original_security_value": 720000,
	},
	{
		"loan_security_code": "SEC-GJ-002",
		"loan_security_name": "Gold Chain & Pendant - 80g 22K",
		"loan_security_type": "Gold Jewelry",
		"original_security_value": 480000,
	},
	{
		"loan_security_code": "SEC-FD-001",
		"loan_security_name": "SBI Fixed Deposit - 5 Year",
		"loan_security_type": "Fixed Deposit",
		"original_security_value": 2000000,
	},
	{
		"loan_security_code": "SEC-MF-001",
		"loan_security_name": "HDFC Balanced Advantage Fund - 50,000 Units",
		"loan_security_type": "Mutual Fund Units",
		"original_security_value": 1500000,
	},
	{
		"loan_security_code": "SEC-EQ-001",
		"loan_security_name": "Reliance Industries Ltd - 5,000 Shares",
		"loan_security_type": "Listed Equity Shares",
		"original_security_value": 6250000,
	},
	{
		"loan_security_code": "SEC-GS-001",
		"loan_security_name": "GOI 7.26% 2033 Bond",
		"loan_security_type": "Government Securities",
		"original_security_value": 5000000,
	},
	{
		"loan_security_code": "SEC-MV-001",
		"loan_security_name": "Toyota Fortuner 2024 Model",
		"loan_security_type": "Motor Vehicle",
		"original_security_value": 4500000,
	},
]


def create_loan_securities():
	print("\n🏦 Loan Securities")
	for sec in LOAN_SECURITIES:
		if not frappe.db.exists("Loan Security", sec["loan_security_code"]):
			doc = frappe.get_doc({"doctype": "Loan Security", **sec})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {sec['loan_security_code']} — {sec['loan_security_name']}")
		else:
			print(f"  ⏭️  {sec['loan_security_code']} already exists")


# =============================================================================
# Loan Security Prices (LMS)
# =============================================================================

def create_loan_security_prices():
	print("\n💰 Loan Security Prices")
	today = now_datetime()
	valid_upto = add_to_date(today, months=12)

	prices = [
		("SEC-RP-001", 13000000),
		("SEC-RP-002", 8800000),
		("SEC-CP-001", 36000000),
		("SEC-GJ-001", 750000),
		("SEC-GJ-002", 500000),
		("SEC-FD-001", 2100000),
		("SEC-MF-001", 1600000),
		("SEC-EQ-001", 6500000),
		("SEC-GS-001", 5100000),
		("SEC-MV-001", 4200000),
	]

	for security_code, price in prices:
		if not frappe.db.exists("Loan Security", security_code):
			print(f"  ⚠️  Security {security_code} not found, skipping price")
			continue

		existing = frappe.db.exists("Loan Security Price", {
			"loan_security": security_code,
			"valid_from": ("<=", today),
			"valid_upto": (">=", today),
		})
		if not existing:
			doc = frappe.get_doc({
				"doctype": "Loan Security Price",
				"loan_security": security_code,
				"loan_security_price": price,
				"valid_from": today,
				"valid_upto": valid_upto,
			})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {security_code} → ₹{price:,.0f}")
		else:
			print(f"  ⏭️  Price for {security_code} already exists")


# =============================================================================
# Loan Document Types (LOS)
# =============================================================================

LOAN_DOCUMENT_TYPES = [
	"PAN Card",
	"Aadhaar Card",
	"Voter ID",
	"Passport",
	"Driving License",
	"Bank Statement (6 months)",
	"Salary Slip (3 months)",
	"Income Tax Returns (2 years)",
	"Property Valuation Report",
	"Property Title Deed",
	"Encumbrance Certificate",
	"Vehicle Registration Certificate",
	"Gold Purity Certificate",
	"Business Registration Certificate",
	"GST Returns",
	"Balance Sheet & P&L (2 years)",
	"Photograph",
	"Address Proof",
	"Employment Letter",
	"NOC from Builder/Society",
]


def create_loan_document_types():
	print("\n📄 Loan Document Types (LOS)")
	for doc_type in LOAN_DOCUMENT_TYPES:
		if not frappe.db.exists("Loan Document Type", doc_type):
			doc = frappe.get_doc({
				"doctype": "Loan Document Type",
				"loan_document_type": doc_type,
			})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {doc_type}")
		else:
			print(f"  ⏭️  {doc_type} already exists")


# =============================================================================
# Loan Demand Offset Orders (LMS)
# =============================================================================

LOAN_DEMAND_OFFSET_ORDERS = [
	{
		"title": "Standard Asset Collection Sequence",
		"components": [
			{"demand_type": "Charges"},
			{"demand_type": "Penalty"},
			{"demand_type": "Interest"},
			{"demand_type": "Principal"},
		],
	},
	{
		"title": "Sub Standard Asset Collection Sequence",
		"components": [
			{"demand_type": "Charges"},
			{"demand_type": "Penalty"},
			{"demand_type": "Interest"},
			{"demand_type": "Principal"},
		],
	},
	{
		"title": "Written Off Asset Collection Sequence",
		"components": [
			{"demand_type": "Penalty"},
			{"demand_type": "Charges"},
			{"demand_type": "Interest"},
			{"demand_type": "Principal"},
		],
	},
	{
		"title": "Settlement Collection Sequence",
		"components": [
			{"demand_type": "Principal"},
			{"demand_type": "Interest"},
			{"demand_type": "Penalty"},
			{"demand_type": "Charges"},
		],
	},
]


def create_loan_demand_offset_orders():
	print("\n📊 Loan Demand Offset Orders")
	for order in LOAN_DEMAND_OFFSET_ORDERS:
		if not frappe.db.exists("Loan Demand Offset Order", order["title"]):
			doc = frappe.get_doc({
				"doctype": "Loan Demand Offset Order",
				"title": order["title"],
				"components": order["components"],
			})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {order['title']}")
		else:
			print(f"  ⏭️  {order['title']} already exists")


# =============================================================================
# Loan Products (LMS)
# =============================================================================

def create_loan_products(company):
	print("\n📦 Loan Products")

	# Get offset order references
	std_offset = "Standard Asset Collection Sequence"
	sub_std_offset = "Sub Standard Asset Collection Sequence"
	written_off_offset = "Written Off Asset Collection Sequence"
	settlement_offset = "Settlement Collection Sequence"

	# Common offset sequence fields for all products
	offset_fields = {
		"collection_offset_sequence_for_standard_asset": std_offset,
		"collection_offset_sequence_for_sub_standard_asset": sub_std_offset,
		"collection_offset_sequence_for_written_off_asset": written_off_offset,
		"collection_offset_sequence_for_settlement_collection": settlement_offset,
	}

	products = [
		{
			"product_code": "PL-001",
			"product_name": "Personal Loan - Salaried",
			"company": company,
			"rate_of_interest": 12.5,
			"penalty_interest_rate": 2.0,
			"maximum_loan_amount": 2500000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per repayment start date",
			"grace_period_in_days": 5,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "TERM-UNSEC",
			"write_off_amount": 100,
		},
		{
			"product_code": "PL-002",
			"product_name": "Personal Loan - Self Employed",
			"company": company,
			"rate_of_interest": 14.0,
			"penalty_interest_rate": 2.5,
			"maximum_loan_amount": 2000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per repayment start date",
			"grace_period_in_days": 5,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "TERM-UNSEC",
			"write_off_amount": 100,
		},
		{
			"product_code": "HL-001",
			"product_name": "Home Loan - Fixed Rate",
			"company": company,
			"rate_of_interest": 8.5,
			"penalty_interest_rate": 1.5,
			"maximum_loan_amount": 50000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per cycle date",
			"cyclic_day_of_the_month": 5,
			"grace_period_in_days": 7,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "TERM-SEC",
			"write_off_amount": 500,
		},
		{
			"product_code": "HL-002",
			"product_name": "Home Loan - Floating Rate",
			"company": company,
			"rate_of_interest": 8.75,
			"penalty_interest_rate": 1.5,
			"maximum_loan_amount": 75000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Pro-rated calendar months",
			"repayment_date_on": "Start of the next month",
			"grace_period_in_days": 7,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "TERM-SEC",
			"write_off_amount": 500,
		},
		{
			"product_code": "LAP-001",
			"product_name": "Loan Against Property",
			"company": company,
			"rate_of_interest": 10.5,
			"penalty_interest_rate": 2.0,
			"maximum_loan_amount": 30000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per repayment start date",
			"grace_period_in_days": 5,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "LAP",
			"write_off_amount": 200,
		},
		{
			"product_code": "GL-001",
			"product_name": "Gold Loan",
			"company": company,
			"rate_of_interest": 9.0,
			"penalty_interest_rate": 1.0,
			"maximum_loan_amount": 5000000,
			"is_term_loan": 0,
			"grace_period_in_days": 3,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "GOLD",
			"write_off_amount": 50,
		},
		{
			"product_code": "VL-001",
			"product_name": "Vehicle Loan - New Car",
			"company": company,
			"rate_of_interest": 9.5,
			"penalty_interest_rate": 2.0,
			"maximum_loan_amount": 10000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per cycle date",
			"cyclic_day_of_the_month": 10,
			"grace_period_in_days": 5,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "VEH",
			"write_off_amount": 100,
		},
		{
			"product_code": "BL-001",
			"product_name": "Business Loan - MSME",
			"company": company,
			"rate_of_interest": 15.0,
			"penalty_interest_rate": 3.0,
			"maximum_loan_amount": 10000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per repayment start date",
			"grace_period_in_days": 7,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "TERM-UNSEC",
			"write_off_amount": 200,
		},
		{
			"product_code": "LOC-001",
			"product_name": "Line of Credit - Business",
			"company": company,
			"rate_of_interest": 16.0,
			"penalty_interest_rate": 3.0,
			"maximum_loan_amount": 5000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Line of Credit",
			"grace_period_in_days": 3,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "LOC",
			"write_off_amount": 100,
		},
		{
			"product_code": "EL-001",
			"product_name": "Education Loan",
			"company": company,
			"rate_of_interest": 10.0,
			"penalty_interest_rate": 1.0,
			"maximum_loan_amount": 5000000,
			"is_term_loan": 1,
			"repayment_schedule_type": "Monthly as per repayment start date",
			"grace_period_in_days": 15,
			"days_past_due_threshold_for_npa": 90,
			"loan_category": "EDU",
			"write_off_amount": 100,
		},
	]

	for prod in products:
		if not frappe.db.exists("Loan Product", prod["product_code"]):
			prod.update(offset_fields)
			doc = frappe.get_doc({"doctype": "Loan Product", **prod})
			doc.insert(ignore_permissions=True)
			print(f"  ✅ {prod['product_code']} — {prod['product_name']} (Rate: {prod['rate_of_interest']}%)")
		else:
			print(f"  ⏭️  {prod['product_code']} already exists")


# =============================================================================
# Customers
# =============================================================================

CUSTOMER_DATA = [
	{
		"customer_name": "Rajesh Kumar Sharma",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "India",
		"email_id": "rajesh.sharma@demo.com",
		"mobile_no": "9876543210",
	},
	{
		"customer_name": "Priya Mehta",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "India",
		"email_id": "priya.mehta@demo.com",
		"mobile_no": "9876543211",
	},
	{
		"customer_name": "Amit Patel Industries",
		"customer_type": "Company",
		"customer_group": "Commercial",
		"territory": "India",
		"email_id": "amit.patel@demo.com",
		"mobile_no": "9876543212",
	},
	{
		"customer_name": "Sunita Reddy",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "India",
		"email_id": "sunita.reddy@demo.com",
		"mobile_no": "9876543213",
	},
	{
		"customer_name": "Vikram Singh Trading Co.",
		"customer_type": "Company",
		"customer_group": "Commercial",
		"territory": "India",
		"email_id": "vikram.singh@demo.com",
		"mobile_no": "9876543214",
	},
	{
		"customer_name": "Deepa Krishnan",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "India",
		"email_id": "deepa.krishnan@demo.com",
		"mobile_no": "9876543215",
	},
	{
		"customer_name": "GreenTech Solutions Pvt Ltd",
		"customer_type": "Company",
		"customer_group": "Commercial",
		"territory": "India",
		"email_id": "contact@greentech.demo.com",
		"mobile_no": "9876543216",
	},
	{
		"customer_name": "Mohd. Farhan Khan",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "India",
		"email_id": "farhan.khan@demo.com",
		"mobile_no": "9876543217",
	},
	{
		"customer_name": "Ananya Iyer",
		"customer_type": "Individual",
		"customer_group": "Individual",
		"territory": "India",
		"email_id": "ananya.iyer@demo.com",
		"mobile_no": "9876543218",
	},
	{
		"customer_name": "Bharat Manufacturing Ltd",
		"customer_type": "Company",
		"customer_group": "Commercial",
		"territory": "India",
		"email_id": "finance@bharatmfg.demo.com",
		"mobile_no": "9876543219",
	},
]


def create_customers():
	print("\n👥 Customers")
	customer_names = []

	# Make sure customer groups exist
	for group in ["Individual", "Commercial"]:
		if not frappe.db.exists("Customer Group", group):
			try:
				doc = frappe.get_doc({
					"doctype": "Customer Group",
					"customer_group_name": group,
				})
				doc.insert(ignore_permissions=True)
				print(f"  ✅ Customer Group: {group}")
			except Exception:
				pass  # May already exist under different parent

	for cust in CUSTOMER_DATA:
		if not frappe.db.exists("Customer", {"customer_name": cust["customer_name"]}):
			doc = frappe.get_doc({"doctype": "Customer", **cust})
			try:
				doc.insert(ignore_permissions=True)
				print(f"  ✅ {cust['customer_name']} ({cust['customer_type']})")
			except Exception as e:
				print(f"  ⚠️  Could not create {cust['customer_name']}: {str(e)[:80]}")
				# Try to find existing customer
				existing = frappe.db.get_value("Customer", {"customer_name": cust["customer_name"]}, "name")
				if existing:
					customer_names.append(existing)
				continue
		else:
			print(f"  ⏭️  {cust['customer_name']} already exists")

		name = frappe.db.get_value("Customer", {"customer_name": cust["customer_name"]}, "name")
		if name:
			customer_names.append(name)

	return customer_names


# =============================================================================
# Loan Applications (LOS + LMS)
# =============================================================================

def create_loan_applications(company, customers):
	print("\n📋 Loan Applications")

	if not customers:
		print("  ⚠️  No customers available. Skipping loan applications.")
		return

	today = getdate(nowdate())

	applications = [
		# Personal Loans
		{
			"applicant": customers[0] if len(customers) > 0 else None,
			"loan_product": "PL-001",
			"loan_amount": 1500000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 36,
			"description": "Personal Loan for home renovation and furniture purchase",
			"first_name": "Rajesh",
			"last_name": "Sharma",
			"applicant_email_address": "rajesh.sharma@demo.com",
			"applicant_phone_number": "+91 9876543210",
			"address_line_1": "42, MG Road, Andheri West",
			"city": "Mumbai",
			"state": "Maharashtra",
			"zip_code": 400058,
			"posting_date": add_days(today, -30),
		},
		{
			"applicant": customers[1] if len(customers) > 1 else customers[0],
			"loan_product": "PL-001",
			"loan_amount": 800000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 24,
			"description": "Personal Loan for wedding expenses",
			"first_name": "Priya",
			"last_name": "Mehta",
			"applicant_email_address": "priya.mehta@demo.com",
			"applicant_phone_number": "+91 9876543211",
			"address_line_1": "15, Park Street, Colaba",
			"city": "Mumbai",
			"state": "Maharashtra",
			"zip_code": 400001,
			"posting_date": add_days(today, -25),
		},
		# Home Loan
		{
			"applicant": customers[3] if len(customers) > 3 else customers[0],
			"loan_product": "HL-001",
			"loan_amount": 5000000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 240,
			"is_secured_loan": 1,
			"proposed_pledges": [
				{"loan_security": "SEC-RP-002", "qty": 1, "loan_security_price": 8800000}
			],
			"description": "Home Loan for purchasing 2BHK flat in Electronic City",
			"first_name": "Sunita",
			"last_name": "Reddy",
			"applicant_email_address": "sunita.reddy@demo.com",
			"applicant_phone_number": "+91 9876543213",
			"address_line_1": "78, Vidyanagar, Electronic City Phase 1",
			"city": "Bangalore",
			"state": "Karnataka",
			"zip_code": 560100,
			"posting_date": add_days(today, -45),
		},
		# Loan Against Property
		{
			"applicant": customers[2] if len(customers) > 2 else customers[0],
			"loan_product": "LAP-001",
			"loan_amount": 8000000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 120,
			"is_secured_loan": 1,
			"proposed_pledges": [
				{"loan_security": "SEC-CP-001", "qty": 1, "loan_security_price": 36000000}
			],
			"description": "Loan Against Property for business expansion - new warehouse",
			"first_name": "Amit",
			"last_name": "Patel",
			"applicant_email_address": "amit.patel@demo.com",
			"applicant_phone_number": "+91 9876543212",
			"address_line_1": "MIDC Industrial Area, Ambernath",
			"city": "Thane",
			"state": "Maharashtra",
			"zip_code": 421501,
			"posting_date": add_days(today, -20),
		},
		# Gold Loan
		{
			"applicant": customers[5] if len(customers) > 5 else customers[0],
			"loan_product": "GL-001",
			"loan_amount": 400000,
			"description": "Gold Loan for agricultural expenses",
			"first_name": "Deepa",
			"last_name": "Krishnan",
			"applicant_email_address": "deepa.krishnan@demo.com",
			"applicant_phone_number": "+91 9876543215",
			"address_line_1": "23, Temple Road, Thrissur",
			"city": "Thrissur",
			"state": "Kerala",
			"zip_code": 680001,
			"posting_date": add_days(today, -15),
		},
		# Vehicle Loan
		{
			"applicant": customers[7] if len(customers) > 7 else customers[0],
			"loan_product": "VL-001",
			"loan_amount": 3500000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 60,
			"description": "Vehicle Loan for purchasing Toyota Fortuner",
			"first_name": "Farhan",
			"last_name": "Khan",
			"applicant_email_address": "farhan.khan@demo.com",
			"applicant_phone_number": "+91 9876543217",
			"address_line_1": "56, Civil Lines, Lucknow",
			"city": "Lucknow",
			"state": "Uttar Pradesh",
			"zip_code": 226001,
			"posting_date": add_days(today, -10),
		},
		# Business Loan
		{
			"applicant": customers[4] if len(customers) > 4 else customers[0],
			"loan_product": "BL-001",
			"loan_amount": 5000000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 48,
			"description": "Business Loan for inventory procurement and working capital",
			"first_name": "Vikram",
			"last_name": "Singh",
			"applicant_email_address": "vikram.singh@demo.com",
			"applicant_phone_number": "+91 9876543214",
			"address_line_1": "Industrial Estate, Rajpura",
			"city": "Patiala",
			"state": "Punjab",
			"zip_code": 147001,
			"posting_date": add_days(today, -12),
		},
		# Education Loan
		{
			"applicant": customers[8] if len(customers) > 8 else customers[0],
			"loan_product": "EL-001",
			"loan_amount": 2500000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 84,
			"description": "Education Loan for MS in Computer Science at Stanford University",
			"first_name": "Ananya",
			"last_name": "Iyer",
			"applicant_email_address": "ananya.iyer@demo.com",
			"applicant_phone_number": "+91 9876543218",
			"address_line_1": "12, Boat Club Road, T. Nagar",
			"city": "Chennai",
			"state": "Tamil Nadu",
			"zip_code": 600017,
			"posting_date": add_days(today, -8),
		},
		# Line of Credit
		{
			"applicant": customers[6] if len(customers) > 6 else customers[0],
			"loan_product": "LOC-001",
			"loan_amount": 3000000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 12,
			"description": "Line of Credit for seasonal working capital needs",
			"first_name": "GreenTech",
			"last_name": "Solutions",
			"applicant_email_address": "contact@greentech.demo.com",
			"applicant_phone_number": "+91 9876543216",
			"address_line_1": "IT Park, Hinjewadi Phase 2",
			"city": "Pune",
			"state": "Maharashtra",
			"zip_code": 411057,
			"posting_date": add_days(today, -5),
		},
		# Home Loan - another
		{
			"applicant": customers[9] if len(customers) > 9 else customers[0],
			"loan_product": "HL-002",
			"loan_amount": 8000000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 240,
			"is_secured_loan": 1,
			"proposed_pledges": [
				{"loan_security": "SEC-RP-001", "qty": 1, "loan_security_price": 13000000},
			],
			"description": "Home Loan for purchasing 3BHK villa in Gachibowli",
			"first_name": "Bharat",
			"last_name": "Manufacturing",
			"applicant_email_address": "finance@bharatmfg.demo.com",
			"applicant_phone_number": "+91 9876543219",
			"address_line_1": "KPHB Colony, Kukatpally",
			"city": "Hyderabad",
			"state": "Telangana",
			"zip_code": 500072,
			"posting_date": add_days(today, -3),
		},
		# Another Personal Loan
		{
			"applicant": customers[0] if len(customers) > 0 else None,
			"loan_product": "PL-002",
			"loan_amount": 1000000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 24,
			"description": "Personal Loan for medical emergency expenses",
			"first_name": "Rajesh",
			"last_name": "Sharma",
			"applicant_email_address": "rajesh.sharma@demo.com",
			"applicant_phone_number": "+91 9876543210",
			"address_line_1": "42, MG Road, Andheri West",
			"city": "Mumbai",
			"state": "Maharashtra",
			"zip_code": 400058,
			"posting_date": add_days(today, -2),
		},
		# Vehicle Loan 2
		{
			"applicant": customers[3] if len(customers) > 3 else customers[0],
			"loan_product": "VL-001",
			"loan_amount": 1200000,
			"repayment_method": "Repay Over Number of Periods",
			"repayment_periods": 48,
			"description": "Vehicle Loan for purchasing Honda City",
			"first_name": "Sunita",
			"last_name": "Reddy",
			"applicant_email_address": "sunita.reddy@demo.com",
			"applicant_phone_number": "+91 9876543213",
			"address_line_1": "78, Vidyanagar, Electronic City Phase 1",
			"city": "Bangalore",
			"state": "Karnataka",
			"zip_code": 560100,
			"posting_date": today,
		},
	]

	for i, app in enumerate(applications):
		if not app.get("applicant"):
			print(f"  ⚠️  Skipping application {i+1} — no applicant available")
			continue

		# Check if similar application already exists
		existing = frappe.db.exists("Loan Application", {
			"applicant": app["applicant"],
			"loan_product": app["loan_product"],
			"loan_amount": app["loan_amount"],
		})

		if not existing:
			loan_app = {
				"doctype": "Loan Application",
				"applicant_type": "Customer",
				"company": company,
			}
			loan_app.update(app)

			try:
				doc = frappe.get_doc(loan_app)
				doc.insert(ignore_permissions=True)
				print(f"  ✅ App #{i+1}: {app['first_name']} {app['last_name']} — ₹{app['loan_amount']:,.0f} ({app['loan_product']})")
			except Exception as e:
				print(f"  ⚠️  Could not create application #{i+1}: {str(e)[:100]}")
		else:
			print(f"  ⏭️  Application for {app['first_name']} {app['last_name']} ({app['loan_product']}) already exists")


# =============================================================================
# Summary
# =============================================================================

def print_summary():
	print("\n" + "=" * 60)
	print("📊 DEMO DATA SUMMARY")
	print("=" * 60)

	counts = {
		"Loan Category": frappe.db.count("Loan Category"),
		"Loan Classification": frappe.db.count("Loan Classification"),
		"Loan Security Type": frappe.db.count("Loan Security Type"),
		"Loan Security": frappe.db.count("Loan Security"),
		"Loan Security Price": frappe.db.count("Loan Security Price"),
		"Loan Document Type": frappe.db.count("Loan Document Type"),
		"Loan Product": frappe.db.count("Loan Product"),
		"Customer": frappe.db.count("Customer"),
		"Loan Application": frappe.db.count("Loan Application"),
		"Loan": frappe.db.count("Loan"),
	}

	for doctype, count in counts.items():
		print(f"  {doctype:<25} : {count}")

	print("=" * 60)
	print("\n💡 Next steps you can do via the UI:")
	print("  1. Submit & Approve Loan Applications (change status)")
	print("  2. Create Loans from approved applications")
	print("  3. Create Loan Disbursements")
	print("  4. Create Loan Repayments")
	print("  5. Process interest accruals")
	print("  6. Create Loan Security Assignments for secured loans")
