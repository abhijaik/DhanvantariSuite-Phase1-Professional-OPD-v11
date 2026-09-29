import io
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
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
        "timing": "Timing (M-A-N)",
        "freq": "Frequency",
        "duration": "Duration",
        "food_relation": "Food Relation",
        "instructions": "Instructions",
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
        "timing": "समय (सुबह-दोपहर-रात)",
        "freq": "बारंबारता",
        "duration": "अवधि",
        "food_relation": "भोजन संबंध",
        "instructions": "निर्देश",
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
        "timing": "वेळ (सकाळ-दुपार-रात्र)",
        "freq": "वारंवारता",
        "duration": "कालावधी",
        "food_relation": "जेवणासंबंधी",
        "instructions": "सूचना",
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

    def generate_prescription_pdf(self, consultation: Consultation, patient: Patient, language: str = "en", doctor=None, clinic_settings=None) -> bytes:
        lang = language if language in TRANSLATIONS else "en"
        t = TRANSLATIONS[lang]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        title_style, header_style, body_style, bold_style = self._get_styles()

        styles = getSampleStyleSheet()
        doc_name_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#0F172A'))
        doc_sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.HexColor('#475569'))
        right_title = ParagraphStyle('RightTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=2, textColor=colors.HexColor('#0D9488'))
        right_sub = ParagraphStyle('RightSub', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, alignment=2, textColor=colors.HexColor('#475569'))
        section_heading = ParagraphStyle('SecHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.HexColor('#0F766E'))

        # Resolve Doctor and Clinic details
        doc_name = getattr(doctor, 'full_name', None) or "Dr. Vivek Singh"
        if not doc_name.lower().startswith("dr.") and not doc_name.lower().startswith("dr "):
            doc_name = f"Dr. {doc_name}"
        doc_designation = "MBBS, MD - Consultant Physician"

        clinic_name = getattr(clinic_settings, 'clinic_name', None) or "DHANVANTARI CLINIC & HEALTHCARE"
        clinic_address = getattr(clinic_settings, 'clinic_address', None) or "Main Branch, Local Area"
        clinic_phone = getattr(clinic_settings, 'phone', None) or "+91 98765 43210"
        clinic_email = getattr(clinic_settings, 'email', None) or "contact@dhanvantari.local"

        story = []

        # 1. Doctor & Clinic Header Table (Side-by-side)
        doc_info = [
            Paragraph(f"<b>{doc_name}</b>", doc_name_style),
            Paragraph(f"{doc_designation}", doc_sub_style),
        ]
        if getattr(clinic_settings, 'license_number', None):
            doc_info.append(Paragraph(f"Reg/Lic: {clinic_settings.license_number}", doc_sub_style))

        clinic_info = [
            Paragraph(f"<b>{clinic_name}</b>", right_title),
            Paragraph(f"{clinic_address}", right_sub),
            Paragraph(f"Ph: {clinic_phone} | Email: {clinic_email}", right_sub),
        ]
        
        header_table = Table([[doc_info, clinic_info]], colWidths=[270, 270])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0D9488'), spaceBefore=2, spaceAfter=8))

        # 2. Patient details bar
        p_row1 = [
            Paragraph(f"<b>{t['patient_name']}</b> {patient.full_name}", body_style),
            Paragraph(f"<b>{t['patient_no']}</b> {patient.patient_number}", body_style),
            Paragraph(f"<b>{t['date']}</b> {consultation.created_at.strftime('%d-%b-%Y %I:%M %p')}", body_style)
        ]
        p_row2 = [
            Paragraph(f"<b>Age / Sex:</b> {patient.age} Yrs / {patient.gender}", body_style),
            Paragraph(f"<b>{t['mobile']}</b> {patient.mobile_normalized}", body_style),
            Paragraph(f"<b>Visit Type:</b> {consultation.consultation_type or 'General OPD'}", body_style)
        ]
        patient_table = Table([p_row1, p_row2], colWidths=[200, 170, 170])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 8))

        # 3. Vitals block (if any recorded)
        vitals_list = []
        if consultation.blood_pressure:
            vitals_list.append(f"<b>BP:</b> {consultation.blood_pressure} mmHg")
        if consultation.weight:
            vitals_list.append(f"<b>Weight:</b> {consultation.weight} kg")
        if consultation.height:
            vitals_list.append(f"<b>Height:</b> {consultation.height} cm")
        if getattr(consultation, 'bmi', None):
            vitals_list.append(f"<b>BMI:</b> {consultation.bmi}")
        if consultation.pulse_rate:
            vitals_list.append(f"<b>Pulse:</b> {consultation.pulse_rate} bpm")
        if consultation.temperature:
            vitals_list.append(f"<b>Temp:</b> {consultation.temperature} °F")
        if getattr(consultation, 'spo2', None):
            vitals_list.append(f"<b>SpO2:</b> {consultation.spo2}%")
        if getattr(consultation, 'respiratory_rate', None):
            vitals_list.append(f"<b>Resp:</b> {consultation.respiratory_rate}/min")

        if vitals_list:
            v_cell = Paragraph(" &nbsp; | &nbsp; ".join(vitals_list), body_style)
            v_table = Table([[Paragraph("<b>Vitals:</b>", bold_style), v_cell]], colWidths=[55, 485])
            v_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
                ('PADDING', (0,0), (-1,-1), 4),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(v_table)
            story.append(Spacer(1, 8))

        # 4. Complaints, Diagnosis & Notes
        cd_data = []
        if consultation.symptoms:
            cd_data.append([
                Paragraph("<b>Symptoms:</b>", bold_style),
                Paragraph(", ".join(consultation.symptoms), body_style)
            ])
        if consultation.diagnosis:
            cd_data.append([
                Paragraph("<b>Diagnosis:</b>", bold_style),
                Paragraph(f"<b><font color='#0F766E'>{consultation.diagnosis}</font></b>", body_style)
            ])
        if cd_data:
            cd_table = Table(cd_data, colWidths=[75, 465])
            cd_table.setStyle(TableStyle([
                ('PADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(cd_table)
            story.append(Spacer(1, 8))

        # 5. Rx Prescription Table
        story.append(Paragraph(f"<b><font size=14 color='#0D9488'>Rx</font> <font size=10 color='#334155'>{t['rx']}</font></b>", section_heading))
        story.append(Spacer(1, 4))

        rx_data = [[
            Paragraph("<b>#</b>", bold_style),
            Paragraph(f"<b>{t['medicine']}</b>", bold_style),
            Paragraph(f"<b>{t.get('timing', 'Timing (M-A-N)')}</b>", bold_style),
            Paragraph(f"<b>{t['duration']}</b>", bold_style),
            Paragraph(f"<b>{t.get('food_relation', 'Food Relation')}</b>", bold_style),
            Paragraph(f"<b>{t.get('instructions', 'Instructions')}</b>", bold_style)
        ]]

        for idx, item in enumerate(consultation.prescription, start=1):
            timing = getattr(item, 'dosage', '') or '-'
            duration = getattr(item, 'duration', '') or '-'
            relation = getattr(item, 'food_relation', '') or 'After Food'
            instructions = getattr(item, 'instructions', '') or '-'
            rx_data.append([
                Paragraph(str(idx), body_style),
                Paragraph(f"<b>{item.medicine_name}</b>", body_style),
                Paragraph(timing, body_style),
                Paragraph(duration, body_style),
                Paragraph(relation, body_style),
                Paragraph(instructions, body_style)
            ])

        rx_table = Table(rx_data, colWidths=[25, 175, 85, 75, 90, 90])
        rx_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F766E')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,0), (3,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(rx_table)
        story.append(Spacer(1, 10))

        # 6. Advice / Notes & Follow-up
        if consultation.notes:
            story.append(Table([[
                Paragraph("<b>Advice / Notes:</b>", bold_style),
                Paragraph(consultation.notes, body_style)
            ]], colWidths=[90, 450], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 2)]))
            story.append(Spacer(1, 5))

        if consultation.follow_up_date:
            story.append(Table([[
                Paragraph("<b>Follow-up Date:</b>", bold_style),
                Paragraph(f"<b><font color='#0D9488'>{consultation.follow_up_date.strftime('%d-%b-%Y')}</font></b>", body_style)
            ]], colWidths=[90, 450], style=[('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 2)]))
            story.append(Spacer(1, 10))

        # 7. Signature Block
        story.append(Spacer(1, 20))
        sig_data = [
            [Paragraph("", body_style), Paragraph("____________________________________", right_sub)],
            [Paragraph("", body_style), Paragraph(f"<b>{doc_name}</b>", right_sub)],
            [Paragraph("", body_style), Paragraph(f"<font size=8 color='#64748B'>{doc_designation}</font>", right_sub)],
        ]
        sig_table = Table(sig_data, colWidths=[300, 240])
        sig_table.setStyle(TableStyle([
            ('PADDING', (0,0), (-1,-1), 1),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ]))
        story.append(sig_table)

        # 8. Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=15, spaceAfter=4))
        story.append(Paragraph(
            "<font size=7 color='#94A3B8'><i>This is an electronically generated prescription via Dhanvantari Clinic ERP. Please keep for your medical records.</i></font>",
            ParagraphStyle('Footer', parent=styles['Normal'], alignment=1)
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
