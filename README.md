<div dir="rtl">

# Skills

مجموعهٔ اسکیل‌های شخصی من برای کار با دستیارهای هوش مصنوعی.
هر اسکیل در یک پوشهٔ مستقل نگهداری می‌شود و دستورالعمل اصلی آن در فایل `SKILL.md` قرار دارد.

## اسکیل‌های موجود

| اسکیل | کاربرد |
| --- | --- |
| [agile-team](skills/agile-team/SKILL.md) | اجرای مرحله‌ای قابلیت‌ها و رفع اشکال با معیار پذیرش، بررسی امنیت و تأیید نتیجه از نگاه محصول. |

## ساختار ریپو

</div>

```text
Skills/
├── README.md
├── .gitignore
└── skills/
    └── agile-team/
        └── SKILL.md
```

<div dir="rtl">

هر اسکیل در صورت نیاز می‌تواند پوشه‌های `scripts/` برای ابزارهای اجرایی، `references/` برای مستندات کمکی و `assets/` برای فایل‌های مورد استفاده در خروجی داشته باشد.

## افزودن اسکیل جدید

۱. داخل `skills/` یک پوشه با نام انگلیسی کوچک و خط تیره بساز؛ مثلاً `laravel-helper`.

۲. در آن فایل `SKILL.md` بساز. این نمونه را با کاربرد واقعی اسکیل خودت کامل کن:

</div>

```markdown
---
name: laravel-helper
description: Review Laravel controllers for validation and authorization issues.
---

# Laravel Helper

Use this skill when reviewing Laravel controllers.

1. Check request validation.
2. Check authorization for the requested action.
3. Report actionable findings with file locations and suggested fixes.
```

<div dir="rtl">

۳. مشخص کن اسکیل چه زمانی استفاده شود، چه مراحلی داشته باشد و چه خروجی‌ای بدهد. نام پوشه و مقدار `name` را یکسان نگه دار.

۴. لینک و توضیح کوتاه آن را به جدول اسکیل‌های همین صفحه اضافه کن.

۵. تغییرات را بررسی و ارسال کن:

</div>

```powershell
Set-Location 'D:\My-skills'
git status
git diff
git add -- skills/laravel-helper README.md
git diff --cached
git commit -m "Add laravel-helper skill"
git push
```

<div dir="rtl">

## دریافت و استفاده

برای دریافت ریپو:

</div>

```powershell
git clone https://github.com/Artashok11228/Skills.git
```

<div dir="rtl">

سپس پوشهٔ اسکیل موردنظر را در مسیر اسکیل‌های ابزار خود قرار بده. مسیر نصب و روش فعال‌سازی به ابزار بستگی دارد؛ فقط کلون کردن این ریپو، اسکیل‌ها را در ابزارها فعال نمی‌کند.

## نگهداری

- هر اسکیل یک پوشه و یک کاربرد مشخص داشته باشد.
- فایل‌های کمکی را فقط زمانی اضافه کن که واقعاً لازم‌اند.
- رمز، توکن، فایل محیطی و اطلاعات خصوصی را وارد ریپو نکن.
- پیش از هر ارسال، تغییرات آمادهٔ ثبت را با `git diff --cached` بررسی کن.
- پیش از انتشار برای استفادهٔ دیگران، مجوز مناسب را انتخاب و در فایل `LICENSE` ثبت کن.

</div>
