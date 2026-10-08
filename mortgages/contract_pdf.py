import os
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


def _get_profile_image_path(user):
    """Return a filesystem path to the user's profile image, or None."""
    if not user:
        return None
    try:
        if user.profile_image and getattr(user.profile_image, 'path', None):
            path = user.profile_image.path
            if os.path.exists(path):
                return path
    except Exception:
        pass
    return None


def _resolve_media_path(url_or_path):
    """Resolve a media URL or relative path to an absolute filesystem path."""
    if not url_or_path:
        return None
    try:
        from django.conf import settings as django_settings
        media_url = getattr(django_settings, 'MEDIA_URL', '/media/')
        media_root = getattr(django_settings, 'MEDIA_ROOT',
                             os.path.join(django_settings.BASE_DIR, 'media'))
        static_url = getattr(django_settings, 'STATIC_URL', '/static/')
        s = str(url_or_path)
        if s.startswith(media_url):
            relative = s[len(media_url):]
        elif s.startswith('/media/'):
            relative = s[7:]
        elif s.startswith(static_url or '/static/'):
            return None
        else:
            relative = s
        relative = relative.lstrip('/')
        full = os.path.join(media_root, relative)
        if os.path.exists(full):
            return full
    except Exception:
        pass
    return None


def _safe_image(path, width=1.0 * inch, height=1.0 * inch):
    """Return a ReportLab Image if the file exists and is readable."""
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image(path, width=width, height=height)
        return img
    except Exception:
        return None


def _fmt_money(amount):
    try:
        return "{:,.0f}".format(float(amount))
    except Exception:
        return str(amount)


def _full_name(user):
    if not user:
        return "---"
    name = user.get_full_name()
    if name and name.strip():
        return name.strip()
    return user.email or "---"


def _words_date(d):
    """Return a readable English date string from a date object."""
    if not d:
        return ""
    try:
        return d.strftime("%d %B %Y")
    except Exception:
        return str(d)


def _address_of(user):
    return getattr(user, 'address', '') or "---"


def _phone_of(user):
    return getattr(user, 'phone_number', '') or "---"


def _email_of(user):
    return getattr(user, 'email', '') or "---"


def generate_sale_contract_pdf(contract, physical_signing_date=None,
                               physical_signing_location=""):
    """
    Generate a professional English house sale contract PDF for the given
    Contract object. Returns a BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='TitleEnglish',
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=colors.HexColor('#0A2B4E'),
    ))
    styles.add(ParagraphStyle(
        name='SubTitleEnglish',
        fontName='Helvetica-Bold',
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=14,
        textColor=colors.HexColor('#0077B6'),
    ))
    styles.add(ParagraphStyle(
        name='SectionEnglish',
        fontName='Helvetica-Bold',
        fontSize=11,
        spaceBefore=12,
        spaceAfter=5,
        textColor=colors.HexColor('#0A2B4E'),
    ))
    styles.add(ParagraphStyle(
        name='BodyEnglish',
        fontName='Helvetica',
        fontSize=10,
        alignment=TA_JUSTIFY,
        leading=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='ClauseEnglish',
        fontName='Helvetica',
        fontSize=10,
        alignment=TA_JUSTIFY,
        leading=14,
        leftIndent=14,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name='SmallEnglish',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#555555'),
    ))
    styles.add(ParagraphStyle(
        name='LabelEnglish',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#333333'),
    ))
    styles.add(ParagraphStyle(
        name='ValueEnglish',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#000000'),
    ))
    styles.add(ParagraphStyle(
        name='CenterSmall',
        fontName='Helvetica',
        fontSize=9,
        alignment=TA_CENTER,
        leading=11,
        textColor=colors.HexColor('#555555'),
    ))

    app = contract.mortgage
    prop = app.property if app else None
    seller = contract.seller
    buyer = contract.customer
    bank = contract.bank

    contract_number = f"CTR-{contract.id:06d}"
    today = date.today()
    today_str = today.strftime("%d/%m/%Y")
    today_words = _words_date(today)

    signing_date = physical_signing_date or contract.physical_signing_date
    signing_location = physical_signing_location or contract.physical_signing_location or ""
    signing_date_str = _words_date(signing_date) if signing_date else ""

    property_title = prop.title if prop else "---"
    property_location = prop.location if prop else "---"
    property_type = prop.get_property_type_display() if prop else "---"
    plot_number = getattr(prop, 'napa', '') or getattr(prop, 'plot_number', '') or "---"
    block = getattr(prop, 'block', '') or "---"
    area = getattr(prop, 'area', '') or "---"
    bedrooms = getattr(prop, 'bedrooms', '') or "---"
    bathrooms = getattr(prop, 'bathrooms', '') or "---"
    sale_price = prop.price if prop else (app.loan_amount or 0)
    loan_amount = app.loan_amount or 0
    repayment_period = app.repayment_period or "---"
    interest_rate = getattr(bank, 'interest_rate', None) or "14.0"
    app_number = getattr(app, 'application_number', '') or f"APP-{app.id if app else 0}"

    seller_name = _full_name(seller)
    buyer_name = _full_name(buyer)
    bank_name = _full_name(bank)

    seller_role = "Real Estate Company" if seller and getattr(seller, 'role', '') == 'realestate' else "Seller"
    seller_address = _address_of(seller)
    buyer_address = _address_of(buyer)
    seller_phone = _phone_of(seller)
    buyer_phone = _phone_of(buyer)
    seller_email = _email_of(seller)
    buyer_email = _email_of(buyer)

    buyer_nida = getattr(app, 'nida_number', '') or "---"
    buyer_dob = getattr(app, 'dob', None)
    buyer_dob_str = buyer_dob.strftime("%d %B %Y") if buyer_dob else "---"
    buyer_marital = getattr(app, 'marital_status', '') or "---"
    buyer_employer = getattr(app, 'employer_name', '') or "---"
    buyer_job = getattr(app, 'job_title', '') or "---"

    story = []

    # Header / logos
    header_data = []
    bank_img = _safe_image(_get_profile_image_path(bank), width=0.8 * inch,
                           height=0.8 * inch)
    morgi_logo_cell = Paragraph(
        '<font color="#0A2B4E" size="16"><b>MorgiHome</b></font><br/>'
        '<font color="#555555" size="9">House Sale Agreement</font>',
        styles['BodyEnglish']
    )
    if bank_img:
        header_data.append([bank_img, morgi_logo_cell])
    else:
        header_data.append(["", morgi_logo_cell])

    header_table = Table(header_data, colWidths=[1 * inch, 5.6 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="100%", thickness=1.5,
                            color=colors.HexColor('#0A2B4E')))
    story.append(Spacer(1, 0.12 * inch))

    # Title
    story.append(Paragraph("HOUSE SALE AGREEMENT", styles['TitleEnglish']))
    story.append(Paragraph(f"Contract Number: <b>{contract_number}</b>",
                           styles['SubTitleEnglish']))
    story.append(Paragraph(f"Date: {today_words}", styles['CenterSmall']))
    story.append(Spacer(1, 0.08 * inch))

    # Parties with photos: seller left, buyer right
    seller_img = _safe_image(_get_profile_image_path(seller), width=0.9 * inch,
                             height=0.9 * inch)
    buyer_img = _safe_image(_get_profile_image_path(buyer), width=0.9 * inch,
                            height=0.9 * inch)

    seller_photo_cell = seller_img if seller_img else Paragraph(
        "<i>[Photo]</i>", styles['CenterSmall'])
    buyer_photo_cell = buyer_img if buyer_img else Paragraph(
        "<i>[Photo]</i>", styles['CenterSmall'])

    seller_details = Paragraph(
        f"<b>{seller_role.upper()}</b><br/>"
        f"Full Name: {seller_name}<br/>"
        f"Address: {seller_address}<br/>"
        f"Phone: {seller_phone}<br/>"
        f"Email: {seller_email}",
        styles['ValueEnglish']
    )
    buyer_details = Paragraph(
        f"<b>BUYER</b><br/>"
        f"Full Name: {buyer_name}<br/>"
        f"Address: {buyer_address}<br/>"
        f"Phone: {buyer_phone}<br/>"
        f"Email: {buyer_email}",
        styles['ValueEnglish']
    )

    party_table = Table(
        [[seller_photo_cell, seller_details, buyer_photo_cell, buyer_details]],
        colWidths=[1.0 * inch, 2.6 * inch, 1.0 * inch, 2.6 * inch]
    )
    party_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#cccccc')),
        ('BOX', (2, 0), (2, 0), 0.5, colors.HexColor('#cccccc')),
    ]))
    story.append(party_table)
    story.append(Spacer(1, 0.1 * inch))

    # Recitals
    story.append(Paragraph("RECITALS", styles['SectionEnglish']))
    story.append(Paragraph(
        f"This House Sale Agreement is made on <b>{today_words}</b> between "
        f"<b>{seller_name}</b> (hereinafter referred to as the <b>{seller_role}</b>) "
        f"and <b>{buyer_name}</b> (hereinafter referred to as the <b>Buyer</b>). "
        f"Both parties have agreed to the terms and conditions set out below, "
        f"with the involvement of <b>{bank_name}</b> (hereinafter referred to as the "
        f"<b>Bank / Mortgage Lender</b>).",
        styles['BodyEnglish']
    ))

    # Property info
    story.append(Paragraph("PROPERTY DETAILS", styles['SectionEnglish']))
    cover_url = prop.cover_image_url if prop and hasattr(prop, 'cover_image_url') else None
    prop_image = _safe_image(_resolve_media_path(cover_url),
                             width=1.5 * inch, height=1.0 * inch)
    prop_data = [
        [Paragraph("Property Name:", styles['LabelEnglish']),
         Paragraph(property_title, styles['ValueEnglish'])],
        [Paragraph("Type:", styles['LabelEnglish']),
         Paragraph(property_type, styles['ValueEnglish'])],
        [Paragraph("Location:", styles['LabelEnglish']),
         Paragraph(property_location, styles['ValueEnglish'])],
        [Paragraph("Plot/Title No.:", styles['LabelEnglish']),
         Paragraph(f"{plot_number} (Block {block})", styles['ValueEnglish'])],
        [Paragraph("Size:", styles['LabelEnglish']),
         Paragraph(f"{area} m² — Bedrooms {bedrooms} | Bathrooms {bathrooms}",
                   styles['ValueEnglish'])],
        [Paragraph("Sale Price:", styles['LabelEnglish']),
         Paragraph(f"TZS {_fmt_money(sale_price)}", styles['ValueEnglish'])],
    ]
    if prop_image:
        prop_data.append([Paragraph("Property Photo:", styles['LabelEnglish']),
                          prop_image])
    prop_table = Table(prop_data, colWidths=[1.8 * inch, 5.2 * inch])
    prop_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(prop_table)
    story.append(Spacer(1, 0.08 * inch))

    # Buyer info
    story.append(Paragraph("BUYER / MORTGAGE APPLICANT DETAILS", styles['SectionEnglish']))
    buyer_data = [
        [Paragraph("Application Number:", styles['LabelEnglish']),
         Paragraph(app_number, styles['ValueEnglish'])],
        [Paragraph("Full Name:", styles['LabelEnglish']),
         Paragraph(buyer_name, styles['ValueEnglish'])],
        [Paragraph("Date of Birth:", styles['LabelEnglish']),
         Paragraph(buyer_dob_str, styles['ValueEnglish'])],
        [Paragraph("NIDA / ID Number:", styles['LabelEnglish']),
         Paragraph(buyer_nida, styles['ValueEnglish'])],
        [Paragraph("Marital Status:", styles['LabelEnglish']),
         Paragraph(buyer_marital.title() if buyer_marital != '---' else '---',
                   styles['ValueEnglish'])],
        [Paragraph("Employer:", styles['LabelEnglish']),
         Paragraph(buyer_employer, styles['ValueEnglish'])],
        [Paragraph("Job Title:", styles['LabelEnglish']),
         Paragraph(buyer_job, styles['ValueEnglish'])],
        [Paragraph("Phone:", styles['LabelEnglish']),
         Paragraph(buyer_phone, styles['ValueEnglish'])],
        [Paragraph("Email:", styles['LabelEnglish']),
         Paragraph(buyer_email, styles['ValueEnglish'])],
    ]
    buyer_table = Table(buyer_data, colWidths=[1.8 * inch, 5.2 * inch])
    buyer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(buyer_table)
    story.append(Spacer(1, 0.08 * inch))

    # Bank / mortgage info
    story.append(Paragraph("BANK / MORTGAGE DETAILS", styles['SectionEnglish']))
    bank_data = [
        [Paragraph("Bank:", styles['LabelEnglish']),
         Paragraph(bank_name, styles['ValueEnglish'])],
        [Paragraph("Application Number:", styles['LabelEnglish']),
         Paragraph(app_number, styles['ValueEnglish'])],
        [Paragraph("Loan Amount:", styles['LabelEnglish']),
         Paragraph(f"TZS {_fmt_money(loan_amount)}", styles['ValueEnglish'])],
        [Paragraph("Repayment Period:", styles['LabelEnglish']),
         Paragraph(f"{repayment_period} months", styles['ValueEnglish'])],
        [Paragraph("Interest Rate:", styles['LabelEnglish']),
         Paragraph(f"{interest_rate}% per annum", styles['ValueEnglish'])],
        [Paragraph("Purchase Price:", styles['LabelEnglish']),
         Paragraph(f"TZS {_fmt_money(sale_price)}", styles['ValueEnglish'])],
    ]
    bank_table = Table(bank_data, colWidths=[1.8 * inch, 5.2 * inch])
    bank_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(bank_table)
    story.append(Spacer(1, 0.08 * inch))

    # Agreement
    story.append(Paragraph("AGREEMENT", styles['SectionEnglish']))
    signing_extra = ""
    if signing_date_str:
        signing_extra += (f"<br/><br/><b>Physical Signing Date:</b> "
                          f"{signing_date_str}.")
    if signing_location:
        signing_extra += (f"<br/><b>Physical Signing Location:</b> "
                          f"{signing_location}.")
    story.append(Paragraph(
        f"The {seller_role} agrees to sell and hand over the property described "
        f"above to the Buyer, and the Buyer agrees to purchase the property at "
        f"the price of <b>TZS {_fmt_money(sale_price)}</b>. Full payment shall be "
        f"made by <b>{bank_name}</b> to the {seller_role} in accordance with the "
        f"mortgage agreement between the Buyer and the Bank. This agreement is "
        f"subject to the loan being approved by the Bank and shall become "
        f"legally effective once all parties have signed.{signing_extra}",
        styles['BodyEnglish']
    ))

    # Clauses
    story.append(Paragraph("TERMS AND CONDITIONS", styles['SectionEnglish']))
    clauses = [
        "<b>1. OFFER AND ACCEPTANCE</b><br/>"
        "The Seller agrees to sell and deliver the property described herein to "
        "the Buyer, and the Buyer agrees to purchase the property at the stated price.",
        "<b>2. PAYMENT BY MORTGAGE</b><br/>"
        "Full payment of the purchase price shall be made by the mortgage lender "
        "(Bank) to the Seller in accordance with the mortgage agreement between "
        "the Buyer and the Bank. The Seller agrees to receive payment from the Bank.",
        "<b>3. TITLE DEED AND TRANSFER</b><br/>"
        "The Seller is responsible for providing a valid title deed and registering "
        "the transfer of ownership into the Buyer's name (or as approved by the Bank) "
        "immediately after payment is made to the Seller.",
        "<b>4. CONDITION OF PROPERTY</b><br/>"
        "The Seller confirms that the property is in good condition, has not been "
        "sold to any other party, and has not been pledged as security for any legal debt.",
        "<b>5. REGISTRATION COSTS AND TAXES</b><br/>"
        "All costs related to the registration of ownership transfer, transfer taxes, "
        "and any legal fees shall be paid as provided by the laws of the country and "
        "as agreed by the parties.",
        "<b>6. BREACH OF CONTRACT</b><br/>"
        "If either party breaches this agreement without lawful cause, that party shall "
        "be liable for damages suffered by the other party and the Bank.",
        "<b>7. BANK CONDITIONS</b><br/>"
        "This agreement is subject to the mortgage agreement between the Buyer and the "
        "Bank. The Bank reserves the right to decline the loan if its conditions are "
        "not met. If the loan is not approved, this agreement shall be void.",
        "<b>8. SIGNATURES AND WITNESSES</b><br/>"
        "This agreement shall be signed by the Seller, Buyer and a Bank representative "
        "in the presence of two witnesses. All signatures shall take place on the date "
        "and at the location designated by the Bank.",
    ]
    for clause in clauses:
        story.append(Paragraph(clause, styles['ClauseEnglish']))

    # Physical signing notice
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph("PHYSICAL SIGNING ARRANGEMENT", styles['SectionEnglish']))
    signing_notice = (
        f"Physical signing shall take place on "
        f"<b>{signing_date_str or '_____/_____/__________'}</b> at "
        f"<b>{signing_location or '____________________________________'}</b>. "
        "This date and location have been set by the Bank to ensure both the Seller "
        "and Buyer are legally aligned during the transfer of the property."
    )
    story.append(Paragraph(signing_notice, styles['BodyEnglish']))

    # Signature section
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("SIGNATURES", styles['SectionEnglish']))

    sig_data = [
        [Paragraph("<b>SELLER</b>", styles['LabelEnglish']),
         Paragraph("<b>BUYER</b>", styles['LabelEnglish'])],
        ["________________________________", "________________________________"],
        [Paragraph(seller_name, styles['SmallEnglish']),
         Paragraph(buyer_name, styles['SmallEnglish'])],
        [Paragraph("Date: __________________", styles['SmallEnglish']),
         Paragraph("Date: __________________", styles['SmallEnglish'])],
        [Paragraph("<b>BANK REPRESENTATIVE</b>", styles['LabelEnglish']),
         Paragraph("<b>BANK STAMP / SECOND SIGNATURE</b>", styles['LabelEnglish'])],
        ["________________________________", "________________________________"],
        [Paragraph(bank_name, styles['SmallEnglish']),
         Paragraph("Stamp / Signature", styles['SmallEnglish'])],
        [Paragraph("Date: __________________", styles['SmallEnglish']),
         Paragraph("Date: __________________", styles['SmallEnglish'])],
    ]
    sig_table = Table(sig_data, colWidths=[3.5 * inch, 3.5 * inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(sig_table)

    # Witnesses
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph("WITNESSES", styles['SectionEnglish']))
    witness_data = [
        [Paragraph("<b>First Witness</b>", styles['LabelEnglish']),
         Paragraph("<b>Second Witness</b>", styles['LabelEnglish'])],
        ["Name: ___________________________",
         "Name: ___________________________"],
        ["Signature: __________________________",
         "Signature: __________________________"],
        ["Date: _________________________",
         "Date: _________________________"],
    ]
    witness_table = Table(witness_data, colWidths=[3.5 * inch, 3.5 * inch])
    witness_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(witness_table)

    # Footer
    story.append(Spacer(1, 0.18 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor('#cccccc')))
    story.append(Paragraph(
        f"This agreement was generated by the MorgiHome system on {today_str}. "
        "This document is a copy of the agreement; a valid contract depends on "
        "signatures by all parties. For more information, contact your Bank or "
        "MorgiHome support.",
        styles['SmallEnglish']
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
