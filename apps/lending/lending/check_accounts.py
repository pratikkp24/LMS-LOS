"""Quick info check."""
import frappe

def info():
    customers = frappe.get_all("Customer", fields=["name","customer_name","customer_type"], limit=20)
    print("\n--- Customers ---")
    for c in customers:
        print(f"  {c.name}: {c.customer_name} ({c.customer_type})")

    products = frappe.get_all("Loan Product", fields=["name","loan_name","is_term_loan"], limit=20)
    print("\n--- Loan Products ---")
    for p in products:
        print(f"  {p.name}: {p.loan_name} (term={p.is_term_loan})")

    securities = frappe.get_all("Loan Security", fields=["name","loan_security_name","disabled"], limit=20)
    print("\n--- Loan Securities ---")
    for s in securities:
        print(f"  {s.name}: {s.loan_security_name} (disabled={s.disabled})")

    # Count existing data
    print("\n--- Current Counts ---")
    for dt in ["Loan Application", "Loan", "Loan Disbursement", "Loan Repayment", "Loan Interest Accrual", "Loan Write Off", "Loan Security Shortfall"]:
        print(f"  {dt}: {frappe.db.count(dt)}")
