import random
import re
import json
import csv
import argparse
import sys
from datetime import datetime
from pathlib import Path
from faker import Faker

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ---------- CONFIGURATION ----------
DEFAULT_NATIONALITY = 'american'
BLOOD_TYPES = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
BLOOD_WEIGHTS = [0.38, 0.07, 0.28, 0.06, 0.18, 0.02, 0.07, 0.01]

# ---------- HELPER FUNCTIONS ----------
def parse_age_range(age_input):
    """Convert '18-30', '18+', '25' to (min, max)."""
    age_input = age_input.strip()
    if '-' in age_input:
        parts = age_input.split('-')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
    if age_input.endswith('+'):
        min_age = int(age_input[:-1])
        return min_age, 120
    if age_input.isdigit():
        age = int(age_input)
        return age, age
    raise ValueError("Age range must be like '18-30', '18+', or '25'")

def skewed_age(min_age, max_age, mode=None):
    """Triangular distribution – skews young. If mode not given, default to lower third."""
    if mode is None:
        mode = min_age + (max_age - min_age) // 3
    return int(random.triangular(min_age, max_age, mode))

def age_to_birthdate(age, current_year=None):
    """Generate birthdate from exact age (not range)."""
    if current_year is None:
        current_year = datetime.now().year
    birth_year = current_year - age
    month = random.randint(1, 12)
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = random.randint(1, days_in_month[month-1])
    try:
        birthdate = datetime(birth_year, month, day).date()
    except ValueError:
        birthdate = datetime(birth_year, 2, 28).date()
    return birthdate

def get_faker_for_nationality(nationality):
    """Map nationality string to Faker locale."""
    locale_map = {
        'american': 'en_US', 'us': 'en_US', 'united states': 'en_US',
        'british': 'en_GB', 'uk': 'en_GB', 'english': 'en_GB',
        'canadian': 'en_CA', 'australian': 'en_AU', 'german': 'de_DE',
        'french': 'fr_FR', 'italian': 'it_IT', 'spanish': 'es_ES',
        'japanese': 'ja_JP', 'chinese': 'zh_CN', 'indian': 'en_IN',
        'russian': 'ru_RU', 'brazilian': 'pt_BR', 'mexican': 'es_MX',
    }
    key = nationality.lower().strip()
    locale = locale_map.get(key, 'en_US')
    return Faker(locale)

def generate_height_weight(gender):
    """Realistic height (cm) and weight (kg) based on gender and BMI ~22."""
    if gender.lower() == 'male':
        height = random.randint(165, 190)
        # BMI between 20-25 -> weight = BMI * (height/100)^2
        bmi = random.uniform(20, 25)
        weight = bmi * (height/100) ** 2
        weight = round(weight, 1)
        weight = max(55, min(120, weight))
    else:
        height = random.randint(155, 175)
        bmi = random.uniform(19, 24)
        weight = bmi * (height/100) ** 2
        weight = round(weight, 1)
        weight = max(45, min(100, weight))
    return height, weight

def generate_password(first_name, birth_year):
    """Generate a plausible password."""
    base = first_name.lower().replace(' ', '') + str(birth_year)[-2:]
    special = random.choice('!@#$%^&*')
    return base + special + str(random.randint(10, 99))

def get_avatar_url(gender, age):
    """DiceBear avatar API – free, no API key."""
    style = random.choice(['adventurer', 'avataaars', 'identicon', 'initials'])
    seed = f"{gender}_{age}_{random.randint(1,10000)}"
    return f"https://avatars.dicebear.com/api/{style}/{seed}.svg"

# ---------- CORE GENERATOR ----------
def generate_single_identity(age_range, nationality, custom_fields=None, use_skew=True):
    """
    Generate one identity dict.
    If use_skew=True, ages follow triangular distribution (realistic younger skew).
    """
    min_age, max_age = parse_age_range(age_range)
    if use_skew:
        age = skewed_age(min_age, max_age)
    else:
        age = random.randint(min_age, max_age)
    
    birthdate = age_to_birthdate(age)
    fake = get_faker_for_nationality(nationality)
    
    identity = {}
    
    # Name overrides
    if custom_fields and 'first_name' in custom_fields:
        identity['first_name'] = custom_fields['first_name']
    else:
        identity['first_name'] = fake.first_name()
    
    if custom_fields and 'last_name' in custom_fields:
        identity['last_name'] = custom_fields['last_name']
    else:
        identity['last_name'] = fake.last_name()
    
    identity['full_name'] = f"{identity['first_name']} {identity['last_name']}"
    identity['birthdate'] = birthdate.isoformat()
    identity['age'] = age
    
    # Gender
    if custom_fields and 'gender' in custom_fields:
        identity['gender'] = custom_fields['gender']
    else:
        identity['gender'] = random.choice(['Male', 'Female', 'Non-binary'])
    
    # Address
    if custom_fields and 'address' in custom_fields:
        identity['address'] = custom_fields['address']
    else:
        identity['address'] = fake.address().replace('\n', ', ')
    
    # Email
    if custom_fields and 'email' in custom_fields:
        identity['email'] = custom_fields['email']
    else:
        base_email = f"{identity['first_name'].lower()}.{identity['last_name'].lower()}@{fake.free_email_domain()}"
        base_email = re.sub(r'[^a-zA-Z0-9._@-]', '', base_email)
        identity['email'] = base_email
    
    # Phone
    if custom_fields and 'phone' in custom_fields:
        identity['phone'] = custom_fields['phone']
    else:
        identity['phone'] = fake.phone_number()
    
    # Job
    if custom_fields and 'job' in custom_fields:
        identity['job'] = custom_fields['job']
    else:
        identity['job'] = fake.job()
    
    identity['nationality'] = nationality
    
    # SSN
    if custom_fields and 'ssn' in custom_fields:
        identity['ssn'] = custom_fields['ssn']
    else:
        try:
            identity['ssn'] = fake.ssn()
        except:
            identity['ssn'] = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
    
    # Height/Weight correlated
    if custom_fields and 'height_cm' in custom_fields and 'weight_kg' in custom_fields:
        identity['height_cm'] = custom_fields['height_cm']
        identity['weight_kg'] = custom_fields['weight_kg']
    else:
        h, w = generate_height_weight(identity['gender'])
        identity['height_cm'] = h
        identity['weight_kg'] = w
    
    # Blood type
    identity['blood_type'] = random.choices(BLOOD_TYPES, weights=BLOOD_WEIGHTS)[0]
    
    # Password
    birth_year = birthdate.year
    identity['password'] = generate_password(identity['first_name'], birth_year)
    
    # Avatar URL
    identity['avatar_url'] = get_avatar_url(identity['gender'], identity['age'])
    
    # Additional custom fields (any leftover from input)
    if custom_fields:
        for key, value in custom_fields.items():
            if key not in identity:
                identity[key] = value
    
    # Add an ID field
    identity['identity_id'] = f"{identity['first_name'][:2]}{identity['last_name'][:2]}{random.randint(1000,9999)}".upper()
    
    return identity

def batch_generate(age_range, nationality, count, use_skew=True, custom_base=None):
    """Generate list of identities."""
    identities = []
    for _ in range(count):
        identities.append(generate_single_identity(age_range, nationality, custom_base, use_skew))
    return identities

# ---------- EXPORT FUNCTIONS ----------
def export_to_csv(identities, filename):
    """Export list of dicts to CSV."""
    if not identities:
        return
    fieldnames = list(identities[0].keys())
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(identities)
    print(f"✅ Exported {len(identities)} identities to {filename}")

def export_to_json(identities, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(identities, f, indent=2)
    print(f"✅ Exported {len(identities)} identities to {filename}")

# ---------- PRESET SYSTEM ----------
def save_preset(name, custom_dict):
    preset_path = Path(f"presets/{name}.preset.json")
    preset_path.parent.mkdir(exist_ok=True)
    with open(preset_path, 'w') as f:
        json.dump(custom_dict, f, indent=2)
    print(f"💾 Preset '{name}' saved to {preset_path}")

def load_preset(name):
    preset_path = Path(f"presets/{name}.preset.json")
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset '{name}' not found.")
    with open(preset_path, 'r') as f:
        return json.load(f)

def list_presets():
    preset_dir = Path("presets")
    if not preset_dir.exists():
        return []
    return [p.stem for p in preset_dir.glob("*.preset.json")]

# ---------- ENCRYPTION ----------
def encrypt_identities(identities, password):
    if not CRYPTO_AVAILABLE:
        print("⚠️ cryptography module not installed. Install with: pip install cryptography")
        return None
    # Derive a key from password (simplistic, use PBKDF2 in production)
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.primitives import hashes
    import base64
    salt = b'ony_salt_'  # in real code, generate random salt and store it
    kdf = PBKDF2(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    cipher = Fernet(key)
    data = json.dumps(identities).encode()
    encrypted = cipher.encrypt(data)
    return encrypted

def decrypt_identities(encrypted_data, password):
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography required")
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.primitives import hashes
    import base64
    salt = b'ony_salt_'
    kdf = PBKDF2(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    cipher = Fernet(key)
    decrypted = cipher.decrypt(encrypted_data)
    return json.loads(decrypted.decode())

# ---------- DISPLAY ----------
def display_identity(identity):
    print("\n" + "="*60)
    print(f"🆔  ONYIDENTITY – {identity['full_name']}")
    print("="*60)
    for key, value in identity.items():
        pretty_key = key.replace('_', ' ').title()
        # truncate long values for clean display
        val_str = str(value)[:60]
        print(f"{pretty_key:20} : {val_str}")
    print("="*60 + "\n")

# ---------- COMMAND LINE INTERFACE ----------
def interactive_mode():
    """Run the interactive generator menu."""
    print(r"""
    ╔════════════════════════════════════════════════╗
    ║         O N Y I D E N T I T Y  v1.0           ║
    ║     Advanced Identity Generator               ║
    ╚════════════════════════════════════════════════╝
    """)
    while True:
        print("\n[1] Generate single identity")
        print("[2] Batch generate (export to CSV/JSON)")
        print("[3] Save current custom fields as preset")
        print("[4] Load preset")
        print("[5] List presets")
        print("[6] Exit")
        choice = input("\nChoose: ").strip()
        
        if choice == '1':
            age_r = input("Age range: ").strip()
            if not age_r:
                print("❌ Age range required")
                continue
            nat = input("Nationality: ").strip() or DEFAULT_NATIONALITY
            custom = {}
            print("\n✨ Enter custom overrides (blank to skip):")
            for field in ['first_name','last_name','gender','job','email']:
                val = input(f"  {field}: ").strip()
                if val:
                    custom[field] = val
            ident = generate_single_identity(age_r, nat, custom, use_skew=True)
            display_identity(ident)
        
        elif choice == '2':
            age_r = input("Age range: ").strip()
            if not age_r:
                continue
            nat = input("Nationality: ").strip() or DEFAULT_NATIONALITY
            try:
                count = int(input("Number of identities: ").strip())
            except:
                count = 1
            custom = {}
            # quick custom (optional)
            extra = input("Any global custom fields? (key=value, comma): ").strip()
            if extra:
                for pair in extra.split(','):
                    if '=' in pair:
                        k,v = pair.split('=',1)
                        custom[k.strip()] = v.strip()
            print(f"⏳ Generating {count} identities...")
            identities = batch_generate(age_r, nat, count, use_skew=True, custom_base=custom)
            # ask export format
            fmt = input("Export to [csv/json/none]: ").lower().strip()
            if fmt == 'csv':
                fname = input("Filename (e.g., output.csv): ").strip() or f"identities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                export_to_csv(identities, fname)
            elif fmt == 'json':
                fname = input("Filename (e.g., output.json): ").strip() or f"identities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                export_to_json(identities, fname)
            else:
                # just display first 3
                for i, ident in enumerate(identities[:3]):
                    print(f"\n--- Identity {i+1} ---")
                    display_identity(ident)
                if len(identities) > 3:
                    print(f"... and {len(identities)-3} more.")
        
        elif choice == '3':
            print("Save current custom fields as preset.")
            # you'd normally collect a dict, but here we ask for fields manually
            preset_name = input("Preset name: ").strip()
            if not preset_name:
                print("❌ Invalid name")
                continue
            custom_dict = {}
            print("Enter key=value pairs (empty line to finish):")
            while True:
                entry = input("> ").strip()
                if not entry:
                    break
                if '=' in entry:
                    k,v = entry.split('=',1)
                    custom_dict[k.strip()] = v.strip()
            save_preset(preset_name, custom_dict)
        
        elif choice == '4':
            presets = list_presets()
            if not presets:
                print("No presets found.")
                continue
            print("Available presets:", ", ".join(presets))
            pname = input("Preset name: ").strip()
            try:
                loaded = load_preset(pname)
                print("✅ Preset loaded. Use it in generation by adding custom fields.")
                # Optionally, you could feed it into a generation, but we just display
                print("Fields:", loaded)
            except Exception as e:
                print(f"❌ {e}")
        
        elif choice == '5':
            presets = list_presets()
            if presets:
                print("Presets:", ", ".join(presets))
            else:
                print("No presets saved yet.")
        
        elif choice == '6':
            print("👋 Exiting OnyIdentity. Stay Ony.")
            break
        
        else:
            print("Invalid choice.")

def cli_mode():
    """Parse command line arguments for non‑interactive batch use."""
    parser = argparse.ArgumentParser(description="OnyIdentity – generate fake identities")
    parser.add_argument('--age', required=True, help="Age range, e.g., '18-35'")
    parser.add_argument('--nationality', default=DEFAULT_NATIONALITY, help="e.g., american, german, japanese")
    parser.add_argument('--count', type=int, default=1, help="Number of identities to generate")
    parser.add_argument('--output', help="Output file (JSON or CSV based on extension)")
    parser.add_argument('--preset', help="Load custom fields from preset name")
    parser.add_argument('--no-skew', action='store_true', help="Use uniform age distribution (default is skewed young)")
    parser.add_argument('--encrypt', help="Encrypt output with password (requires cryptography)")
    args = parser.parse_args()
    
    custom = {}
    if args.preset:
        try:
            custom = load_preset(args.preset)
            print(f"Loaded preset '{args.preset}'")
        except Exception as e:
            print(f"Error loading preset: {e}")
            sys.exit(1)
    
    identities = batch_generate(args.age, args.nationality, args.count, use_skew=not args.no_skew, custom_base=custom)
    
    if args.output:
        if args.output.lower().endswith('.csv'):
            export_to_csv(identities, args.output)
        else:
            export_to_json(identities, args.output)
        
        if args.encrypt and CRYPTO_AVAILABLE:
            encrypted = encrypt_identities(identities, args.encrypt)
            enc_file = args.output + ".enc"
            with open(enc_file, 'wb') as f:
                f.write(encrypted)
            print(f"🔒 Encrypted version saved to {enc_file}")
        elif args.encrypt and not CRYPTO_AVAILABLE:
            print("⚠️ cryptography not installed, cannot encrypt.")
    else:
        # print to stdout
        for ident in identities:
            print(json.dumps(ident, indent=2))
            print("-" * 40)

# ---------- MAIN ENTRY ----------
if __name__ == "__main__":
    # If any CLI arguments given, run in CLI mode; otherwise interactive.
    if len(sys.argv) > 1:
        cli_mode()
    else:
        interactive_mode()