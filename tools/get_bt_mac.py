"""Trouve la MAC Bluetooth associée à COM15."""
import winreg

def find_com_port_mac(target_com="COM15"):
    """Cherche dans BTHENUM quel device Bluetooth a le port cible."""
    base = r"SYSTEM\CurrentControlSet\Enum\BTHENUM"
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
    except FileNotFoundError:
        print("Clé BTHENUM introuvable.")
        return

    print(f"Recherche du device lié à {target_com}...\n")

    i = 0
    while True:
        try:
            dev_class = winreg.EnumKey(root, i)
            dev_class_key = winreg.OpenKey(root, dev_class)
            j = 0
            while True:
                try:
                    instance = winreg.EnumKey(dev_class_key, j)
                    inst_key = winreg.OpenKey(dev_class_key, instance)

                    # Cherche le FriendlyName
                    try:
                        name, _ = winreg.QueryValueEx(inst_key, "FriendlyName")
                    except FileNotFoundError:
                        name = "(sans nom)"

                    # Cherche les params COM
                    try:
                        param_key = winreg.OpenKey(inst_key, "Device Parameters")
                        try:
                            port, _ = winreg.QueryValueEx(param_key, "PortName")
                            if target_com.upper() in port.upper():
                                print(f"[TROUVÉ] {target_com} → {name}")
                                print(f"         Instance : {instance}")
                                # Extrait la MAC de l'instance ID
                                # Format: Dev_XXXXXXXXXXXX&...
                                parts = instance.split("_")
                                for p in parts:
                                    if len(p) == 12 and all(c in "0123456789abcdefABCDEF" for c in p):
                                        mac = ":".join(p[k:k+2] for k in range(0, 12, 2)).upper()
                                        print(f"         MAC      : {mac}")
                        except FileNotFoundError:
                            pass
                        winreg.CloseKey(param_key)
                    except FileNotFoundError:
                        pass

                    winreg.CloseKey(inst_key)
                    j += 1
                except OSError:
                    break
            winreg.CloseKey(dev_class_key)
            i += 1
        except OSError:
            break
    winreg.CloseKey(root)

find_com_port_mac("COM15")
