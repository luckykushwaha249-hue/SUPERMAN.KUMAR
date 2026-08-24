"""
LLB Whiteboard Notes Helper
----------------------------
WhatsApp jaisi chat UI. Photo bhejo (camera/gallery), app usse phone ke
andar hi (ON-DEVICE, Google ML Kit se) padhega aur ek saaf, readable
text wali image bana kar wapas dega. Us image ko share bhi kar sakte ho.

IMPORTANT: Isme KOI API KEY ya INTERNET ki zaroorat nahi hai.
Sab kuch phone ke andar offline hota hai (Google ML Kit Text Recognition).
"""

import os
import time
import threading
import textwrap
import traceback
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget

from PIL import Image as PILImage, ImageDraw, ImageFont

# ================= ANDROID SETUP =================
try:
    from android.permissions import request_permissions, Permission
    ANDROID = True
except Exception:
    ANDROID = False

APP_DIR = os.path.join(os.path.expanduser("~"), ".llb_notes_app")
os.makedirs(APP_DIR, exist_ok=True)

Window.clearcolor = (0.90, 0.93, 0.90, 1)  # halka whatsapp jaisa background


# =========================================================
#  ON-DEVICE OCR (Google ML Kit) - bina API key, bina internet
# =========================================================
def recognize_text_on_device(filepath, on_success, on_error):
    """
    Ye function sirf built Android APK ke andar chalta hai (jnius/ML Kit
    sirf Android par available hote hain). Desktop par test karte waqt
    ye seedha error dega, jo normal hai.
    """
    if not ANDROID:
        on_error("On-device OCR sirf Android phone (built APK) par kaam "
                  "karta hai, is computer par test nahi ho sakta.")
        return

    try:
        from jnius import autoclass, PythonJavaClass, java_method

        BitmapFactory = autoclass("android.graphics.BitmapFactory")
        InputImage = autoclass("com.google.mlkit.vision.common.InputImage")
        TextRecognition = autoclass("com.google.mlkit.vision.text.TextRecognition")
        TextRecognizerOptions = autoclass(
            "com.google.mlkit.vision.text.latin.TextRecognizerOptions"
        )

        class OnSuccessListener(PythonJavaClass):
            __javainterfaces__ = ["com/google/android/gms/tasks/OnSuccessListener"]
            __javacontext__ = "app"

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method("(Ljava/lang/Object;)V")
            def onSuccess(self, result):
                try:
                    full_text = result.getText()
                except Exception as e:
                    full_text = ""
                self.callback(full_text)

        class OnFailureListener(PythonJavaClass):
            __javainterfaces__ = ["com/google/android/gms/tasks/OnFailureListener"]
            __javacontext__ = "app"

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method("(Ljava/lang/Exception;)V")
            def onFailure(self, exception):
                try:
                    msg = exception.toString()
                except Exception:
                    msg = "Unknown OCR error"
                self.callback(msg)

        bitmap = BitmapFactory.decodeFile(filepath)
        if bitmap is None:
            on_error("Photo file sahi se load nahi ho payi.")
            return

        image = InputImage.fromBitmap(bitmap, 0)
        options = TextRecognizerOptions.DEFAULT_OPTIONS
        recognizer = TextRecognition.getClient(options)

        success_listener = OnSuccessListener(on_success)
        failure_listener = OnFailureListener(on_error)

        task = recognizer.process(image)
        task.addOnSuccessListener(success_listener)
        task.addOnFailureListener(failure_listener)

        # listeners ko zinda rakhna zaroori hai jab tak result na aa jaye
        recognize_text_on_device._last_listeners = (success_listener, failure_listener)

    except Exception as e:
        traceback.print_exc()
        on_error(f"OCR start nahi ho payi: {e}")


# ---------------- Rounded chat bubble helper ----------------
class ChatBubble(BoxLayout):
    """Ek chat bubble (sent ya received) - WhatsApp jaisa look."""

    def __init__(self, sent=True, bg_color=None, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(6), **kwargs)
        self.size_hint_y = None
        self.sent = sent
        if bg_color is None:
            bg_color = (0.82, 0.93, 0.78, 1) if sent else (1, 1, 1, 1)
        with self.canvas.before:
            Color(*bg_color)
            self.bg_rect = RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


def make_row(widget, sent=True):
    """Bubble ko left ya right align karne ke liye wrapper row."""
    row = BoxLayout(size_hint_y=None, padding=(dp(8), dp(4)))
    row.bind(minimum_height=lambda inst, val: setattr(row, "height", val))
    spacer = Widget(size_hint_x=0.15)
    if sent:
        row.add_widget(spacer)
        row.add_widget(widget)
    else:
        row.add_widget(widget)
        row.add_widget(Widget(size_hint_x=0.15))
    return row


class LLBNotesApp(App):
    def build(self):
        self.title = "SUPERMAN.KUMAR"
        if ANDROID:
            try:
                request_permissions([
                    Permission.CAMERA,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE,
                ])
            except Exception:
                pass

        root = BoxLayout(orientation="vertical")

        # ---- Top bar ----
        top_bar = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(10))
        with top_bar.canvas.before:
            Color(0.15, 0.42, 0.35, 1)
            self._top_rect = RoundedRectangle(radius=[0])
        top_bar.bind(pos=self._sync_top, size=self._sync_top)
        top_bar.add_widget(Label(
            text="SUPERMAN.KUMAR",
            bold=True, color=(1, 1, 1, 1), font_size="18sp"
        ))
        root.add_widget(top_bar)

        # ---- Chat area ----
        self.scroll = ScrollView()
        self.chat_layout = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(4), padding=dp(6)
        )
        self.chat_layout.bind(
            minimum_height=lambda inst, val: setattr(self.chat_layout, "height", val)
        )
        self.scroll.add_widget(self.chat_layout)
        root.add_widget(self.scroll)

        # welcome message
        self.add_bot_text(
            "Namaste! Apne LLB whiteboard ki photo bhejiye, main use "
            "readable text image me convert kar dunga (bilkul offline, "
            "phone ke andar hi)."
        )

        # ---- Bottom bar (jaise WhatsApp ka input area) ----
        bottom_bar = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(8), spacing=dp(8))
        with bottom_bar.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self._bottom_rect = RoundedRectangle(radius=[0])
        bottom_bar.bind(pos=self._sync_bottom, size=self._sync_bottom)

        cam_btn = Button(text="Camera", size_hint_x=0.5)
        cam_btn.bind(on_release=self.open_camera)
        gallery_btn = Button(text="Gallery", size_hint_x=0.5)
        gallery_btn.bind(on_release=self.open_gallery)

        bottom_bar.add_widget(cam_btn)
        bottom_bar.add_widget(gallery_btn)
        root.add_widget(bottom_bar)

        return root

    def _sync_top(self, inst, *a):
        self._top_rect.pos = inst.pos
        self._top_rect.size = inst.size

    def _sync_bottom(self, inst, *a):
        self._bottom_rect.pos = inst.pos
        self._bottom_rect.size = inst.size

    # ---------------- Chat helpers ----------------
    def add_bot_text(self, text):
        bubble = ChatBubble(sent=False, size_hint_x=0.8)
        lbl = Label(
            text=text, color=(0, 0, 0, 1), size_hint_y=None,
            text_size=(Window.width * 0.65, None), halign="left", valign="top"
        )
        lbl.bind(texture_size=lambda inst, val: setattr(lbl, "height", val[1]))
        bubble.add_widget(lbl)
        bubble.bind(minimum_height=lambda inst, val: setattr(bubble, "height", val + dp(20)))
        row = make_row(bubble, sent=False)
        self.chat_layout.add_widget(row)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1)
        return lbl

    def add_image_bubble(self, filepath, sent=True, caption=""):
        bubble = ChatBubble(sent=sent, size_hint_x=0.75)
        img = KivyImage(source=filepath, size_hint_y=None, height=dp(220), allow_stretch=True)
        bubble.add_widget(img)
        status_lbl = Label(
            text=caption, color=(0.3, 0.3, 0.3, 1), size_hint_y=None, height=dp(20),
            font_size="12sp"
        )
        bubble.add_widget(status_lbl)
        bubble.height = dp(220) + dp(40)
        row = make_row(bubble, sent=sent)
        self.chat_layout.add_widget(row)
        Clock.schedule_once(lambda dt: setattr(self.scroll, "scroll_y", 0), 0.1)
        return status_lbl, bubble

    def add_share_button(self, bubble, filepath):
        share_btn = Button(text="Share Image", size_hint_y=None, height=dp(36))
        share_btn.bind(on_release=lambda inst: self.share_file(filepath))
        bubble.add_widget(share_btn)
        bubble.height += dp(40)

    # ---------------- Camera / Gallery ----------------
    def open_camera(self, *args):
        try:
            from plyer import camera
            filename = os.path.join(APP_DIR, f"capture_{int(time.time())}.jpg")
            camera.take_picture(filename=filename, on_complete=self.on_photo_selected)
        except Exception:
            self.show_error("Camera available nahi hai is device par.")
            traceback.print_exc()

    def open_gallery(self, *args):
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._on_gallery_selection,
                filters=[["Images", "*.jpg", "*.jpeg", "*.png"]],
            )
        except Exception:
            self.show_error("Gallery open nahi ho payi.")
            traceback.print_exc()

    def _on_gallery_selection(self, selection):
        if selection:
            self.on_photo_selected(selection[0])

    def on_photo_selected(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return
        # UI thread par wapas aana zaroori hai
        Clock.schedule_once(lambda dt: self._handle_new_photo(filepath))

    def _handle_new_photo(self, filepath):
        self.add_image_bubble(filepath, sent=True, caption="Sent ✓")

        try:
            size_kb = os.path.getsize(filepath) / 1024
        except Exception:
            size_kb = 300
        est_seconds = max(4, min(15, int(size_kb / 80) + 4))

        status_lbl = self.add_bot_text(
            f"Photo mil gayi! Padh raha hoon (offline)...\n"
            f"Estimated time: ~{est_seconds} second me readable text image ready ho jayegi."
        )

        thread = threading.Thread(
            target=self._run_ocr, args=(filepath, status_lbl)
        )
        thread.daemon = True
        thread.start()

    # ---------------- OCR pipeline ----------------
    def _run_ocr(self, filepath, status_lbl):
        def on_success(extracted_text):
            if not extracted_text or not extracted_text.strip():
                extracted_text = "(Koi readable text nahi mil paaya. Photo clear roshni me, seedha aur paas se lena try karo.)"
            output_path = self.render_text_image(extracted_text, filepath)
            Clock.schedule_once(
                lambda dt: self._on_processing_done(status_lbl, output_path)
            )

        def on_error(message):
            Clock.schedule_once(
                lambda dt: setattr(status_lbl, "text", f"Error aayi: {message}")
            )

        recognize_text_on_device(filepath, on_success, on_error)

    def _on_processing_done(self, status_lbl, output_path):
        status_lbl.text = "Ho gaya! Aapki readable notes taiyar hain:"
        caption_bubble_lbl, bubble = self.add_image_bubble(
            output_path, sent=False, caption="Readable notes ✓"
        )
        self.add_share_button(bubble, output_path)

    # ---------------- Render text into a clean readable image ----------------
    def render_text_image(self, text, source_path):
        width = 1080
        margin = 50
        font_size = 34
        line_spacing = 12

        font = self._load_font(font_size)

        avg_char_width = font_size * 0.55
        max_chars_per_line = max(20, int((width - 2 * margin) / avg_char_width))

        wrapped_lines = []
        for paragraph in text.split("\n"):
            if paragraph.strip() == "":
                wrapped_lines.append("")
                continue
            wrapped_lines.extend(
                textwrap.wrap(paragraph, width=max_chars_per_line) or [""]
            )

        line_height = font_size + line_spacing
        height = margin * 2 + line_height * max(len(wrapped_lines), 1)

        img = PILImage.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        y = margin
        for line in wrapped_lines:
            draw.text((margin, y), line, font=font, fill=(20, 20, 20))
            y += line_height

        output_path = os.path.join(
            APP_DIR, f"notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        img.save(output_path)
        return output_path

    def _load_font(self, size):
        candidate_paths = [
            "/system/fonts/Roboto-Regular.ttf",
            "/system/fonts/DroidSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    # ---------------- Share ----------------
    def share_file(self, filepath):
        try:
            from plyer import share
            share.share(
                title="LLB Notes",
                text="Meri readable class notes",
                filepath=filepath,
            )
        except Exception:
            self.show_error("Share karne me dikkat aayi. File yaha save hai:\n" + filepath)
            traceback.print_exc()

    # ---------------- Error popup ----------------
    def show_error(self, message):
        popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()


if __name__ == "__main__":
    LLBNotesApp().run()
