FROM python:3.10-slim

# جلوگیری از کش و خروجی بافر
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# نصب ابزارهای لازم برای بیلد بعضی پکیج‌ها (مثل numpy/pandas)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# اول فقط ریکوایرمنتس رو کپی کنیم برای کش بهتر
COPY requirements.txt .

# نصب دیپندنسی‌ها
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# حالا کل پروژه
COPY . .

# پورت پیش‌فرض
EXPOSE 8000

# دستور اجرا
CMD ["python", "main.py"]
