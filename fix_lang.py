import pathlib, re

# Define replacements Swahili -> English
replacements = [
    ("Karibu tena, CRDB Bank", "Welcome back, CRDB Bank"),
    ("Hapa ni muhtasari wa shughuli za benki leo", "Here is today's bank operations summary"),
    ("Angalia Maombi", "View Applications"),
    ("Pakua Ripoti", "Download Report"),
    ("Jumla ya Maombi", "Total Applications"),
    ("Yanayosubiri", "Pending"),
    ("Yaliyoidhinishwa", "Approved"),
    ("Imetolewa (TZS)", "Total Disbursed (TZS)"),
    ("Maombi kwa Mwezi", "Applications per Month"),
    ("Maombi", "Applications"),
    ("Yaliyoidhinishwa", "Approved"),
    ("Yaliyotolewa", "Disbursed"),
    ("Hatari Ndogo", "Low Risk"),
    ("Hatari ya Kati", "Medium Risk"),
    ("Hatari Kubwa", "High Risk"),
    ("Hatari Ndogo • Idhinisha", "Low Risk • Approve"),
    ("Chunguza Maombi", "View Applications"),
    ("Review Maombi", "Review Applications"),
    ("Mikataba", "Contracts"),
    ("Marejesho", "Repayments"),
    ("Ripoti", "Reports"),
    ("Quick Actions", "Quick Actions"),
    ("Maombi ya Hivi Karibuni", "Recent Applications"),
    ("Mteja", "Customer"),
    ("Kiasi", "Amount"),
    ("Aina", "Type"),
    ("Hatari (AI)", "AI Risk"),
    ("Hali", "Status"),
    ("Tarehe", "Date"),
    ("Taarifa za Mteja", "Customer Information"),
    ("Jina Kamili", "Full Name"),
    ("Simu", "Phone"),
    ("Ajira", "Employment"),
    ("Mapato / Mwezi", "Monthly Income"),
    ("Anwani", "Address"),
    ("Maelezo ya Mkopo", "Loan Details"),
    ("Muda", "Term"),
    ("Riba", "Interest"),
    ("Malipo / Mwezi", "Monthly Payment"),
    ("Mali", "Property"),
    ("Nyaraka", "Documents"),
    ("Mwenendo wa Maombi", "Application Timeline"),
    ("Maelezo ya Afisa", "Officer Notes"),
    ("Hifadhi Maelezo", "Save Notes"),
    ("Muhtasari wa Uamuzi", "Decision Summary"),
    ("AI Score", "AI Score"),
    ("DTI Ratio", "DTI Ratio"),
    ("Historia ya Mikopo", "Credit History"),
    ("Tahadhari", "Warning"),
    ("Hati ya nyumba bado haijathibitishwa kikamilifu", "Property title not fully verified"),
    ("Maombi yamewasilishwa", "Application Submitted"),
    ("AI Analysis imekamilika", "AI Analysis Completed"),
    ("Inasubiri Review ya Bank", "Pending Bank Review"),
    ("Uamuzi", "Decision"),
    ("Kagua Nyaraka", "Review Documents"),
    ("Fungua PDF", "Open PDF"),
    ("Pakua", "Download"),
    ("Chukua Uamuzi", "Make Decision"),
    ("Uamuzi", "Decision"),
    ("Kiasi Kitakachotolewa", "Amount to Disburse"),
    ("Maelezo / Sababu", "Comments / Reason"),
    ("Andika sababu ya uamuzi wako", "Enter decision reason"),
    ("Nathibitisha kuwa nimekagua nyaraka zote", "I confirm I have reviewed all documents"),
    ("Thibitisha Uamuzi", "Confirm Decision"),
    ("Ghairi", "Cancel"),
    ("Kumbuka", "Note"),
    ("Uamuzi ukishatolewa, hauwezi kutenguliwa", "Once submitted, decision cannot be undone"),
    ("Orodha ya Maombi", "Applications List"),
    ("Jumla 1,284 • 86 yanasubiri uamuzi", "Total 1,284 • 86 pending decision"),
    ("Export CSV", "Export CSV"),
    ("Maombi Mapya", "New Application"),
    ("Tafuta kwa jina, #APP, namba ya simu", "Search by name, #APP, phone"),
    ("Hali zote", "All Statuses"),
    ("Aina zote", "All Types"),
    ("Hatari zote (AI)", "All Risks (AI)"),
    ("Inaonyesha 1-5 kati ya 1,284", "Showing 1-5 of 1,284"),
    ("Mteja / ID", "Customer / ID"),
    ("Kiasi & Aina", "Amount & Type"),
    ("Mapato / Score", "Income / Score"),
    ("Kitendo", "Action"),
    ("Inasubiri Saini", "Pending Signature"),
    ("Imekamilika", "Completed"),
    ("Mikataba ya Mikopo", "Loan Contracts"),
    ("742 mikataba hai • TZS 4.2B imetolewa", "742 active contracts • TZS 4.2B disbursed"),
    ("Mkataba", "Contract"),
    ("Hai", "Active"),
    ("Tuma Reminder", "Send Reminder"),
    ("Jumla Marejesho (Mwezi)", "Total Repayments (Month)"),
    ("Yaliyolipiwa Kwa Wakati", "Paid On Time"),
    ("Yaliyochelewa (30+ days)", "Overdue (30+ days)"),
    ("Yaliyoshindwa (NPL)", "Non-Performing (NPL)"),
    ("Marejesho ya Mikopo", "Loan Repayments"),
    ("Marejesho kwa Mwezi (TZS M)", "Monthly Repayments (TZS M)"),
    ("Top Wacheleweshaji", "Top Defaulters"),
    ("Angalia Wote (23)", "View All (23)"),
    ("Ratiba ya Marejesho - Sept 2026", "Repayment Schedule - Sep 2026"),
    ("Tarehe ya Kulipa", "Due Date"),
    ("Iliyolipiwa", "Paid Amount"),
    ("Tafuta mkataba", "Search contract"),
    ("Mkataba Mpya", "New Contract"),
    ("Ripoti za Benki", "Bank Reports"),
    ("Pakua na chambua data ya mikopo", "Download and analyze loan data"),
    ("Pakua Ripoti ya Mwezi (PDF)", "Download Monthly Report (PDF)"),
    ("Jenga Ripoti Maalum", "Build Custom Report"),
    ("Aina ya Ripoti", "Report Type"),
    ("Kuanzia", "From"),
    ("Hadi", "To"),
    ("Tengeneza Ripoti", "Generate Report"),
    ("Ripoti za Hivi Karibuni", "Recent Reports"),
    ("Jina la Ripoti", "Report Name"),
    ("Na", "By"),
    ("Benki", "Bank"),
    ("Mteja / Mkataba", "Customer / Contract"),
    ("Menu Kuu", "Main Menu"),
    ("Mfumo", "System"),
    ("Mipangilio", "Settings"),
    ("Msaada", "Help"),
    ("Toka", "Logout"),
    ("Tafuta maombi, wateja", "Search applications, customers"),
    ("Jiandikisha ili kuanza", "Sign up to get started"),
    ("I am a:", "I am a:"),
    ("Mteja/Mkopaji", "Customer/Borrower"),
    ("Muuza Nyumba", "House Seller"),
    ("Wanawekwa na Admin tu — hawawezi kujisajili wenyewe", "Created by Admin only — cannot self-register"),
    ("Bank/RealEstate/Lawyer: Wanawekwa na Admin tu", "Bank/RealEstate/Lawyer: Created by Admin only"),
    ("Jina la Benki", "Bank Name"),
    ("Thibitisha", "Confirm"),
    ("Sajili benki mpya kwenye mfumo", "Register a new bank in the system"),
    ("Sajili kampuni ya mali isiyohamishika", "Register a real estate company"),
    ("Sajili wakili mpya", "Register a new lawyer"),
    ("Inasubiri uthibitisho wa Admin", "Pending admin approval"),
    ("Password ya muda itatumwa kwa email", "Temporary password will be sent via email"),
    ("Akaunti imeundwa", "Account created"),
    ("Karibu MorgiHome", "Welcome to MorgiHome"),
]

def process_file(path):
    text = pathlib.Path(path).read_text(encoding='utf-8')
    original = text
    for sw, en in replacements:
        text = text.replace(sw, en)
    if text != original:
        pathlib.Path(path).write_text(text, encoding='utf-8')
        return True
    return False

# Process both projects
for base in [r"C:\morgihome\templates", r"C:\sampleweb\templates"]:
    p = pathlib.Path(base)
    if not p.exists():
        continue
    count = 0
    for f in p.rglob("*.html"):
        if process_file(f):
            count += 1
            print(f"Updated {f}")
    print(f"Done {base}: {count} files changed")

# Also process login/signup templates that have Swahili
for base in [r"C:\morgihome\templates", r"C:\sampleweb\templates\accounts"]:
    p = pathlib.Path(base)
    if not p.exists():
        continue
    for f in p.rglob("*.html"):
        # Already handled above, but keep for safety
        pass

print("Language fix complete")
