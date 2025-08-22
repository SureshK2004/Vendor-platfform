from decimal import Decimal

def calculate_total_price(service, quantity, pricing_tier_id=None):
    """
    Calculate the total price for a booking including platform fees and taxes
    """
    # Get base price from tier or service
    if pricing_tier_id:
        try:
            tier = service.pricing_tiers.get(id=pricing_tier_id, is_active=True)
            base_price = tier.price
        except PricingTier.DoesNotExist:
            base_price = service.base_price
    else:
        base_price = service.base_price
        
    # Calculate subtotal
    subtotal = base_price * quantity
    
    # Calculate platform fee (15%)
    platform_fee = subtotal * Decimal('0.15')
    
    # Calculate tax (example: 8% sales tax)
    tax_rate = Decimal('0.08')
    tax_amount = subtotal * tax_rate
    
    # Calculate total
    total_amount = subtotal + platform_fee + tax_amount
    
    return {
        'base_price': base_price,
        'subtotal': subtotal,
        'platform_fee': platform_fee,
        'tax_amount': tax_amount,
        'total_amount': total_amount
    }