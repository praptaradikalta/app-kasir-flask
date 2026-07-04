# utils.py
import bcrypt
def hash_password(password):
 return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def parse_int(value, default=0):
    """
    Mencoba mengkonversi value ke integer.
    Jika gagal, kembalikan nilai default.
    Bisa menerima string angka desimal seperti '25.0'.
    """
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_float(value, default=0.0):
    """
    Mencoba mengkonversi value ke float.
    Jika gagal, kembalikan nilai default.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_bool(value, default=False):
    """
    Mengkonversi value ke boolean.
    Menerima nilai string '0', '1', 'true', 'false', integer 0 atau 1.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        val = value.strip().lower()
        if val in ['1', 'true', 'yes', 'on']:
            return True
        elif val in ['0', 'false', 'no', 'off']:
            return False
    return default


def validate_enum(value, enum_class, default=None):
    """
    Validasi apakah value ada di enum_class (Enum).
    Jika valid, kembalikan value, jika tidak kembalikan default.
    """
    valid_values = [e.value for e in enum_class]
    if value in valid_values:
        return value
    return default


def sanitize_string(value, default=''):
    """
    Membersihkan dan mengembalikan string yang sudah strip.
    Jika None atau bukan string, kembalikan default.
    """
    if isinstance(value, str):
        return value.strip()
    return default
