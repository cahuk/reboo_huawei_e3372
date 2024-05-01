import serial


def scan_com_ports():
    available_ports = []
    for port_number in range(256):
        try:
            port_name = f"COM{port_number}"
            port = serial.Serial(port_name)
            port.close()
            available_ports.append(port_name)
        except serial.SerialException:
            pass
    return available_ports


# Виведення доступних COM-портів
print("Доступні COM-порти:")
for port in scan_com_ports():
    print(port)
