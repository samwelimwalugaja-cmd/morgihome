import pathlib, re, os

# Comprehensive Swahili -> English for ALL portals
replacements = [
    # Bank portal leftovers
    ("Karibu tena! Hapa ndipo unapo", "Welcome back! This is where you"),
    ("Karibu tena", "Welcome back"),
    ("Kagua na idhinisha applications ya mikopo", "Review and approve loan applications"),
    ("Kagua na idhinisha mikataba ya wateja", "Review and approve client contracts"),
    ("View ratiba yako ya marejesho ya mkopo", "View your loan repayment schedule"),
    ("Fuatilia applications yako ya mkopo katika hatu", "Track your loan applications through stages"),
    ("Maelezo haya yatatumwa kwa mte", "This information will be sent to the customer"),
    ("Uchambuzi wa hatari na mikopo", "Risk and loan analysis"),
    ("Tafadhali", "Please"),
    ("Orodha", "List"),
    ("Inasubiri", "Pending"),
    ("Angalia", "View"),
    ("Inaonyesha", "Showing"),
    ("Mkataba", "Contract"),
    ("Jina", "Name"),
    ("Simu", "Phone"),
    ("Aina", "Type"),
    ("Kiasi", "Amount"),
    ("Hati", "Document"),
    ("Hati ya Usajili", "Registration Certificate"),
    ("Hati ya Kodi", "Tax Clearance"),
    ("Leseni", "License"),
    ("Leseni ya Biashara", "Business License"),
    ("Kodi", "Tax"),
    ("Usajili", "Registration"),
    ("Hakiki", "Verify"),
    ("Hakiki: <span", "Verified: <span"),
    ("Malipo", "Payments"),
    ("malipo yako", "your payments"),
    ("Muda", "Duration"),
    ("Muda gani", "How long"),
    ("Inachukua muda gani", "How long does it take"),
    ("Riba", "Interest"),
    ("Dhamana", "Collateral"),
    ("Mwisho: Ago 2026", "End: Aug 2026"),
    ("mikopo", "loans"),
    ("NPL 1.0% • 7 mikopo", "NPL 1.0% • 7 loans"),
    ("Chagua vigezo na tarehe", "Choose filters and date"),
    ("ya Marejesho", "Repayments"),
    ("marejesho ya mkopo", "loan repayments"),
    ("ratiba yako ya marejesho", "your repayment schedule"),
    ("Hakuna Email/Phone/NIN banner. Badge tu ya", "No Email/Phone/NIN banner. Only"),
    ("hakuna Email/Phone/NIN banner", "no Email/Phone/NIN banner"),
    ("HAIHITAJI phone/NIN", "does NOT require phone/NIN"),
    ("Muuza", "Seller"),
    ("Wateja", "Customers"),
    ("Thibitishwa", "Verified"),
    ("Tupigie simu", "Call us"),
    ("Kutafuta na", "Search and"),
    ("Kutafuta", "Search"),
    ("Iliwasilishwa 02 Sep 2026", "Submitted 02 Sep 2026"),
    ("Adres", "Address"),
    ("Kitambulisho NIDA", "National ID"),
    ("Mkataba wa Ajira", "Employment Contract"),
    ("Hati ya Nyumba", "Property Title Deed"),
    ("Bank Statement 6m", "6-Month Bank Statement"),
    ("Hakuna watumiaji", "No users"),
    ("View ratiba", "View schedule"),
    ("KUIDHINISHA", "APPROVE"),
    ("KUKATAA", "REJECT"),
    ("Una uhakika unataka", "Are you sure you want to"),
    ("this application", "this application"),
    ("Complete email + 3 documents", "Complete 3 business documents"),
    ("Complete 4 steps", "Complete 3 steps"),
    ("0/4", "0/3"),
    ("4 steps", "3 steps"),
    ("Vinjari majumba, omba mkopo, na fuatilia malipo yako", "Browse houses, apply for loans, and track your payments"),
    ("Customer ana uwezo", "Customer has ability"),
    # Signup / Accounts
    ("Mteja/Mkopaji", "Customer/Borrower"),
    ("Muuza Nyumba", "House Seller"),
    ("Jina la Benki", "Bank Name"),
    ("Jina la Kampuni", "Company Name"),
    ("Jina Kamili", "Full Name"),
    ("Namba ya Simu", "Phone Number"),
    ("Leseni ya Kitaalamu", "Professional License"),
    ("Hati ya Kodi", "Tax Clearance"),
    ("Hati ya Usajili", "Registration Certificate"),
    ("Wanawekwa na Admin tu", "Created by Admin only"),
    ("Inasubiri uthibitisho wa Admin", "Pending admin approval"),
    ("Password ya muda itatumwa kwa email", "Temporary password will be sent via email"),
    ("Imejengwa kwa Shadcn Admin Template", "Built with Shadcn Admin Template"),
    ("Ac 2026 MorgiHome", "© 2026 MorgiHome"),
    ("Imejengwa kwa", "Built with"),
    ("Hapa ni muhtasari", "Here is a summary"),
    ("Here is today's bank operations summary", "Here is today's bank operations summary"),
    ("Hakuna Email/Phone/NIN banner", "No Email/Phone/NIN banner"),
    ("kati ya", "of"),
    ("Ya Mwezi", "Monthly"),
    ("ya Mwezi", "monthly"),
    ("kwa Mwezi", "per Month"),
    ("kwa mwezi", "per Month"),
    ("•", "•"),
    # Generic
    ("Tafuta", "Search"),
    ("Hakuna", "No"),
    ("Ondoa", "Remove"),
    ("Thibitisha", "Confirm"),
    ("Inabaki", "Remaining"),
    ("Imeongezwa", "Added"),
    ("Imetumwa kwa", "Sent to"),
    ("Tafadhali hakiki", "Please verify"),
    ("Anwani", "Address"),
    ("Muda", "Term"),
    ("Riba", "Interest"),
    ("Deni", "Debt"),
    ("Mkopo", "Loan"),
    ("Nyumba", "House"),
    ("Ardhi", "Land"),
    ("Hakiki", "Verify"),
    ("Malipo", "Payment"),
    ("Dhamana", "Collateral"),
    ("Hatari", "Risk"),
    ("Idhinisha", "Approve"),
    ("Kataa", "Reject"),
    ("Inasubiri", "Pending"),
    ("Thibitishwa", "Verified"),
    ("kati ya", "of"),
    # Data-sw attributes - make English
    ('data-sw="Karibu', 'data-sw="Welcome'),
    ('data-sw="Tupigie simu', 'data-sw="Call us'),
    ('data-sw="Kutafuta', 'data-sw="Search'),
]

def process_file(path):
    try:
        text = pathlib.Path(path).read_text(encoding='utf-8')
    except:
        return False
    original = text
    for sw, en in replacements:
        text = text.replace(sw, en)
    # Fix double replacements
    text = text.replace("applicationlications", "applications")
    text = text.replace("Totallications", "Total Applications")
    # Fix encoding artifacts
    text = text.replace("�?�", "•")
    text = text.replace("dY`<", "")
    text = text.replace("Ac 2026", "© 2026")
    if text != original:
        pathlib.Path(path).write_text(text, encoding='utf-8')
        return True
    return False

count_total = 0
for base in [r"C:\morgihome\templates", r"C:\morgihome\static", r"C:\sampleweb\templates", r"C:\sampleweb\static"]:
    p = pathlib.Path(base)
    if not p.exists():
        continue
    count = 0
    for f in p.rglob("*.*"):
        if f.suffix in [".html",".js",".css"]:
            if process_file(f):
                count += 1
                print(f"Updated {f}")
    print(f"Done {base}: {count} files")
    count_total += count

print(f"Total updated: {count_total}")

# Final scan for remaining obvious Swahili
print("\n=== Final check ===")
for f in pathlib.Path(r"C:\morgihome\templates").rglob("*.html"):
    txt = pathlib.Path(f).read_text(encoding='utf-8', errors='ignore')
    for word in ["Karibu","Jumla","Maombi","Hakuna","Tafuta","Mteja","Muuza","Jiandikisha"]:
        if word in txt:
            print(f"Still has {word}: {f}")
            break
