from decimal import Decimal, getcontext

ctx = getcontext()
value = 110936145826700.27
print('context precision', ctx.prec)
print('value', value, type(value))

d = ctx.create_decimal_from_float(value)
print('decimal from float', d)
try:
    q = d.quantize(Decimal('0.01'))
    print('quantized', q)
except Exception as e:
    print('error', type(e), e)
