# Unicode spoof test-data generator
# Paste your generator code here

def generate_unicode_spoof_data():
    # Example: returns a list of spoofed strings
    return [
        'pаssword',  # Cyrillic 'а'
        'admіn',     # Cyrillic 'і'
        'stаff',     # Cyrillic 'а'
        'drор',      # Cyrillic 'о'
        '<scrіpt>',  # Cyrillic 'і'
        'evіl',      # Cyrillic 'і'
    ]

if __name__ == '__main__':
    data = generate_unicode_spoof_data()
    for item in data:
        print(item)
