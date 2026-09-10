import pathlib

replacements2 = [
    ("Jumla", "Total"),
    ("Angalia", "View"),
    ("Inaonyesha", "Showing"),
    ("Tafuta", "Search"),
    ("Hakuna", "No"),
    ("Idhinisha", "Approve"),
    ("Kataa", "Reject"),
    ("Mkataba", "Contract"),
    ("Jina", "Name"),
    ("Simu", "Phone"),
    ("Anwani", "Address"),
    ("Dhamana", "Collateral"),
    ("Hatari", "Risk"),
    ("Thibitishwa", "Verified"),
    ("Inasubiri", "Pending"),
    ("Orodha", "List"),
    ("Tafadhali", "Please"),
    ("Wasiliana na admin", "Contact admin"),
    ("Ukisahau password", "Forgot password"),
    ("Thibitisha", "Confirm"),
    ("Mteja", "Customer"),
    ("Muuza", "Seller"),
    ("Mkataba wa Ajira", "Employment Contract"),
    ("Hati ya Nyumba", "Property Title"),
    ("Bank Statement 6m", "6M Bank Statement"),
    ("Kitambulisho NIDA", "National ID"),
    ("Sajili", "Register"),
    ("Sajili benki", "Register bank"),
    ("Sajili kampuni", "Register company"),
    ("Sajili wakili", "Register lawyer"),
    ("Chagua Faili", "Choose File"),
    ("Hakuna faili", "No file"),
    ("Hakuna watumiaji", "No users"),
    ("Wateja", "Customers"),
    ("Wauzaji", "Sellers"),
    ("Inabaki", "Remaining"),
    ("Imeongezwa", "Added"),
    ("Imetumwa kwa", "Sent to"),
    ("Akaunti yako", "Your account"),
    ("Tafadhali hakiki", "Please verify"),
    ("Akaunti haijathibitishwa", "Account not verified"),
    ("kati ya", "of"),
    ("ya Mwezi", "of Month"),
    ("kwa Mwezi", "per Month"),
]

def process_file(path):
    text = pathlib.Path(path).read_text(encoding='utf-8')
    original = text
    for sw, en in replacements2:
        text = text.replace(sw, en)
    if text != original:
        pathlib.Path(path).write_text(text, encoding='utf-8')
        return True
    return False

for base in [r"C:\morgihome\templates", r"C:\sampleweb\templates"]:
    p = pathlib.Path(base)
    if not p.exists():
        continue
    count = 0
    for f in p.rglob("*.html"):
        if process_file(f):
            count += 1
            print(f"Updated {f}")
    print(f"Done {base}: {count} files")

print("Second pass complete")
