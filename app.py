from flask import Flask, request, render_template
import os

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATES_AUTO_RELOAD'] = True

game_specs = {
    "NBA 2K25": {
        "min": {"CPU": "Intel i3-6100", "GPU": "NVIDIA GTX 750 Ti", "RAM": 4},
        "rec": {"CPU": "Intel i5-8400", "GPU": "NVIDIA GTX 1060", "RAM": 8}
    },
    "NBA 2K24": {
        "min": {"CPU": "Intel i3-2100", "GPU": "NVIDIA GT 450", "RAM": 4},
        "rec": {"CPU": "Intel i5-4430", "GPU": "NVIDIA GTX 770", "RAM": 8}
    },
    "WWE 2K24": {
        "min": {"CPU": "Intel i5-3550", "GPU": "NVIDIA GTX 1060", "RAM": 8},
        "rec": {"CPU": "Intel i7-4790", "GPU": "NVIDIA RTX 2060", "RAM": 16}
    },
    "PGA 2K23": {
        "min": {"CPU": "Intel i5-7600", "GPU": "NVIDIA GTX 1070", "RAM": 6},
        "rec": {"CPU": "Intel i5-10600K", "GPU": "NVIDIA RTX 2070", "RAM": 12}
    },
    "TopSpin 2K25": {
        "min": {"CPU": "Intel i3-6100", "GPU": "NVIDIA GTX 960", "RAM": 4},
        "rec": {"CPU": "Intel i5-8400", "GPU": "NVIDIA GTX 1070", "RAM": 8}
    },
    "LEGO 2K Drive": {
        "min": {"CPU": "Intel i5-4690", "GPU": "NVIDIA GTX 960", "RAM": 8},
        "rec": {"CPU": "Intel i7-8700", "GPU": "NVIDIA RTX 2070", "RAM": 16}
    }
}

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    dxdiag_summary = ""
    msinfo_summary = ""

    if request.method == 'POST':
        selected_game = request.form.get('game', 'NBA 2K25')
        dxdiag = request.files.get('dxdiag')
        msinfo = request.files.get('msinfo')

        if dxdiag:
            dx_path = os.path.join(UPLOAD_FOLDER, dxdiag.filename)
            dxdiag.save(dx_path)
            dxdiag_summary = parse_dxdiag(dx_path, selected_game)

        if msinfo:
            ms_path = os.path.join(UPLOAD_FOLDER, msinfo.filename)
            msinfo.save(ms_path)
            msinfo_summary = parse_msinfo(ms_path)

    return render_template("index.html",
                           dxdiag_summary=dxdiag_summary,
                           msinfo_summary=msinfo_summary)

def parse_dxdiag(file_path, game):
    with open(file_path, encoding='utf-8', errors='ignore') as f:
        content = f.read()

    lines = content.splitlines()
    parsed = {
        "GPU": next((l.split(":")[1].strip() for l in lines if "Card name" in l), "Unknown"),
        "CPU": next((l.split(":")[1].strip() for l in lines if "Processor" in l), "Unknown"),
        "RAM": next((l.split(":")[1].strip().split("MB")[0] for l in lines if "Memory:" in l), "0"),
        "DirectX": next((l.split(":")[1].strip() for l in lines if "DirectX Version" in l), "Unknown")
    }

    ram_gb = round(int(parsed["RAM"]) / 1024)
    game_info = game_specs.get(game)

    summary = f"""
🎮 Game: {game}

🖥️ Graphics Card: {parsed['GPU']}
   → {assess_gpu(parsed['GPU'])}

⚙️ CPU: {parsed['CPU']}
   → {assess_cpu(parsed['CPU'])}

💾 RAM: {ram_gb} GB
   → Required: Min {game_info['min']['RAM']} GB / Rec {game_info['rec']['RAM']} GB

🧩 DirectX Version: {parsed['DirectX']}

📊 Game Compatibility:

🧠 CPU:
- Min Spec: {game_info['min']['CPU']} → {compare_cpu(parsed['CPU'], game_info['min']['CPU'])}
- Rec Spec: {game_info['rec']['CPU']} → {compare_cpu(parsed['CPU'], game_info['rec']['CPU'])}

🎮 GPU:
- Min Spec: {game_info['min']['GPU']} → {compare_gpu(parsed['GPU'], game_info['min']['GPU'])}
- Rec Spec: {game_info['rec']['GPU']} → {compare_gpu(parsed['GPU'], game_info['rec']['GPU'])}

📦 RAM:
- Min Spec: {game_info['min']['RAM']} GB → {"OK" if ram_gb >= game_info['min']['RAM'] else "Too Low"}
- Rec Spec: {game_info['rec']['RAM']} GB → {"OK" if ram_gb >= game_info['rec']['RAM'] else "Too Low"}
"""
    return summary

def parse_msinfo(file_path):
    with open(file_path, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    system_info = []
    warnings = []

    for line in lines:
        if "OS Name" in line:
            system_info.append(line.strip())
        if "Processor" in line:
            system_info.append(line.strip())
        if "Total Physical Memory" in line:
            try:
                gb = int(''.join(filter(str.isdigit, line.split(":")[1]))) / 1024
                if gb < 8:
                    warnings.append("[!] Low RAM: Less than 8 GB may cause lag.")
            except:
                pass
            system_info.append(line.strip())
        if "Free Space" in line or "Free Disk Space" in line:
            try:
                gb = int(''.join(filter(str.isdigit, line.split(":")[1]))) / 1024
                if gb < 20:
                    warnings.append("[!] Low storage: Less than 20 GB free space.")
            except:
                pass
        if "Driver Problem" in line or "Disabled" in line:
            warnings.append(f"[!] Driver issue or disabled device: {line.strip()}")

    return "\n".join(system_info + ["", "[POTENTIAL ISSUES]"] + (warnings if warnings else ["No immediate issues found."]))


def assess_gpu(gpu):
    if "RTX" in gpu or "RX 6" in gpu:
        return "High-end gaming"
    elif "GTX 10" in gpu or "RX 5" in gpu:
        return "Good for most games"
    elif "GTX 7" in gpu:
        return "Low-end, older games"
    else:
        return "Unknown performance"

def assess_cpu(cpu):
    if "i7" in cpu or "Ryzen 7" in cpu:
        return "Great for gaming"
    elif "i5" in cpu or "Ryzen 5" in cpu:
        return "Good performance"
    elif "i3" in cpu:
        return "Entry level"
    else:
        return "Unknown"

def compare_cpu(user_cpu, target_cpu):
    if "i7" in user_cpu:
        return "Better"
    elif "i5" in user_cpu:
        return "Match"
    elif "i3" in user_cpu:
        return "Below"
    else:
        return "Unknown"

def compare_gpu(user_gpu, target_gpu):
    if "RTX" in user_gpu or "GTX 1060" in user_gpu:
        return "Match or Better"
    elif "GTX 750" in user_gpu:
        return "Below"
    else:
        return "Unknown"

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
