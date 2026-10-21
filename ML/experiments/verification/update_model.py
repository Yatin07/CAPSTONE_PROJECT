with open('E:/CAP/ML/models/bakery_model.py', 'r', encoding='utf-8') as f:
    content = f.read()
if 'country_name="FR"' not in content:
    content = content.replace('model.fit(df_item)', 'model.add_country_holidays(country_name="FR")\n        model.fit(df_item)')
    with open('E:/CAP/ML/models/bakery_model.py', 'w', encoding='utf-8') as f:
        f.write(content)
