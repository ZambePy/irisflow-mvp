"""
Tema visual do IrisFlow.
Alto contraste, fontes grandes, cores acessíveis.
Centralizado aqui para facilitar customização por perfil.
"""

# Paleta de cores
COLORS = {
    "bg":           "#0D0D0D",   # fundo principal — quase preto
    "surface":      "#1A1A2E",   # superfície de cartões
    "surface_hover":"#16213E",
    "accent_blue":  "#4CC9F0",   # destaque principal
    "accent_green": "#4ADE80",   # SIM / positivo
    "accent_red":   "#F87171",   # NÃO / negativo / emergência
    "accent_yellow":"#FBBF24",   # alerta / atenção
    "text_primary": "#F0F0F0",
    "text_muted":   "#9CA3AF",
    "dwell_fill":   "#4CC9F0",
    "emergency_bg": "#7F1D1D",
}

# Fonte padrão — sem serifa, legível
FONT_FAMILY = "Segoe UI, Arial, sans-serif"

# QSS global aplicado na QApplication
APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text_primary']};
    font-family: {FONT_FAMILY};
}}

QLabel {{
    color: {COLORS['text_primary']};
}}

QLabel#statusLabel {{
    color: {COLORS['text_muted']};
    font-size: 13px;
}}

QPushButton {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    border: 2px solid {COLORS['accent_blue']};
    border-radius: 12px;
    font-size: 26px;
    font-weight: bold;
    padding: 12px 20px;
    min-height: 110px;
}}

QPushButton:hover {{
    background-color: {COLORS['surface_hover']};
    border-color: {COLORS['accent_blue']};
}}

QPushButton#btnSim {{
    border-color: {COLORS['accent_green']};
    color: {COLORS['accent_green']};
}}

QPushButton#btnNao {{
    border-color: {COLORS['accent_red']};
    color: {COLORS['accent_red']};
}}

QPushButton#btnEmergencia {{
    background-color: {COLORS['emergency_bg']};
    border-color: {COLORS['accent_red']};
    color: {COLORS['accent_red']};
    font-size: 22px;
}}

QProgressBar {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['accent_blue']};
    border-radius: 6px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['dwell_fill']};
    border-radius: 6px;
}}
"""
