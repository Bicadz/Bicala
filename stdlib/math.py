# ================================
# MATH - Math module for Bicala
# ================================
import math as _mathematics_
# Constants
pi = _mathematics_.pi
e = _mathematics_.e
tau = _mathematics_.tau
inf = _mathematics_.inf
nan = _mathematics_.nan
# Root / Pow / Abs
def sqrt(x): return _mathematics_.sqrt(x)
def cbrt(x): return _mathematics_.cbrt(x)
def root(x, n): return x ** (1/n)

def pow(x, y): return _mathematics_.pow(x, y)

def abs(x): return _mathematics_.abs(x)
def fabs(x): return _mathematics_.fabs(x)
# Number Theory
def fact(x):return _mathematics_.factorial(int(x))

def gcd(a, b): return _mathematics_.gcd(a, b)
def lcm(a, b): return abs(a * b) // _mathematics_.gcd(a, b)
# Rounding
def floor(x): return _mathematics_.floor(x)
def ceil(x): return _mathematics_.ceil(x)
def trunc(x): return _mathematics_.trunc(x)

bi_rnd = round
def round(x, n=0): return bi_rnd(x, n)
# Sum
bi_sum = sum
def sum(arr): return bi_sum(arr)
def fsum(arr): return _mathematics_.fsum(arr)
# Log / exp
def log(x, base=None): return _mathematics_.log(x, base) if base else _mathematics_.log(x,10)
def ln(x): return _mathematics_.log(x,_mathematics_.e())
def log10(x): return _mathematics_.log10(x)
def log2(x): return _mathematics_.log2(x)

def log1p(x): return _mathematics_.log1p(x)

def exp(x): return _mathematics_.exp(x)
def expm1(x): return _mathematics_.expm1(x)
# ----------------
# Trigonometry
# ----------------
def sin(x): return _mathematics_.sin(x)
def cos(x): return _mathematics_.cos(x)
def tan(x): return _mathematics_.tan(x)
def asin(x): return _mathematics_.asin(x)
def acos(x): return _mathematics_.acos(x)
def atan(x): return _mathematics_.atan(x)
def atan2(y, x): return _mathematics_.atan2(y, x)

def sinh(x): return _mathematics_.sinh(x)
def cosh(x): return _mathematics_.cosh(x)
def tanh(x): return _mathematics_.tanh(x)
def asinh(x): return _mathematics_.asinh(x)
def acosh(x): return _mathematics_.acosh(x)
def atanh(x): return _mathematics_.atanh(x)
# Geometry
def hypot(x, y): return _mathematics_.hypot(x, y)
def dist(x1, y1, x2, y2): return _mathematics_.hypot(x2 - x1, y2 - y1)
# Angle System
def degrees(x): return _mathematics_.degrees(x)
def radians(x): return _mathematics_.radians(x)
def grad(x): return x * (200 / pi)
# Time Angle
def sec_to_deg(s): return s / 3600
def min_to_deg(m): return m / 60
def hour_to_deg(h): return h * 15

def deg_to_sec(d): return d * 3600
def deg_to_min(d): return d * 60
def deg_to_hour(d): return d / 15
# Floating-point control
def copysign(x, y): return _mathematics_.copysign(x, y)
def frexp(x): return _mathematics_.frexp(x)
def ldexp(x, i): return _mathematics_.ldexp(x, i)
# Checks
def isfinite(x): return _mathematics_.isfinite(x)
def isnan(x): return _mathematics_.isnan(x)
def isinf(x): return _mathematics_.isinf(x)
# Combinatorics
def perm(n,k): return _mathematics_.perm(n,k)
def comb(n,k): return _mathematics_.comb(n,k)
# Extras
def clamp(x, a, b): return max(a, min(b, x))

def sign(x): return (x > 0) - (x < 0)

def neg(x): return -x

def lerp(a, b, t): return a + (b - a) * t