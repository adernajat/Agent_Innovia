"""
utils/pdf_generator.py
======================
Génération de PDF pour les commandes fournisseur
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path
import os

def generer_pdf_commande(commande_data: dict, filename: str = None) -> str:
    """
    Génère un PDF pour une commande fournisseur
    
    Args:
        commande_data: Dictionnaire contenant les données de la commande
        filename: Nom du fichier (optionnel)
    
    Returns:
        Chemin du fichier PDF généré
    """
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"commande_{commande_data['matiere']}_{timestamp}.pdf"
    
    # Créer le dossier data/pdfs s'il n'existe pas
    pdf_dir = Path(__file__).parent.parent / "data" / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = pdf_dir / filename
    
    # Création du document PDF
    doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                           topMargin=20*mm, bottomMargin=20*mm,
                           leftMargin=20*mm, rightMargin=20*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a5f'),
        spaceAfter=30,
        alignment=1  # Centre
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Contenu du PDF
    story = []
    
    # Titre
    story.append(Paragraph("BON DE COMMANDE FOURNISSEUR", title_style))
    story.append(Spacer(1, 12))
    
    # En-tête avec informations générales
    story.append(Paragraph(f"Référence: CMD-{datetime.now().strftime('%Y%m%d')}-{commande_data.get('id', '001')}", header_style))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Spacer(1, 12))
    
    # Informations fournisseur
    story.append(Paragraph("INFORMATIONS FOURNISSEUR", header_style))
    supplier_info = [
        ["Nom:", commande_data.get('fournisseur_nom', 'N/A')],
        ["Contact:", commande_data.get('fournisseur_contact', 'N/A')],
        ["Téléphone:", commande_data.get('fournisseur_telephone', 'N/A')],
        ["Email:", commande_data.get('fournisseur_email', 'N/A')]
    ]
    
    supplier_table = Table(supplier_info, colWidths=[60*mm, 100*mm])
    supplier_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(supplier_table)
    story.append(Spacer(1, 12))
    
    # Détails de la commande
    story.append(Paragraph("DÉTAILS DE LA COMMANDE", header_style))
    
    commande_info = [
        ["Matière:", commande_data.get('matiere', 'N/A')],
        ["Quantité:", f"{commande_data.get('quantite', 0):,.0f} unités"],
        ["Prix unitaire:", f"{commande_data.get('prix_unitaire', 0):,.2f} €"],
        ["Prix total:", f"{commande_data.get('prix_total', 0):,.2f} €"],
        ["Délai de livraison:", f"{commande_data.get('delai_jours', 0)} jours"],
        ["Livraison prévue:", commande_data.get('date_livraison_prevue', 'N/A')],
        ["Statut:", commande_data.get('statut', 'En attente')]
    ]
    
    commande_table = Table(commande_info, colWidths=[60*mm, 100*mm])
    commande_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(commande_table)
    story.append(Spacer(1, 12))
    
    # Décision IA (si disponible)
    if commande_data.get('decision_ia_id'):
        story.append(Paragraph("DÉCISION IA", header_style))
        ia_info = [
            ["ID Décision:", commande_data.get('decision_ia_id')],
            ["Action suggérée:", commande_data.get('action_ia', 'N/A')],
            ["Justification:", commande_data.get('justification_ia', 'N/A')]
        ]
        
        ia_table = Table(ia_info, colWidths=[60*mm, 100*mm])
        ia_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(ia_table)
        story.append(Spacer(1, 12))
    
    # Pied de page
    story.append(Spacer(1, 20))
    story.append(Paragraph("Conditions générales:", ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold')))
    story.append(Paragraph("1. La livraison est effectuée selon les délais indiqués.", normal_style))
    story.append(Paragraph("2. Le paiement est dû à 30 jours après réception de la facture.", normal_style))
    story.append(Paragraph("3. La marchandise voyage aux risques et périls du destinataire.", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))
    
    # Génération du PDF
    doc.build(story)
    
    return str(filepath)

def generer_pdf_recommandations(recommandations: list, matiere: str, quantite: float) -> str:
    """
    Génère un PDF avec la liste des fournisseurs recommandés
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recommandations_{matiere}_{timestamp}.pdf"
    
    pdf_dir = Path(__file__).parent.parent / "data" / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = pdf_dir / filename
    
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Titre
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, spaceAfter=20)
    story.append(Paragraph(f"Recommandations Fournisseurs - {matiere}", title_style))
    story.append(Paragraph(f"Quantité: {quantite:,.0f} unités", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Tableau des recommandations
    table_data = [["Fournisseur", "Prix Total (€)", "Délai (j)", "Score", "Qualité"]]
    
    for rec in recommandations:
        supplier = rec['fournisseur']
        table_data.append([
            supplier['nom'],
            f"{rec['prix_total']:,.2f}",
            str(rec['delai_jours']),
            f"{rec['score']}/5",
            f"{supplier['qualite']} ★"
        ])
    
    table = Table(table_data, colWidths=[70*mm, 40*mm, 30*mm, 30*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    
    return str(filepath)