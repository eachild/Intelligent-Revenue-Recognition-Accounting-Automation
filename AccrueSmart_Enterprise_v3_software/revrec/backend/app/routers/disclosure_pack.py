# backend/app/routers/disclosure_pack.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from datetime import datetime
import os
from typing import List, Dict, Any
import json
from app.schemas import ContractIn, AllocResult
# from app.reporting import summarize_schedules
from app.engine import build_allocation

# Router for disclosure pack endpoint
router = APIRouter(prefix="/reports", tags=["disclosure-pack"])

# Class to generate disclosure pack reports
class DisclosurePackGenerator:
    # Initialize with output directory
    def __init__(self, output_dir: str = "./out"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='Heading1',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        self.styles.add(ParagraphStyle(
            name='Heading2',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue
        ))
        self.styles.add(ParagraphStyle(
            name='Body',
            parent=self.styles['BodyText'],
            fontSize=10,
            spaceAfter=6
        ))
    
    # Generate ASC 606 Revenue from Contracts with Customers disclosure
    def generate_asc_606_disclosure(self, story, contracts: List[Dict]):
        """Generate ASC 606 Revenue from Contracts with Customers disclosure"""
        story.append(Paragraph("ASC 606 - Revenue from Contracts with Customers", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Revenue Disaggregation
        story.append(Paragraph("Revenue Disaggregation", self.styles['Heading2']))
        revenue_data = self._aggregate_revenue_by_category(contracts)
        if revenue_data:
            story.append(self._create_revenue_table(revenue_data))
        
        # Contract Balances Rollforward
        story.append(Paragraph("Contract Balances", self.styles['Heading2']))
        balance_data = self._calculate_contract_balances(contracts)
        if balance_data:
            story.append(self._create_balances_table(balance_data))
        
        # Remaining Performance Obligations
        story.append(Paragraph("Remaining Performance Obligations", self.styles['Heading2']))
        rpo_data = self._calculate_rpo(contracts)
        if rpo_data:
            story.append(self._create_rpo_table(rpo_data))
        
        story.append(PageBreak())
    
    # Generate ASC 842 Leases disclosure
    def generate_asc_842_disclosure(self, story, leases: List[Dict]):
        """Generate ASC 842 Leases disclosure"""
        story.append(Paragraph("ASC 842 - Leases", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        if not leases:
            story.append(Paragraph("No lease contracts identified.", self.styles['Body']))
            story.append(PageBreak())
            return
        
        # Lease Assets and Liabilities
        story.append(Paragraph("Lease Assets and Liabilities", self.styles['Heading2']))
        lease_data = self._aggregate_lease_data(leases)
        story.append(self._create_lease_table(lease_data))
        
        # Lease Expense
        story.append(Paragraph("Lease Expense", self.styles['Heading2']))
        expense_data = self._calculate_lease_expense(leases)
        story.append(self._create_lease_expense_table(expense_data))
        
        story.append(PageBreak())

    # Generate ASC 740 Income Taxes disclosure
    def generate_asc_740_disclosure(self, story, tax_data: Dict):
        """Generate ASC 740 Income Taxes disclosure"""
        story.append(Paragraph("ASC 740 - Income Taxes", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Deferred Tax Assets/Liabilities
        story.append(Paragraph("Deferred Tax Assets and Liabilities", self.styles['Heading2']))
        if tax_data.get('deferred_taxes'):
            story.append(self._create_tax_table(tax_data['deferred_taxes']))
        
        # Tax Provision Reconciliation
        story.append(Paragraph("Income Tax Provision Reconciliation", self.styles['Heading2']))
        if tax_data.get('tax_reconciliation'):
            story.append(self._create_tax_reconciliation_table(tax_data['tax_reconciliation']))
        
        story.append(PageBreak())

    # Generate ASC 718 Stock Compensation disclosure
    def generate_asc_718_disclosure(self, story, compensation_data: Dict):
        """Generate ASC 718 Compensation - Stock Compensation disclosure"""
        story.append(Paragraph("ASC 718 - Stock Compensation", self.styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Stock Option Activity
        story.append(Paragraph("Stock Option Activity", self.styles['Heading2']))
        if compensation_data.get('stock_options'):
            story.append(self._create_stock_option_table(compensation_data['stock_options']))
        
        # Stock-based Compensation Expense
        story.append(Paragraph("Stock-based Compensation Expense", self.styles['Heading2']))
        if compensation_data.get('compensation_expense'):
            story.append(self._create_compensation_expense_table(compensation_data['compensation_expense']))
        
        story.append(PageBreak())

    # Create revenue disaggregation table
    def _create_revenue_table(self, data: List[Dict]) -> Table:
        """Create revenue disaggregation table"""
        headers = ['Revenue Category', 'Current Period', 'Prior Period', 'Variance %']
        table_data = [headers]
        
        for item in data:
            table_data.append([
                item['category'],
                f"${item['current']:,.2f}",
                f"${item['prior']:,.2f}",
                f"{item['variance']:.1f}%"
            ])
        
        table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table

    # Create contract balances table
    def _create_balances_table(self, data: Dict) -> Table:
        """Create contract balances table"""
        headers = ['Balance Type', 'Beginning', 'Additions', 'Recognized', 'Ending']
        table_data = [headers]
        
        for balance_type, amounts in data.items():
            table_data.append([
                balance_type.replace('_', ' ').title(),
                f"${amounts['beginning']:,.2f}",
                f"${amounts['additions']:,.2f}",
                f"${amounts['recognized']:,.2f}",
                f"${amounts['ending']:,.2f}"
            ])
        
        table = Table(table_data, colWidths=[1.5*inch] + [1*inch]*4)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table

    # Create remaining performance obligations table
    def _create_rpo_table(self, data: Dict) -> Table:
        """Create remaining performance obligations table"""
        headers = ['Period', 'Amount']
        table_data = [headers]
        
        for period, amount in data.items():
            table_data.append([period, f"${amount:,.2f}"])
        
        table = Table(table_data, colWidths=[2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table

    # Create lease disclosure table
    def _create_lease_table(self, data: List[Dict]) -> Table:
        """Create lease disclosure table"""
        headers = ['Lease Type', 'Right-of-Use Assets', 'Lease Liabilities', 'Lease Term']
        table_data = [headers]
        
        for lease in data:
            table_data.append([
                lease['type'],
                f"${lease['assets']:,.2f}",
                f"${lease['liabilities']:,.2f}",
                f"{lease['term']} months"
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table

    # Create lease expense table
    def _create_tax_table(self, data: Dict) -> Table:
        """Create deferred taxes table"""
        headers = ['Temporary Difference', 'Deferred Tax Asset', 'Deferred Tax Liability']
        table_data = [headers]
        
        for item, amounts in data.items():
            table_data.append([
                item.replace('_', ' ').title(),
                f"${amounts['asset']:,.2f}" if amounts['asset'] else '-',
                f"${amounts['liability']:,.2f}" if amounts['liability'] else '-'
            ])
        
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table

    # Create stock option activity table
    def _create_stock_option_table(self, data: List[Dict]) -> Table:
        """Create stock option activity table"""
        headers = ['', 'Number of Options', 'Weighted Average Exercise Price']
        table_data = [headers]
        
        for activity in data:
            table_data.append([
                activity['activity_type'],
                f"{activity['options']:,}",
                f"${activity['price']:.2f}"
            ])
        
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        return table

    # Create compensation expense table
    def _aggregate_revenue_by_category(self, contracts: List[Dict]) -> List[Dict]:
        """Aggregate revenue by category for disclosure"""
        # This would integrate with your existing revenue aggregation logic
        # Placeholder implementation
        categories = {
            'Product Sales': {'current': 0, 'prior': 0},
            'Service Revenue': {'current': 0, 'prior': 0},
            'License Fees': {'current': 0, 'prior': 0},
            'Maintenance & Support': {'current': 0, 'prior': 0}
        }
        
        # Aggregate revenue from contracts
        for contract in contracts:
            allocation = build_allocation(contract)
            for po in allocation.allocations:
                category = self._categorize_po(po.description)
                categories[category]['current'] += po.allocated_price
        
        result = []
        for category, amounts in categories.items():
            if amounts['current'] > 0:
                variance = ((amounts['current'] - amounts['prior']) / amounts['prior'] * 100) if amounts['prior'] else 0
                result.append({
                    'category': category,
                    'current': amounts['current'],
                    'prior': amounts['prior'],
                    'variance': variance
                })
        
        return result

    # Categorize performance obligation
    def _categorize_po(self, description: str) -> str:
        """Categorize performance obligation based on description"""
        desc_lower = description.lower()
        if any(word in desc_lower for word in ['device', 'product', 'hardware', 'equipment']):
            return 'Product Sales'
        elif any(word in desc_lower for word in ['service', 'support', 'maintenance']):
            return 'Maintenance & Support'
        elif any(word in desc_lower for word in ['license', 'software', 'subscription']):
            return 'License Fees'
        else:
            return 'Service Revenue'

    # Calculate contract balances
    def _calculate_contract_balances(self, contracts: List[Dict]) -> Dict:
        """Calculate contract balances for disclosure"""
        # Placeholder implementation - integrate with your balance calculation logic
        return {
            'deferred_revenue': {
                'beginning': 100000,
                'additions': 50000,
                'recognized': 30000,
                'ending': 120000
            },
            'contract_assets': {
                'beginning': 15000,
                'additions': 8000,
                'recognized': 5000,
                'ending': 18000
            }
        }

    # Calculate remaining performance obligations
    def _calculate_rpo(self, contracts: List[Dict]) -> Dict:
        """Calculate remaining performance obligations"""
        # Placeholder implementation
        return {
            'Next 12 months': 75000,
            '13-24 months': 45000,
            '25-36 months': 25000,
            'Beyond 36 months': 15000
        }

    # Aggregate lease data
    def _aggregate_lease_data(self, leases: List[Dict]) -> List[Dict]:
        """Aggregate lease data for disclosure"""
        # Placeholder implementation
        return [
            {'type': 'Operating Leases', 'assets': 250000, 'liabilities': 245000, 'term': 60},
            {'type': 'Finance Leases', 'assets': 150000, 'liabilities': 148000, 'term': 48}
        ]

    # Calculate lease expense
    def _calculate_lease_expense(self, leases: List[Dict]) -> List[Dict]:
        """Calculate lease expense for disclosure"""
        # Placeholder implementation
        return [
            {'expense_type': 'Operating Lease Cost', 'amount': 45000},
            {'expense_type': 'Finance Lease Interest', 'amount': 12000},
            {'expense_type': 'Finance Lease Amortization', 'amount': 18000},
            {'expense_type': 'Variable Lease Payments', 'amount': 8000}
        ]

    # Calculate lease expense table
    def generate_disclosure_pack(self, 
                               contracts: List[Dict] = None,
                               leases: List[Dict] = None,
                               tax_data: Dict = None,
                               compensation_data: Dict = None,
                               filename: str = None) -> str:
        """Generate comprehensive disclosure pack PDF"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"disclosure_pack_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=1*inch)
        story = []
        
        # Title Page
        title_style = ParagraphStyle(
            name='Title',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center
        )
        story.append(Paragraph("Financial Statement Disclosures", title_style))
        story.append(Paragraph(f"As of {datetime.now().strftime('%B %d, %Y')}", self.styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Generated by AccrueSmart AI Accounting System", self.styles['Body']))
        story.append(PageBreak())
        
        # Generate disclosures for each standard
        self.generate_asc_606_disclosure(story, contracts or [])
        self.generate_asc_842_disclosure(story, leases or [])
        self.generate_asc_740_disclosure(story, tax_data or {})
        self.generate_asc_718_disclosure(story, compensation_data or {})
        
        # Build PDF
        doc.build(story)
        return filepath

# FastAPI endpoint
@router.post("/disclosure-pack")
async def generate_disclosure_pack(
    contract_ids: List[str] = None,
    include_leases: bool = True,
    include_taxes: bool = True,
    include_compensation: bool = True
):
    """Generate comprehensive disclosure pack PDF"""
    
    try:
        generator = DisclosurePackGenerator()
        
        # Get contracts from repository
        from app.repository import get_many
        contracts = get_many(contract_ids) if contract_ids else []
        
        # Get additional data (placeholders - integrate with your services)
        leases = []
        tax_data = {}
        compensation_data = {}
        
        if include_leases:
            # Integrate with your leases service
            from app.services.leases import get_lease_data
            leases = get_lease_data()  # Implement this in your leases service
        
        if include_taxes:
            # Integrate with your tax service
            from app.services.asc740 import get_tax_disclosure_data
            tax_data = get_tax_disclosure_data()  # Implement this in your tax service
        
        if include_compensation:
            # Integrate with your compensation service
            from app.services.asc718 import get_compensation_data
            compensation_data = get_compensation_data()  # Implement this if you have ASC 718 service
        
        # Generate PDF
        filepath = generator.generate_disclosure_pack(
            contracts=contracts,
            leases=leases,
            tax_data=tax_data,
            compensation_data=compensation_data
        )
        
        return FileResponse(
            filepath,
            media_type='application/pdf',
            filename=os.path.basename(filepath)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating disclosure pack: {str(e)}")