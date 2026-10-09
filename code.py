import json

import analogio
import board
import microcontroller
import socketpool
import wifi
from secrets import secrets
from sensors import initialize_sensors, read_sensors


ADC_REFERENCE_V = 3.3
VSYS_DIVIDER = 3.0

sensors, analog_sensors = initialize_sensors()
vsys_input = analogio.AnalogIn(board.A3)

with open("index.html", "rb") as page_file:
    PAGE = page_file.read()

wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])
pool = socketpool.SocketPool(wifi.radio)
server = pool.socket()
server.bind(("0.0.0.0", 80))
server.listen(2)

print("Connected to Wi-Fi:", secrets["ssid"])
print("Open http://%s" % wifi.radio.ipv4_address)


def send_response(client, status, content_type, body):
    headers = (
        "HTTP/1.1 %s\r\n" % status
        + "Content-Type: %s\r\n" % content_type
        + "Content-Length: %d\r\n" % len(body)
        + "Cache-Control: no-store\r\n"
        + "Connection: close\r\n\r\n"
    ).encode("utf-8")
    response = headers + body
    sent = 0
    while sent < len(response):
        count = client.send(response[sent:])
        if count <= 0:
            break
        sent += count


while True:
    client, address = server.accept()
    try:
        request = client.recv(1024)
        request_line = request.split(b"\r\n", 1)[0].split(b" ")
        path = request_line[1] if len(request_line) > 1 else b""

        if path == b"/" or path == b"/index.html":
            send_response(client, "200 OK", "text/html; charset=utf-8", PAGE)
        elif path == b"/temperature":
            vsys_volts = vsys_input.value * ADC_REFERENCE_V / 65535 * VSYS_DIVIDER
            sensor_readings = [
                {"sensor": "Pico processor temperature", "reading": "%.1f C" % microcontroller.cpu.temperature},
                {"sensor": "Pico supply voltage", "reading": "%.2f V" % vsys_volts},
                {"sensor": "Pico CPU frequency", "reading": "%.1f MHz" % (microcontroller.cpu.frequency / 1000000)},
            ]
            sensor_readings.extend(read_sensors(sensors, analog_sensors))
            reading = json.dumps({"sensors": sensor_readings})
            send_response(
                client,
                "200 OK",
                "application/json; charset=utf-8",
                reading.encode("utf-8"),
            )
        else:
            send_response(client, "404 Not Found", "text/plain; charset=utf-8", b"Not found")
    except OSError as error:
        print("Request error:", error)
    finally:
        client.close()