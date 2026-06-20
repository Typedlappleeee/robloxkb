"""Détection à l'écran pour l'auto-achat (boutique Roblox type "Seed Shop").

Repère tout seul, sans rien enregistrer :
  - les icônes d'articles (cases sombres alignées à gauche de chaque ligne) ;
  - le bouton de confirmation doré (hexagone "acheter").

Le reste du programme clique sur ces positions. Tout est volontairement réglable
(seuils) car l'apparence dépend du jeu, de la résolution et de l'écran.
"""

# OpenCV / numpy / mss sont optionnels : si absents, VISION_OK reste False et
# l'onglet Auto-Achat affiche un message au lieu de planter.
try:
    import cv2
    import numpy as np
    import mss
    VISION_OK = True
    VISION_ERR = ""
except Exception as _e:                       # pragma: no cover
    VISION_OK = False
    VISION_ERR = str(_e)


# ─── Paramètres par défaut (réglables depuis l'interface) ─────────────────────

DEFAULTS = {
    "dark_thresh":   60,    # pixel < seuil = sombre (cadre d'icône d'article)
    "icon_min":      34,    # côté mini d'une icône (px)
    "icon_max":     140,    # côté maxi d'une icône (px)
    "gold_lo":       12,    # teinte dorée mini (HSV OpenCV, 0-179)
    "gold_hi":       38,    # teinte dorée maxi
    "gold_sat":      90,    # saturation mini du doré
    "gold_val":     120,    # luminosité mini du doré
    "gold_min_area": 250,   # aire mini du bouton doré (px²)
}


def detect(img_bgr, p=None):
    """Renvoie (icons, confirms) : listes de (x, y) en pixels image."""
    if p is None:
        p = DEFAULTS
    return _detect_icons(img_bgr, p), _detect_gold(img_bgr, p)


def _detect_icons(img_bgr, p):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    dark = cv2.inRange(gray, 0, int(p["dark_thresh"]))
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lo, hi = int(p["icon_min"]), int(p["icon_max"])
    out = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if not (lo <= w <= hi and lo <= h <= hi):
            continue
        if not (0.7 <= w / float(h) <= 1.4):          # à peu près carré
            continue
        out.append((x + w // 2, y + h // 2))
    return out


def _detect_gold(img_bgr, p):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        (int(p["gold_lo"]), int(p["gold_sat"]), int(p["gold_val"])),
        (int(p["gold_hi"]), 255, 255),
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cnts:
        if cv2.contourArea(c) < int(p["gold_min_area"]):
            continue
        x, y, w, h = cv2.boundingRect(c)
        out.append((x + w // 2, y + h // 2))
    return out


def grab_monitor():
    """Capture l'écran principal. Renvoie (img_bgr, offset_x, offset_y)."""
    with mss.mss() as sct:
        mon = sct.monitors[1]                  # 1 = écran principal
        shot = sct.grab(mon)
        img = np.array(shot)[:, :, :3]         # BGRA -> BGR
        return img, mon["left"], mon["top"]


def annotate(img_bgr, icons, confirms):
    """Dessine les détections pour l'aperçu (vert = article, orange = doré)."""
    out = img_bgr.copy()
    for (x, y) in icons:
        cv2.rectangle(out, (x - 25, y - 25), (x + 25, y + 25), (0, 255, 0), 3)
    for (x, y) in confirms:
        cv2.circle(out, (x, y), 22, (0, 165, 255), 3)
    return out


def show(title, img_bgr, max_w=1280):
    """Affiche une image (aperçu) ; une touche ferme la fenêtre."""
    h, w = img_bgr.shape[:2]
    s = min(1.0, max_w / float(w))
    if s < 1.0:
        img_bgr = cv2.resize(img_bgr, (int(w * s), int(h * s)))
    cv2.imshow(title, img_bgr)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
