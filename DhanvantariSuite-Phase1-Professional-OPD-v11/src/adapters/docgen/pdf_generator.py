import io
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.domain.models.invoice import Invoice
from src.domain.models.consultation import Consultation
from src.domain.models.patient import Patient
from src.domain.ports.doc_gen_port import DocGenPort

# Dictionary of translations for Hindi, Marathi, and English
TRANSLATIONS = {
    "en": {
        "invoice_title": "INVOICE / RECEIPT",
        "prescription_title": "MEDICAL PRESCRIPTION",
        "invoice_no": "Invoice No:",
        "date": "Date:",
        "patient_name": "Patient Name:",
        "patient_no": "Patient No:",
        "mobile": "Mobile:",
        "item_desc": "Description",
        "qty": "Qty",
        "price": "Price",
        "tax": "Tax",
        "total": "Total",
        "subtotal": "Subtotal:",
        "discount": "Discount:",
        "grand_total": "Grand Total:",
        "payment_mode": "Payment Mode:",
        "payment_status": "Status:",
        "rx": "Rx (Prescription Details):",
        "medicine": "Medicine Name",
        "dosage": "Dosage",
        "freq": "Frequency",
        "duration": "Duration",
        "notes": "Doctor Notes:"
    },
    "hi": {
        "invoice_title": "चालान / रसीद",
        "prescription_title": "चिकित्सा पर्चा",
        "invoice_no": "पर्ची संख्या:",
        "date": "दिनांक:",
        "patient_name": "मरीज का नाम:",
        "patient_no": "मरीज संख्या:",
        "mobile": "मोबाइल:",
        "item_desc": "विवरण",
        "qty": "मात्रा",
        "price": "दर",
        "tax": "कर",
        "total": "कुल",
        "subtotal": "उप-योग:",
        "discount": "छूट:",
        "grand_total": "कुल राशि:",
        "payment_mode": "भुगतान का प्रकार:",
        "payment_status": "स्थिति:",
        "rx": "दवा का विवरण (Rx):",
        "medicine": "दवा का नाम",
        "dosage": "खुराक",
        "freq": "बारंबारता",
        "duration": "अवधि",
        "notes": "डॉक्टर की टिप्पणी:"
    },
    "mr": {
        "invoice_title": "देयक / पावती",
        "prescription_title": "औषधोपचार पत्रक",
        "invoice_no": "देयक क्रमांक:",
        "date": "दिनांक:",
        "patient_name": "रुग्णाचे नाव:",
        "patient_no": "रुग्ण क्रमांक:",
        "mobile": "मोबाईल:",
        "item_desc": "तपशील",
        "qty": "प्रमाण",
        "price": "दर",
        "tax": "कर",
        "total": "एकूण",
        "subtotal": "उप-एकूण:",
        "discount": "सवलत:",
        "grand_total": "एकूण रक्कम:",
        "payment_mode": "पैसे भरण्याची पद्धत:",
        "payment_status": "स्थिती:",
        "rx": "औषधोपचार तपशील (Rx):",
        "medicine": "औषधाचे नाव",
        "dosage": "मात्रा",
        "freq": "वारंवारता",
        "duration": "कालावधी",
        "notes": "डॉक्टरची नोंद:"
    }
}

class PDFGeneratorAdapter(DocGenPort):
    def __init__(self):
        # Register a unicode-compliant font if available, else fall back to Helvetica
        # We look for Gargi or another standard Devanagari font in standard paths
        self.font_name = "Helvetica"
        devanagari_paths = [
            "C:\\Windows\\Fonts\\gargi.ttf",
            "C:\\Windows\\Fonts\\arialuni.ttf",
            "C:\\Windows\\Fonts\\Kokila.ttf"
        ]
        for path in devanagari_paths:
            try:
                import os
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont("Devanagari", path))
                    self.font_name = "Devanagari"
                    break
            except Exception:
                pass

    def _get_styles(self):
        styles = getSampleStyleSheet()
        # Add custom paragraph styles supporting unicode font
        title_style = ParagraphStyle(
            name="InvoiceTitle",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#2C3E50"),
            alignment=1, # Centered
            spaceAfter=15
        )
        header_style = ParagraphStyle(
            name="SectionHeader",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#2C3E50"),
            spaceBefore=10,
            spaceAfter=10
        )
        body_style = ParagraphStyle(
            name="InvoiceBody",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=10,
            leading=12
        )
        bold_style = ParagraphStyle(
            name="InvoiceBodyBold",
            parent=styles["Normal"],
            fontName=self.font_name + "-Bold" if self.font_name == "Helvetica" else self.font_name,
            fontSize=10,
            leading=12
        )
        return title_style, header_style, body_style, bold_style

    def generate_invoice_pdf(self, invoice: Invoice, patient: Patient, language: str) -> bytes:
        lang = language if language in TRANSLATIONS else "en"
        t = TRANSLATIONS[lang]
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        
        title_style, header_style, body_style, bold_style = self._get_styles()
        story = []

        # 1. Title
        story.append(Paragraph(t["invoice_title"], title_style))
        story.append(Spacer(1, 10))

        # 2. Metadata / Patient Details
        metadata = [
            [Paragraph(f"<b>{t['invoice_no']}</b> {invoice.invoice_number}", body_style), 
             Paragraph(f"<b>{t['patient_no']}</b> {patient.patient_number}", body_style)],
            [Paragraph(f"<b>{t['date']}</b> {invoice.created_at.strftime('%Y-%m-%d')}", body_style), 
             Paragraph(f"<b>{t['patient_name']}</b> {patient.full_name}", body_style)],
            [Paragraph(f"<b>{t['payment_mode']}</b> {invoice.payment_mode}", body_style), 
             Paragraph(f"<b>{t['mobile']}</b> {patient.mobile_normalized}", body_style)]
        ]
        
        meta_table = Table(metadata, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # 3. Invoice Items Table
        table_data = [[
            Paragraph(f"<b>{t['item_desc']}</b>", body_style),
            Paragraph(f"<b>{t['qty']}</b>", body_style),
            Paragraph(f"<b>{t['price']}</b>", body_style),
            Paragraph(f"<b>{t['tax']}</b>", body_style),
            Paragraph(f"<b>{t['total']}</b>", body_style)
        ]]
        
        for item in invoice.items:
            table_data.append([
                Paragraph(item.description, body_style),
                Paragraph(str(item.quantity), body_style),
                Paragraph(f"{item.unit_price:.2f}", body_style),
                Paragraph(f"{item.tax_amount:.2f} ({item.tax_rate}%)", body_style),
                Paragraph(f"{item.total:.2f}", body_style)
            ])

        items_table = Table(table_data, colWidths=[220, 50, 80, 110, 80])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 15))

        # 4. Totals Calculation Table
        totals_data = [
            [Paragraph("", body_style), Paragraph("<b>Consultation Charges:</b>", body_style), Paragraph(f"{invoice.consultation_charges:.2f}", body_style)],
            [Paragraph("", body_style), Paragraph("<b>Medicine Charges:</b>", body_style), Paragraph(f"{invoice.medicine_charges:.2f}", body_style)],
            [Paragraph("", body_style), Paragraph("<b>Lab Charges:</b>", body_style), Paragraph(f"{invoice.lab_charges:.2f}", body_style)],
            [Paragraph("", body_style), Paragraph(f"<b>{t['subtotal']}</b>", body_style), Paragraph(f"{invoice.subtotal:.2f}", body_style)],
            [Paragraph("", body_style), Paragraph(f"<b>{t['discount']}</b>", body_style), Paragraph(f"{invoice.discount_amount:.2f}", body_style)],
            [Paragraph("", body_style), Paragraph(f"<b>{t['grand_total']}</b>", body_style), Paragraph(f"<b>{invoice.total_amount:.2f}</b>", body_style)],
            [Paragraph("", body_style), Paragraph("<b>Amount Paid:</b>", body_style), Paragraph(f"<b>{invoice.amount_paid:.2f}</b>", body_style)],
            [Paragraph("", body_style), Paragraph("<b>Amount Due:</b>", body_style), Paragraph(f"<b>{invoice.amount_due:.2f}</b>", body_style)],
            [Paragraph("", body_style), Paragraph("<b>Payment Status:</b>", body_style), Paragraph(f"<b>{invoice.payment_status.value}</b>", body_style)],
        ]
        totals_table = Table(totals_data, colWidths=[320, 120, 100])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('PADDING', (0,0), (-1,-1), 3),
            ('LINEABOVE', (1,5), (-1,5), 1, colors.HexColor("#2C3E50")),
            ('LINEABOVE', (1,6), (-1,6), 0.5, colors.HexColor("#A0AEC0")),
        ]))
        story.append(totals_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_prescription_pdf(self, consultation: Consultation, patient: Patient, language: str) -> bytes:
        lang = language if language in TRANSLATIONS else "en"
        t = TRANSLATIONS[lang]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        
        title_style, header_style, body_style, bold_style = self._get_styles()
        story = []

        # 1. Clinic Letterhead Header
        story.append(Paragraph("<b><font size=16 color='#2C3E50'>DHANVANTARI CLINIC SUITE</font></b>", title_style))
        story.append(Paragraph("<font size=9 color='#7F8C8D'>Main Branch, Local Area | Tel: +91 98765 43210 | Email: contact@dhanvantari.local</font>", title_style))
        story.append(Paragraph(f"<b><font size=11 color='#34495E'>{t['prescription_title']}</font></b>", title_style))
        story.append(Spacer(1, 10))

        # 2. Patient details
        metadata = [
            [Paragraph(f"<b>{t['patient_name']}</b> {patient.full_name}", body_style),
             Paragraph(f"<b>{t['date']}</b> {consultation.created_at.strftime('%Y-%m-%d')}", body_style)],
            [Paragraph(f"<b>{t['patient_no']}</b> {patient.patient_number}", body_style),
             Paragraph(f"<b>{t['mobile']}</b> {patient.mobile_normalized}", body_style)]
        ]
        meta_table = Table(metadata, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # 3. Symptoms, Diagnosis & Vitals
        story.append(Paragraph(f"<b>{t['notes']}</b>", header_style))
        if getattr(consultation, 'consultation_type', None):
            ctype_text = f"<b>Consultation Type:</b> {consultation.consultation_type}"
            if getattr(consultation, 'consultation_subtype', None):
                ctype_text += f" | <b>Sub-Type:</b> {consultation.consultation_subtype}"
            story.append(Paragraph(ctype_text, body_style))
            story.append(Spacer(1, 5))
            
        story.append(Paragraph(f"<b>Symptoms:</b> {', '.join(consultation.symptoms)}", body_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Diagnosis:</b> {consultation.diagnosis}", body_style))
        story.append(Spacer(1, 8))

        # Vitals block
        vitals_list = []
        if consultation.blood_pressure:
            vitals_list.append(f"BP: {consultation.blood_pressure}")
        if consultation.weight:
            vitals_list.append(f"Weight: {consultation.weight} kg")
        if consultation.height:
            vitals_list.append(f"Height: {consultation.height} cm")
        if getattr(consultation, 'bmi', None):
            vitals_list.append(f"BMI: {consultation.bmi}")
        if consultation.temperature:
            vitals_list.append(f"Temp: {consultation.temperature} °F")
        if consultation.pulse_rate:
            vitals_list.append(f"Pulse: {consultation.pulse_rate} bpm")
        if getattr(consultation, 'spo2', None):
            vitals_list.append(f"SpO2: {consultation.spo2}%")
        if getattr(consultation, 'respiratory_rate', None):
            vitals_list.append(f"Resp Rate: {consultation.respiratory_rate} /min")
            
        if vitals_list:
            story.append(Paragraph(f"<b>Vitals:</b> {', '.join(vitals_list)}", body_style))
            story.append(Spacer(1, 15))

        # 4. Rx details table
        story.append(Paragraph(f"<b>{t['rx']}</b>", header_style))
        
        rx_data = [[
            Paragraph(f"<b>{t['medicine']}</b>", body_style),
            Paragraph(f"<b>{t['dosage']}</b>", body_style),
            Paragraph(f"<b>{t['freq']}</b>", body_style),
            Paragraph(f"<b>{t['duration']}</b>", body_style),
            Paragraph(f"<b>Relation</b>", body_style)
        ]]
        
        for item in consultation.prescription:
            relation = getattr(item, 'food_relation', '') or 'After Food'
            instructions = getattr(item, 'instructions', '') or ''
            med_text = f"<b>{item.medicine_name}</b>"
            if instructions:
                med_text += f"<br/><font size=8 color='#7F8C8D'>Instructions: {instructions}</font>"
            rx_data.append([
                Paragraph(med_text, body_style),
                Paragraph(item.dosage, body_style),
                Paragraph(item.frequency, body_style),
                Paragraph(item.duration, body_style),
                Paragraph(relation, body_style)
            ])

        rx_table = Table(rx_data, colWidths=[180, 80, 100, 90, 90])
        rx_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
        ]))
        story.append(rx_table)
        story.append(Spacer(1, 15))

        if consultation.notes:
            story.append(Paragraph(f"<b>Instructions / Notes:</b> {consultation.notes}", body_style))
            story.append(Spacer(1, 10))

        if consultation.follow_up_date:
            story.append(Paragraph(f"<b>Follow-up Date:</b> {consultation.follow_up_date.strftime('%Y-%m-%d')}", bold_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
