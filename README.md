# SUPERMAN.KUMAR

WhatsApp jaisi chat app — apne LLB whiteboard ki photo bhejo, phone hi
usse padhega (offline, Google ML Kit) aur ek clean, readable text-image
bana kar wapas dega. Us image ko share bhi kar sakte ho.

**Koi API key nahi. Koi account setup nahi. Koi extra step nahi.**
Sirf GitHub par code paste karo, APK ban jayega.

## Files
- `main.py` – Poora app ka code
- `buildozer.spec` – Android APK build settings
- `.github/workflows/main.yml` – GitHub Actions, jo automatic APK banayega
- `README.md` – Ye file

## Setup steps (sirf itna karna hai)

1. GitHub par ek naya repository banao.
2. Ye files/folders repo me is exact structure me upload karo:
   ```
   .github/workflows/main.yml
   main.py
   buildozer.spec
   README.md
   ```
   `.github` folder ka naam bilkul waisa hi rakhna.
3. Push karo `main` branch par.
4. Repo ke **Actions** tab me jao — build khud-ba-khud shuru ho jayegi.
   Pehli build ~20-30 minute legi.
5. Build complete hone par usi run ke **Artifacts** section me
   `superman-kumar-apk` milega — download karke phone me install kar lo.

Bas. Isse zyada kuch nahi karna — na key, na login, na config.

## App kaise kaam karti hai
1. App khulte hi seedha chat screen dikhegi.
2. "Camera" ya "Gallery" button se whiteboard photo bhejo.
3. Photo turant chat me dikhegi ("Sent ✓").
4. App estimate batayegi, fir phone ke andar hi (bina internet) text
   padhega.
5. Ready hote hi ek nayi readable text-image chat me aayegi, jisme
   "Share Image" button hoga.

## Zaroori jaankari
- Ye poori tarah offline chalti hai — istemal karte waqt internet ki
  zaroorat nahi.
- Handwriting bahut zyada messy/dhundhli hui to accuracy kam ho sakti
  hai — photo achhi roshni me, seedhi aur paas se lena.
- Ye app **desktop par test nahi ho sakti** (OCR feature sirf phone
  par built APK me kaam karega) — ye normal hai, worry mat karo.
