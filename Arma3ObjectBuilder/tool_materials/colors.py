# Coversion functions to convert between 8-bit sRGB, decimal sRGB and linear RGB.
# https://entropymine.com/imageworsener/srgbformula/
# https://en.wikipedia.org/wiki/SRGB


def is_valid_value(value, input_type):
    if input_type == 'S8':
        return value >= 0 and value <= 255 and value == int(value)
    
    if input_type == 'S':
        return value >= 0.0 and value <= 1.0
        
    if input_type == 'L':
        return value >= 0.0 and value <= 1.0


def srgb8_to_srgb8(value):
    if not is_valid_value(value, 'S8'):
        return -1
    
    return value


def srgb_to_srgb(value):
    if not is_valid_value(value, 'S'):
        return -1
    
    return value


def linear_to_linear(value):
    if not is_valid_value(value, 'L'):
        return -1
    
    return value


def srgb8_to_srgb(value):
    if not is_valid_value(value, 'S8'):
        return -1
    
    return value / 255


def srgb_to_srgb8(value):
    if not is_valid_value(value, 'S'):
        return -1
    
    return round(value * 255)


def srgb_to_linear(value):
    if not is_valid_value(value, 'S'):
        return -1
    
    if value <= 0.04045:
        return value / 12.92
    
    return ((value + 0.055) / 1.055)**2.4


def linear_to_srgb(value):
    if not is_valid_value(value, 'L'):
        return -1
    
    if value <= 0.0031308:
        return value * 12.92
    
    return 1.055 * value**(1/2.4) - 0.055


def srgb8_to_linear(value):
    if not is_valid_value(value, 'S8'):
        return -1
    
    return srgb_to_linear(srgb8_to_srgb(value))


def linear_to_srgb8(value):
    if not is_valid_value(value, 'L'):
        return -1
    
    return srgb_to_srgb8(linear_to_srgb(value))


def convert_color_value(value, input_type, output_type):
    output = -1
    
    if input_type == 'S8':
        if output_type == 'S8':
            output = srgb8_to_srgb8(value)
        elif output_type == 'S':
            output = srgb8_to_srgb(value)
        elif output_type == 'L':
            output = srgb8_to_linear(value)
            
    elif input_type == 'S':
        if output_type == 'S8':
            output = srgb_to_srgb8(value)
        elif output_type == 'S':
            output = srgb_to_srgb(value)
        elif output_type == 'L':
            output = srgb_to_linear(value)
            
    elif input_type == 'L':
        if output_type == 'S8':
            output = linear_to_srgb8(value)
        elif output_type == 'S':
            output = linear_to_srgb(value)
        elif output_type == 'L':
            output = linear_to_linear(value)
    
    return output


def convert_color(rgb, input_type, output_type):
    r = convert_color_value(rgb[0], input_type, output_type)
    g = convert_color_value(rgb[1], input_type, output_type)
    b = convert_color_value(rgb[2], input_type, output_type)

    return (r, g, b)
