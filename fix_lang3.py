import pathlib

replacements3 = [
    ("maombi", "applications"),
    ("Maombi", "Applications"),
    ("za Hivi Karibuni", "Recent"),
    ("Reject applications", "Reject application"),
    ("Approve maombi", "Approve application"),
    ("Una uhakika unataka", "Are you sure you want to"),
    ("maombi haya", "this application"),
    ("Reports za", "Reports"),
    ("Hivi Karibuni", "Recent"),
    ("ya Hivi Karibuni", "Recent"),
    ("Reports Recent", "Recent Reports"),
    ("No watumiaji", "No users"),
    ("No  maombi", "No applications"),
    ("Search maombi", "Search applications"),
    ("View maombi", "View application"),
    ("Showing 1-5 kati ya", "Showing 1-5 of"),
    ("kati ya", "of"),
    ("Reject application", "Reject"),
    ("Approve application", "Approve"),
]

def process_file(path):
    text = pathlib.Path(path).read_text(encoding='utf-8')
    original = text
    for sw, en in replacements3:
        text = text.replace(sw, en)
    # Fix double spaces and specific cleanup
    text = text.replace("Reports Recent", "Recent Reports")
    text = text.replace("Recent Recent", "Recent")
    text = text.replace("Reject application", "Reject")
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
    print(f"Done {base}: {count}")

print("Third pass complete")
# Quick verify
for f in pathlib.Path(r"C:\morgihome\templates\bank").rglob("*.html"):
    txt = pathlib.Path(f).read_text(encoding='utf-8')
    if "maombi" in txt or "Karibu" in txt or "Jumla" in txt or "za Hivi" in txt:
        print(f"Still has Swahili: {f}")
