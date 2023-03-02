from app.utils import remove_spaces


def test_remove_spaces_success_multiple_spaces():
    input_val = '   Hola \t\n mundo, \r   esta  es una       Prueba'
    assert 'Hola mundo, esta es una Prueba' == remove_spaces(input_val)


def test_remove_spaces_success_multiple_break_lines():
    input_val = ('\n\r  Hola \t\n mundo\n\n\n... \r  '
                 'esta  es una   \r\t\t  Prueba')
    assert 'Hola mundo... esta es una Prueba' == remove_spaces(input_val)


def test_remove_spaces_empty_string():
    assert '' == remove_spaces('')
