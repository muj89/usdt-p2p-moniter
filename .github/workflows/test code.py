import requests
from bs4 import BeautifulSoup
from googlesearch import search

# الكلمة المراد البحث عنها
query = "الحرب في السودان"

# استخدام مكتبة googlesearch للحصول على أول 3 روابط من البحث
urls = list(search(query, tld="com", lang="ar", num=3, stop=3, pause=2))

headlines = []

for url in urls:
    try:
        # جلب محتوى الصفحة
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # الحصول على عنوان الصفحة من وسم <title>
            title = soup.title.string.strip() if soup.title else "No Title Found"
            headlines.append(title)
        else:
            headlines.append(f"Error: HTTP {response.status_code} for URL {url}")
    except Exception as e:
        headlines.append(f"Error fetching {url}: {e}")

# حفظ أول 3 عناوين في ملف نصي
with open("results.txt", "w", encoding="utf-8") as f:
    for headline in headlines:
        f.write(headline + "\n")

print("تم حفظ أول 3 عناوين في ملف results.txt")
