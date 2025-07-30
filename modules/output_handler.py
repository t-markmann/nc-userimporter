import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
import qrcode
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

def generate_qr_code(data, output_dir, filename):
    """
    Generates a QR code based on provided data and saves it as an image file.

    Args:
        data (str): The data to encode in the QR code.
        output_dir (str): The directory where the QR code image will be saved.
        filename (str): The name of the QR code image file (without extension).

    Returns:
        str: The full path to the saved QR code image.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code image as a .jpg file
    img_path = os.path.join(output_dir, f"{filename}.jpg")
    img.save(img_path)
    
    # Clear the QR object for reuse
    qr.clear()
    
    return img_path

nclogo = "assets/Nextcloud_Logo.jpg"  # Nextcloud logo
im = Image(nclogo, 150, 106)

def generate_pdf(user_data, qr_code_path, output_filepath, config_ncUrl, lang, multi_user=False):
    """
    Generates a PDF for either a single user or multiple users.
    
    Args:
        user_data (dict): User data, either for a single user or a list of users in multi-user mode.
        qr_code_path (str): The path to the QR code image (for single user mode).
        output_filepath (str): The output path for the generated PDF.
        config_ncUrl (str): The Nextcloud URL.
        lang (dict): The dictionary containing translations for output text.
        multi_user (bool): Whether to generate a multi-user PDF.
    """
    # Use DejaVuSans for default font
    font_path = os.path.join(os.path.dirname(__file__), '../assets/IBMPlexSans-Regular.ttf')
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('IBMPlexSans', font_path))
            custom_font = 'IBMPlexSans'
        except Exception:
            custom_font = 'Helvetica'
    else:
        custom_font = 'Helvetica'

    doc = SimpleDocTemplate(output_filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName=custom_font))
    styles['Normal'].fontName = custom_font
    styles['Heading1'].fontName = custom_font

    if multi_user:
        for user in user_data['users']:
            _build_single_user_section(story, styles, user, user.get('qr_code_path'), config_ncUrl, lang)
            story.append(PageBreak())  # Add page break between users
    else:
        _build_single_user_section(story, styles, user_data, qr_code_path, config_ncUrl, lang)

    doc.build(story)

def _build_single_user_section(story, styles, user_data, qr_code_path, config_ncUrl, lang):
    """
    Helper function to build the PDF content for a single user.

    Args:
        story (list): The list of elements that make up the PDF content.
        styles (StyleSheet): Styles for formatting the PDF.
        user_data (dict): Contains 'username' and 'password' for the user.
        qr_code_path (str): Path to the generated QR code image.
        config_ncUrl (str): The Nextcloud URL for the user.
        lang (dict): The dictionary containing translations for output text.
    """
    
    # Add Nextcloud logo at the top of the page
    story.append(im)
    story.append(Spacer(1, 12))
    
    # Greeting and account creation message
    displayname = user_data.get('displayname', '').strip()  # Entferne Leerzeichen
    if not displayname:
        displayname = user_data['username']  # Fallback auf den Benutzernamen

    # Add greeting
    ptext = f"<font size=14>{lang.get('output_handler_greeting', 'Missing translation string for: output_handler_greeting')} {displayname},</font>"
    story.append(Paragraph(ptext, styles["Justify"]))
    story.append(Spacer(1, 12))

    # Account creation message
    ptext = f"<font size=14>{lang.get('output_handler_account_created', 'Missing translation string for: output_handler_account_created')}</font>"
    story.append(Paragraph(ptext, styles["Justify"]))
    story.append(Spacer(1, 12))

    # Login instructions
    ptext = f"<font size=14>{lang.get('output_handler_login_instructions', 'Missing translation string for: output_handler_login_instructions')}</font>"
    story.append(Paragraph(ptext, styles["Normal"]))
    story.append(Spacer(1, 24))

    # Nextcloud URL
    ptext = f"<font size=14>{lang.get('output_handler_nc_url', 'Missing translation string for: output_handler_nc_url')}: {config_ncUrl}</font>"
    story.append(Paragraph(ptext, styles["Normal"]))
    story.append(Spacer(1, 24))

    # Username (box)
    uname_table = Table([[user_data['username']]], colWidths=[250], rowHeights=[30])
    uname_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('FONTNAME', (0,0), (-1,-1), 'Courier'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))
    ptext = f"<font size=14>{lang.get('output_handler_username', 'Username')}:</font>"
    story.append(Paragraph(ptext, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(uname_table)
    story.append(Spacer(1, 24))

    # Password (box)
    pwd_table = Table([[user_data['password']]], colWidths=[250], rowHeights=[30])
    pwd_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('FONTNAME', (0,0), (-1,-1), 'Courier'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))
    ptext = f"<font size=14>{lang.get('output_handler_password', 'Password')}:</font>"
    story.append(Paragraph(ptext, styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(pwd_table)
    story.append(Spacer(1, 24))

    # QR Code
    if qr_code_path and os.path.exists(qr_code_path):
        ptext = f"<font size=14>{lang.get('output_handler_qr_code_alternative', 'Missing translation string for: output_handler_qr_code_alternative')}</font>"
        story.append(Paragraph(ptext, styles["Normal"]))
        story.append(Spacer(1, 24))
        # Insert the QR code image
        story.append(Image(qr_code_path, 150, 150))

    story.append(Spacer(1, 24))

def _build_single_user_pdf(story, styles, user_data, qr_code_path, nclogo, config_ncUrl, lang):
    """
    Builds the PDF structure for a single user, including the Nextcloud logo.

    Args:
        story (list): The list of elements that make up the PDF content.
        styles (StyleSheet): Styles for formatting the PDF.
        user_data (dict): Contains 'username' and 'password' for the user.
        qr_code_path (str): Path to the generated QR code image.
        nclogo (str): Path to the Nextcloud logo.
        config_ncUrl (str): The Nextcloud URL for the user.
        lang (dict): The dictionary containing translations for output text.
    """
    _build_single_user_section(story, styles, user_data, qr_code_path, config_ncUrl, lang)
