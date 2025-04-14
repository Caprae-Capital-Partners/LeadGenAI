import re

def clean_company_name_variants(name):
    original = name.strip()
    variants = [original]

    variants.append(original.replace("&", "and"))
    variants.append(original.replace("-", " "))
    variants.append(re.sub(r"[^\w\s\-&]", "", original))
    variants.append(" ".join(original.split()))

    return list(dict.fromkeys(variants))
