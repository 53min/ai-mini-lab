"""fp32 비트 패턴 -> 값 디코딩 (수도코드의 실행 가능한 버전) + numpy 대조.

사용법:
    python decode_fp32.py                  # 기본 (-126 규칙)
    python decode_fp32.py --subnormal-exp -127   # 완료 기준 질문: -127로 바꾸면?
"""
import argparse
import math

import numpy as np


def bit_2_exponent(bits8: str) -> int:
    # 비트 문자열을 부호 없는 정수로
    return int(bits8, 2)


def bit_2_mantissa(bits23: str) -> float:
    # 첫 비트부터 2^-1, 2^-2, ... 를 곱해 더함
    return sum(int(c) * 2.0 ** -(i + 1) for i, c in enumerate(bits23))


def decode_fp32(bit: str, subnormal_exp: int = -126) -> float:
    sign = 1.0 if bit[0] == "0" else -1.0

    if bit[1:9] == "11111111":
        if bit[9:] == "0" * 23:
            return sign * math.inf
        return math.nan

    if bit[1:9] == "00000000":
        if bit[9:] == "0" * 23:
            return sign * 0.0
        return sign * 2.0 ** subnormal_exp * bit_2_mantissa(bit[9:])  # <- 수도코드에서 sign이 빠졌던 줄

    return sign * 2.0 ** (bit_2_exponent(bit[1:9]) - 127) * (1 + bit_2_mantissa(bit[9:]))


# ---------------- 보조: 대조용 유틸 ----------------
def to_bits(u32: int) -> str:
    return format(u32, "032b")


def numpy_ref(u32: int) -> float:
    return float(np.array([u32], dtype=np.uint32).view(np.float32)[0])


def same(a: float, b: float) -> bool:
    # NaN끼리는 == 가 False 이므로 따로, -0/+0 은 부호까지 비교
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    return a == b and math.copysign(1, a) == math.copysign(1, b)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--subnormal-exp", type=int, default=-126)
    p.add_argument("--n", type=int, default=100_000)
    args = p.parse_args()
    dec = lambda u: decode_fp32(to_bits(u), args.subnormal_exp)

    print("== 예측 표 ==")
    for u in [0xBF400000, 0x00800000, 0x00000001, 0x7F800000, 0x7FC00000, 0x80000000, 0x807FFFFF]:
        a, r = dec(u), numpy_ref(u)
        print(f"{u:#010x}  mine={a!r:<26} numpy={r!r:<26} {'OK' if same(a, r) else 'FAIL'}")

    print("\n== 정규/비정규 경계 ==")
    hi_sub, lo_norm = dec(0x007FFFFF), dec(0x00800000)
    print(f"0x007FFFFF = {hi_sub!r}")
    print(f"0x00800000 = {lo_norm!r}")
    print(f"차이 = {lo_norm - hi_sub!r}  (2^-149 = {2.0**-149!r})")
    print(f"비정규 간격 = {dec(0x00000002) - dec(0x00000001)!r}")

    rng = np.random.default_rng(0)
    xs = rng.integers(0, 2**32, args.n, dtype=np.uint64)
    fails = [int(u) for u in xs if not same(dec(int(u)), numpy_ref(int(u)))]
    print(f"\n무작위 {args.n}개 불일치: {len(fails)}")


if __name__ == "__main__":
    main()
