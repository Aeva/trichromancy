
import math
import numpy as np


GAMMA = 2.4

LINEAR_TO_XYZ = np.array([
    [506752.0 / 1228815.0, 87881.0 / 245763.0, 12673.0 / 70218.0],
    [87098.0 / 409605.0, 175762.0 / 245763.0, 12673.0 / 175545.0],
    [7918.0 / 409605.0, 87881.0 / 737289.0, 1001167.0 / 1053270.0]])

XYZ_TO_LINEAR = np.array([
    [12831.0 / 3959.0, -329.0 / 214.0, -1974.0 / 3959.0],
    [-851781.0 / 878810.0, 1648619.0 / 878810.0, 36519.0 / 878810.0],
    [705.0 / 12673.0, -2585.0 / 12673.0, 705.0 / 667.0]])

XYZ_TO_LMS = np.array([
    [0.8190224432164319, 0.3619062562801221, -0.12887378261216414],
    [0.0329836671980271, 0.9292868468965546, 0.03614466816999844],
    [0.048177199566046255, 0.26423952494422764, 0.6335478258136937]])

LMS_TO_OKLAB = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660]])

OKLAB_TO_LMS = np.array([
    [0.99999999845051981432, 0.39633779217376785678, 0.21580375806075880339],
    [1.0000000088817607767, -0.1055613423236563494, -0.063854174771705903402],
    [1.0000000546724109177, -0.089484182094965759684, -1.2914855378640917399]])

LMS_TO_XYZ = np.array([
    [1.2268798733741557, -0.5578149965554813, 0.28139105017721583],
    [-0.04057576262431372, 1.1122868293970594, -0.07171106666151701],
    [-0.07637294974672142, -0.4214933239627914, 1.5869240244272418]])


def sign(scalar):
    if scalar > 0:
        return 1
    if scalar < 0:
        return -1
    else:
        return 0


def sRGB_to_linear(sRGB):
    """
    Convert from sRGB to Linear RGB.
    Adapted from https://www.w3.org/TR/css-color-4/#color-conversion-code
    """

    linear = np.zeros(3)

    for channel, color in enumerate(sRGB):
        abs_color = abs(color)

        if abs_color < 0.04045:
            linear[channel] = color / 12.92
        else:
            linear[channel] = sign(color) * (math.pow((abs_color + 0.055) / 1.055, GAMMA))

    return linear


def linear_2_sRGB(linear):
    """
    Convert from Linear RGB to sRGB.
    Adapted from https://www.w3.org/TR/css-color-4/#color-conversion-code
    """

    sRGB = np.zeros(3)

    for channel, color in enumerate(linear):
        abs_color = abs(color)

        if abs_color > 0.0031308:
            sRGB[channel] = sign(color) * (1.055 * math.pow(abs_color, 1.0 / GAMMA) - 0.055)
        else:
            sRGB[channel] = 12.92 * color

    return sRGB


def linear_to_XYZ(linear):
    """
    Convert from Linear RGB to CIE XYZ.
    Adapted from https://www.w3.org/TR/css-color-4/#color-conversion-code
    """
    return LINEAR_TO_XYZ @ linear


def XYZ_to_linear(xyz):
    """
    Convert from CIE XYZ to Linear RGB.
    Adapted from https://www.w3.org/TR/css-color-4/#color-conversion-code
    """
    return XYZ_TO_LINEAR @ xyz


def XYZ_to_OkLab(xyz):
    """
    Convert from D65-relative CIE XYZ to OKLab.
    Adapted from https://www.w3.org/TR/css-color-4/#color-conversion-code
    """
    lms = np.cbrt(XYZ_TO_LMS @ xyz)
    return LMS_TO_OKLAB @ lms


def OkLab_to_XYZ(oklab):
    """
    Convert from OKLab to D65-relative CIE XYZ.
    Adapted from https://www.w3.org/TR/css-color-4/#color-conversion-code
    """
    lms = np.pow(OKLAB_TO_LMS @ oklab, 3.0)
    return LMS_TO_XYZ @ lms


def OkLab_to_OkLch(oklab):
    """
    Convert from OkLab to OkLch.
    Adapted from https://www.w3.org/TR/css-color-4/#lab-to-lch
    """

    lightness = OkLab[0]
    axis_a = OkLab[1]
    axis_b = OkLab[2]

    axes = np.array([AxisA, AxisB])
    chroma = math.sqrt(np.dot(axes, axes))

    hue = math.degrees(math.atan2(AxisB, AxisA))
    if math.isnan(hue):
        hue = 0.0
    else:
        hue = min(max(hue, -180.0), 180.0)

    return np.array([lightness, chroma, hue])


def OkLch_to_OkLab(oklch):
    """
    Convert from OkLch to OkLab.
    Adapted from https://www.w3.org/TR/css-color-4/#lch-to-lab
    """

    lightness = oklch[0]
    chroma = oklch[1]
    hue = math.radians(oklch[2])

    axis_a = 0.0
    axis_b = 0.0

    # https://www.w3.org/TR/css-color-4/#specifying-oklab-oklch notes that
    # if the lightness is 0, then the resulting color is black, and if the
    # lightness is 1.0, then the resulting color is white.
    if not (lightness == 0.0 or lightness == 1.0):
        axisA = chroma * math.cos(hue)
        axisB = chroma * math.sin(hue)

    return np.array([lightness, axis_a, axis_b])


def sRGB_to_OkLAB(r, g, b):
    sRGB = np.array([r, g, b])
    linear = sRGB_to_linear(sRGB)
    xyz = linear_to_XYZ(linear)
    return XYZ_to_OkLab(xyz)


def OkLAB_to_sRGB(l, a, b):
    oklab = np.array([l, a, b])
    xyz = OkLAB_to_XYZ(oklab)
    linear = XYZ_to_linear(xyz)
    return linear_to_sRGB(linear)


def LinearRGB_to_OkLAB(r, g, b):
    linear = np.array([r, g, b])
    xyz = linear_to_XYZ(linear)
    return XYZ_to_OkLab(xyz)


def OkLAB_to_LinearRGB(l, a, b):
    oklab = np.array([l, a, b])
    xyz = OkLAB_to_XYZ(oklab)
    return XYZ_to_linear(xyz)


def mix(lhs, rhs, alpha):
    """
    Linear interpolation between two scalar values or 1D numpy arrays.
    """
    assert(type(lhs) == type(rhs))
    if type(lhs) == numpy.ndarray:
        assert(lhs.size == rhs.size)
        if type(alpha) != numpy.ndarray:
            alpha = np.array([alpha] * lhs.size)

    span = rhs - lhs
    return rhs * alpha + lhs


def mix_lchab(lhs_oklab, rhs_oklab, alpha, chroma_weight):
    """
    Inspired by "Luminance Preserving Tint" (Clinkscales-Prager 2024-2025, private correspondences).
    The original technique is a lighting method that separates luminance and tint by mixing the former
    in a LAB or LCH color space and the latter in linear RGB color, and the results are combined using
    a special blending parameter.

    The blending method below first performs an ordinary color interpolation in OkLAB space, which is
    also luminance preserving, but has different perceptual characteristics than Clinkscales & Prager's
    method, and lacks their control parameter.  The primaries and the results are then converted to LCH
    space, where a second chroma-only interpolation is used to replace the chroma of the first
    interpolation (with a new blending parameter to control the balance of the two results).  Thus,
    this method is also variably chroma preserving.
    """

    palette_oklab = mix(lhs_oklab, rhs_oklab, alpha)

    if chroma_weight > 0.0:
        lhs_oklch = OkLab_to_OkLch(lhs_oklab)
        rhs_oklch = OkLab_to_OkLch(rhs_oklab)
        palette_oklch = OkLab_to_OkLch(palette_oklab)
        palette_oklch[1] = mix(palette_oklch[1], mix(lhs_oklch[1], rhs_oklch[1], alpha), chroma_weight)
        palette_oklab = OkLch_to_OkLab(palette_oklch)

    return palette_oklab


if __name__ == "__main__":
    print(linear_2_sRGB(np.ones(3)))
    print(linear_2_sRGB(np.zeros(3)))
    print(linear_2_sRGB(np.array([0.25, 0.5, 0.75])))

    srgb_red = np.array([1.0, 0.0, 0.0])
    linear_red = sRGB_to_linear(srgb_red)
    xyz_red = linear_to_XYZ(linear_red)
    print(f"xyz: {xyz_red}")
    oklab_red = XYZ_to_OkLab(xyz_red)
    print(f"oklab: {oklab_red}")

    xyz_red = OkLab_to_XYZ(oklab_red)
    print(f"xyz: {xyz_red}")
    linear_red = XYZ_to_linear(xyz_red)
    srgb_red = linear_2_sRGB(linear_red)
    print(f"srgb: {srgb_red}")
