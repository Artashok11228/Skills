# Examples (fictional inventories / نمونهٔ ساختگی)

Skill names below are invented to show shape and reasoning. Always build answers from the real inventory.

## 1. Simple: one skill is enough

Request: «یک تست برای این باگ می‌خواهم؛ کدام اسکیل؟»
Inventory has `tdd` (invocable) and `unit-test-helper` (other tool, overlaps).

```markdown
**برداشت و فرض‌ها:** یک باگ مشخص داری و می‌خواهی اول تست شکست‌خورده بنویسی؛ تغییر بزرگ نیست.

**اسکیل منتخب:** `tdd`: چرخهٔ تست‌اول را دقیقاً پوشش می‌دهد. قابل فراخوانی در همین ابزار (`/tdd`)؛ وابستگی خاصی ندارد.
`unit-test-helper` هم‌پوشان است و فقط در ابزار دیگر است؛ مزیتی ندارد.

**اولین اقدام:** `/tdd` را با شرح باگ و مسیر فایل اجرا کن.
```

## 2. Complex: vibe-coded MVP going to a real customer

Request: «با وایب‌کدینگ ساختم؛ نسخهٔ اول برای مشتری واقعی است؛ چه مسیری؟» No deploy was requested.
Fictional inventory: `requirements-check`, `bug-hunt`, `security-scan` (needs `semgrep`, not installed), `security-review-lite`, `code-review`, `deploy-cloud`.

```markdown
**برداشت و فرض‌ها:** محصول کار می‌کند ولی بررسی سیستماتیک نشده؛ کاربر واقعی و داده‌اش در میان است، پس امنیت ضروری است. استقرار خواسته نشده.

**اسکیل‌های منتخب**
- `requirements-check`: نیاز مشتری و مسیر اصلی را به معیار پذیرش تبدیل می‌کند؛ پایهٔ بقیهٔ بررسی‌هاست. قابل فراخوانی؛ وابستگی ندارد.
- `bug-hunt`: باگ و کندی مسیرهای اصلی. قابل فراخوانی.
- `security-review-lite`: بررسی امنیتی مبتنی بر خواندن کد. قابل فراخوانی. (`security-scan` عمیق‌تر است ولی `semgrep` نصب نیست، پس جایگزین فقط در صورت نصب.)
- `code-review`: بازبینی مجدد اصلاحات. قابل فراخوانی.

**مسیر**
1. [ضروری] `requirements-check`، ورودی: توضیح محصول و مشتری | خروجی: فهرست مسیرهای اصلی و معیار پذیرش | پایان: مسیرهای حیاتی تأیید شد
2. [ضروری] `bug-hunt`، ورودی: خروجی ۱ + کد | خروجی: فهرست باگ‌ها با شدت | پایان: مسیرهای حیاتی بررسی شد
3. [ضروری] `security-review-lite`، ورودی: کد + خروجی ۱ (داده‌های حساس) | خروجی: یافته‌های امنیتی | قابل موازی با ۲ اگر ابزار و تو اجازه بدهید
4. [ضروری] رفع یافته‌های بحرانی ۲ و ۳ (بدون اسکیل خاص)
5. [ضروری] `code-review`، ورودی: تغییرات ۴ | پایان: یافتهٔ بحرانی باز نمانده؛ اگر ماند → برگرد به ۴

جریان: 1 → (2 ∥ 3) → 4 → 5 ↺ 4

**کمبودها و موانع:** تست بار و مانیتورینگ پوشش ندارد؛ `semgrep` نصب نیست. استقرار (`deploy-cloud`) خارج از این درخواست است و مرحله نیست. این بررسی‌ها ریسک را کم می‌کنند ولی آمادگی را تضمین نمی‌کنند.

**اولین اقدام:** `requirements-check` را با توضیح مشتری و سه کار اصلی‌ای که باید بی‌نقص کار کند اجرا کن.
```

## 3. Advice only

Request: «فقط بگو چه ترتیبی؛ چیزی اجرا نکن.»
Deliver the plan and do not invoke any selected skill. The inventory script in step 2 still runs; it only reads. Say that the chosen skills were not run.
