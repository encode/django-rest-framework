def parse_quantity_and_unit(quantity_unit_string):
    """
    Parse a combined quantity and unit string and return a dictionary containing the parsed values.

    Args:
        quantity_unit_string (str): A string that combines a numeric quantity and a unit, e.g., "5min", "10h".

    Returns:
        dict: A dictionary containing the parsed quantity and unit, with keys 'quantity' and 'unit'.
              If the input string contains only a unit (e.g., "ms"), quantity will be set to 1.
    """
    i = 0
    quantity_unit_dict = {}
    while i < len(quantity_unit_string) and quantity_unit_string[i].isnumeric():
        i += 1
    if i == 0:
        quantity_unit_dict['quantity'] = 1
        quantity_unit_dict['unit'] = quantity_unit_string
    else:
        quantity_unit_dict['quantity'] = int(quantity_unit_string[:i])
        quantity_unit_dict['unit'] = quantity_unit_string[i:]
    return quantity_unit_dict