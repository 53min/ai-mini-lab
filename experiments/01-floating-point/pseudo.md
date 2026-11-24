```text
def bit_2_exponent(8bits):
    return bits_2_integer(8bits) # 단순 비트 정수로 바꿔주는거(10진법)

def bit_2_mantissa(23bits):
    return bits_2_fraction(23bits) # 첫 비트부터 2의 -제곱 줄어들면서 다하는 거

def decode_fp32(bit):
    if bit[0] == 0:
        sign = +1
    else:
        sign = -1

    if bit[1:9] == 11111111:
        if bit[9:] == 00000000000000000000000:
            return sign * 'inf'
        else: 
            return 'NaN'

    if bit[1:9] == 00000000:
        if bit[9:] == 00000000000000000000000:
            return sign * 0
        else:
            return sign * 2^(-126) * (bit_2_mantissa(bit[9:]))

    value = 2^(bit_2_exponent(bit[1:9])-127) * (1+bit_2_mantissa(bit[9:]))
    return sign * value
```