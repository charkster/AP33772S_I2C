import machine
import socket
import network
import time
from AP33772S import *

i2c    = machine.I2C(scl=machine.Pin(7), sda=machine.Pin(6), freq=100000) # esp32c3 xiao

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.ifconfig(('192.168.0.203', '255.255.255.0', '192.168.0.1', '205.171.3.25'))
    wlan.active(True)
    wlan.connect('your_ssid', 'your_password')

    max_wait = 10 # Wait for connection to establish
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

connect_to_wifi()
USB_PD = AP33772S(i2c=i2c)

pdo_list = ['0 OFF']
pdo_html  = '<pre><b>Num, Type,  Volt Upper, Current</b><br />\n'
for pdo_num in range(1,8):
    pdo = USB_PD.get_pdo(pdo_num)
    if (pdo[2] > 0.0):
        if (pdo[1] == 'FIXED'):
            pdo_str = '{}    {:5}  {:5.1f}         {:.2f}'.format(pdo[0],pdo[1],pdo[2],pdo[3])
        else:
            pdo_str = '{}    {:5}  {:5.1f}         {:.2f}'.format(pdo[0],pdo[1],pdo[2],pdo[3])
        pdo_html +=  pdo_str + '<br />\n'
        pdo_list.append(pdo_str)
pdo_html += '</pre>\n'

html_str  = '<!DOCTYPE html>\n'
html_str += '<html>\n'
html_str += '<body>\n'
html_str += '<h2>Available PDOs</h2>\n'
html_str += pdo_html + '<br />\n'
html_str += '<form action=\"/\" method=\"post\">\n'
html_str += '<b><label for=\"pdo-select\">PDO Selection:</label></b><br />\n'
html_str += '<select name=\"selection\" id=\"PDO Select\">\n'
html_str += '<option value=\"\">--Please choose an option--</option>\n'
pdo_count = 0
for pdo in pdo_list:
    html_str += '<option value=\"' + str(pdo_count) + '\">' + pdo + '</option>\n'
    pdo_count += 1
html_str += '</select>\n'
html_str += '<input type=\"submit\" value=\"Click to Select\"/><br />\n'
html_str += '<b><label for=\"pps_volt\">PPS Voltage:</label></b><br />\n'
html_str += '<input type=\"number\" required name=\"pps_volt\" min=\"0\" value=\"0\" step=\"0.01\"><br /><br />\n'
html_str += '</form>\n'

html_str_end  = '</body>\n'
html_str_end += '</html>\n'

def handle_client(client):
    request = client.recv(1024)
    request = str(request)
#    print('Content = %s' % request)

    if 'POST' in request:
        pps_volt = 0.0
        selection = int(request.split('selection=')[1][0])
        pps_volt  = float(request.split('pps_volt=')[1][:-1])
        if (selection == 0): # disable
            USB_PD.set_rdo_reset()
            USB_PD.set_output('OFF')
            en_pin.value(0)
            time.sleep(1)
            en_pin.value(1)
        else:
            USB_PD.set_output('AUTO')
            pdo = USB_PD.get_pdo(selection)
            if (pdo[1] == 'FIXED'):
                USB_PD.set_rdo(pdo_num=selection, voltage=pdo[2],   op_current=pdo[3])
            elif (pdo[1] == 'PPS'):
                USB_PD.set_rdo(pdo_num=selection, voltage=pps_volt, op_current=pdo[3] )
    
    meas_volt_str = '{:.3f}'.format(USB_PD.get_voltage())
    meas_curr_str = '{:.3f}'.format(USB_PD.get_current())
    html_str_measure  = '<b>Measured Voltage: </b>' +  meas_volt_str + '<br />\n'
    html_str_measure += '<b>Measured Current: </b>' +  meas_curr_str + '<br />\n'
    html_str_measure += '<button onClick=\"window.location.reload();\">Measure</button>\n'

    client.send('HTTP/1.1 200 OK\r\n')
    client.send('Content-Type: text/html\r\n')
    client.send('Connection: close\r\n\r\n')
    client.sendall(html_str)
    client.sendall(html_str_measure)
    client.sendall(html_str_end)
    client.close()

# Set up the web server
address = socket.getaddrinfo('192.168.0.203', 80)[0][-1]
server_socket = socket.socket()
server_socket.bind(address)
server_socket.listen(5) # at most 5 clients
print('Listening on', address)

while True:
    client, addr = server_socket.accept()
    print('Client connected from', address)
    handle_client(client)

