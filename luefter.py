#!/usr/bin/python
#coding: utf8

#
# Notwendige Bibliotheken
#
import sys
import time
import os
import math
import RPi.GPIO as GPIO
import Adafruit_DHT

##################################################################################################

#
# Sensor Innen
#

# Type ist DHT22
sensorinnen = Adafruit_DHT.DHT22

# Pin ist GPIO27 = PIN13
# siehe https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header
gpioinnen = 27

#
# Sensor Aussen
#

# Type ist DHT22
sensoraussen = Adafruit_DHT.DHT22

# Pin ist GPIO22 = PIN15
# siehe https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header
gpioaussen = 22

#
# Ausgang für den Lüfter
#

# Zählweise der Pins festlegen: Wir bezeichnen GPIOs und nicht die PINs
GPIO.setmode(GPIO.BCM)

# Das Relais hängt an GPIO 10 = PIN19
# siehe https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header
gpioausgang = 10

# GPIO 10 als Ausgang festlegen und ausschalten
GPIO.setup(gpioausgang, GPIO.OUT)
GPIO.output(gpioausgang, GPIO.LOW)

# Die Spannungsversorgung der Sensoren hängt an GPIO 9 = PIN21
# siehe https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header
gpiospannung = 9

# GPIO 9 als Ausgang festlegen und einschalten
GPIO.setup(gpiospannung, GPIO.OUT)
GPIO.output(gpiospannung, GPIO.HIGH)

# Die StatusLED hängt an GPIO 11 = PIN23
# siehe https://www.raspberrypi.com/documentation/computers/os.html#gpio-and-the-40-pin-header
gpiostatus = 11

# GPIO 11 als Ausgang festlegen und ausschalten
GPIO.setup(gpiostatus, GPIO.OUT)
GPIO.output(gpiostatus, GPIO.LOW)

#
# Grenzwerte
#

# Schleifenzeit in Sekunden - lese alle x Sekunden ein Wert
loopzeit = 300

# Maximal erlaubte Luftfeuchtigkeit Innen
humiditymax = 75

# Minimal erlaubte Temperatur Innen
temperaturemin = 4

# Min Differenz absolute Feuchte Innen/Aussen in g/m3
humiditydiff = 2

# Sperrzeit Lüfter in Sekunden (Nach Ausschalten ist der Lüfter für diese Zeit verriegelt)
sperrzeit = 900

######################################################################################################

# Variable bei Start initalisieren
sperrzeittimestamp = 0

#
# Commandline Parameter
#
if len(sys.argv) > 1:
    parameter1 = sys.argv[1]
else:
    parameter1 = None

#
# Wenn Parameter = test, dann gebe Werte aus, schalte Luefter EIN und nach 5 Sekunden aus, dann beenden
#
if parameter1 == "test":
    print "--> Lese Sensoren ein..."
    # SensorInnen auslesen
    humidityinnen, temperatureinnen = Adafruit_DHT.read_retry(sensorinnen, gpioinnen)
    if humidityinnen is not None and temperatureinnen is not None:
        # Blink wenn OK
        GPIO.output(gpiostatus, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(gpiostatus, GPIO.LOW)
        print('Innen:  Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperatureinnen, humidityinnen))
    else:
        print('Innen:  FEHLER!')

    # SensorInnen auslesen
    humidityaussen, temperatureaussen = Adafruit_DHT.read_retry(sensoraussen, gpioaussen)
    if humidityaussen is not None and temperatureaussen is not None:
        # Blink wenn OK
        GPIO.output(gpiostatus, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(gpiostatus, GPIO.LOW)
        print('Aussen: Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperatureaussen, humidityaussen))
    else:
        print('Aussen: FEHLER!')
   
    time.sleep (1)

    # Lüfter einschalten, GPIO 10 auf EIN setzen
    print "--> Schalte Luefter EIN..."
    GPIO.output(gpioausgang, GPIO.HIGH)

    # Warten
    time.sleep(10)

    # Lüfter wieder ausschalten, GPIO 10 auf AUS setzen
    print "--> Schalte Luefter AUS..."
    GPIO.output(gpioausgang, GPIO.LOW)

    # Ende
    GPIO.cleanup()
    sys.exit(0)

#
# Endlosschleife abarbeiten
#
while True:

    fehler = 0
    jetzt = time.time()

    # Zeit ausgeben
    print(time.strftime("%d.%m.%Y %H:%M:%S"))

    # Konstanten um Taupunkte und abs. Feuchte zu berechnen
    # Siehe https://www.wetterochs.de/wetter/feuchte.html und https://myscope.net/taupunkttemperatur/
    mw = 18.016 # Molekulargewicht des Wasserdampfes (kg/kmol)
    gk = 8214.3 # universelle Gaskonstante (J/(kmol*K))
    t0 = 273.15 # Absolute Temperatur von 0 °C (Kelvin)

    # SensorInnen auslesen
    humidityinnen, temperatureinnen = Adafruit_DHT.read_retry(sensorinnen, gpioinnen)
    if humidityinnen is not None and temperatureinnen is not None:
        # Blink wenn OK
        GPIO.output(gpiostatus, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(gpiostatus, GPIO.LOW)
        if humidityinnen > 100:
            humidityinnen = 100
        # Taupunkt Berechnung
        t = temperatureinnen
        r = humidityinnen
        tk = t + t0 # Temperatur in Kelvin
        if t >= 0:
            a = 7.5
            b = 237.3
        else:
            a = 9.5
            b = 265.5
        sdd = 6.1078 * 10**((a*t)/(b+t)) # Sättigungsdampfdruck (hPa)
        dd = sdd * (r/100) # Dampfdruck (hPa)
        absfeuchteinnen = 10**5 * mw/gk * dd/tk # Wasserdampfdichte bzw. absolute Feuchte (g/m3)
        v = math.log10(dd/6.1078) # v-Parameter
        taupunktinnen = (b*v) / (a-v) # Taupunkttemperatur (°C)
        print('Innen:  Temp={0:0.1f}°C  Rel.Feuchte={1:0.1f}%  Abs.Feuchte={2:0.1f}g/m3  Tp={3:0.1f}°C'.format(temperatureinnen, humidityinnen, absfeuchteinnen, taupunktinnen))
    else:
        print('Innen:  FEHLER! Schalte Sensoren 5 Sekunden spannungslos.')
        fehler = 1
        # Fehler - eventuell Sensor abgestürzt. 5 Sekunden Spannungslos schalten
        GPIO.output(gpiospannung, GPIO.LOW)
        time.sleep(5)
        GPIO.output(gpiospannung, GPIO.HIGH)

    # SensorInnen auslesen
    humidityaussen, temperatureaussen = Adafruit_DHT.read_retry(sensoraussen, gpioaussen)
    if humidityaussen is not None and temperatureaussen is not None:
        # Blink wenn OK
        GPIO.output(gpiostatus, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(gpiostatus, GPIO.LOW)
        # Korrektur - manchmal steigt Luftfeuchtigkeit auf 2000%...
        if humidityaussen > 100:
            humidityaussen = 100
        # Taupunkt Berechnung
        t = temperatureaussen
        r = humidityaussen
        tk = t + t0 # Temperatur in Kelvin
        if t >= 0:
            a = 7.5
            b = 237.3
        else:
            a = 9.5
            b = 265.5
        sdd = 6.1078 * 10**((a*t)/(b+t)) # Sättigungsdampfdruck (hPa)
        dd = sdd * (r/100) # Dampfdruck (hPa)
        absfeuchteaussen = 10**5 * mw/gk * dd/tk # Wasserdampfdichte bzw. absolute Feuchte (g/m3)
        v = math.log10(dd/6.1078) # v-Parameter
        taupunktaussen = (b*v) / (a-v) # Taupunkttemperatur (°C)
        print('Aussen: Temp={0:0.1f}°C  Rel.Feuchte={1:0.1f}%  Abs.Feuchte={2:0.1f}g/m3  Tp={3:0.1f}°C'.format(temperatureaussen, humidityaussen, absfeuchteaussen, taupunktaussen))
    else:
        fehler = 1
        print('Aussen: FEHLER! Schalte Sensoren 5 Sekunden spannungslos.')
        # Fehler - eventuell Sensor abgestürzt. 5 Sekunden Spannungslos schalten
        GPIO.output(gpiospannung, GPIO.LOW)
        time.sleep(5)
        GPIO.output(gpiospannung, GPIO.HIGH)

    # Wenn kein Fehler aufgetreten ist, starte Lüfter bei gegebenen Bedingungen
    # Logik:
    # WENN rel. Luftfeuchtigkeit Innen > humiditymax UND
    # WENN Temperatur Innen > temperaturemin UND
    # WNN Abs. Luftfeuchtigkeit Außen + humiditydiff < Abs. Luftfeuchtigkeit Innen UND
    # Sperrzeit nicht aktiv
    if fehler == 0:
        if humidityinnen > humiditymax and temperatureinnen > temperaturemin and absfeuchteaussen + humiditydiff < absfeuchteinnen:
            if jetzt < sperrzeittimestamp:
                print "--> Lüfter soll ein, aber Sperrzeit AKTIV..."
            else:
                print "--> Lüfter EIN..."
                GPIO.output(gpioausgang, GPIO.HIGH)
                luefter = 1
        else:
            print "--> Lüfter AUS..."
            # Wenn Lüfter an war, setze Sperrzeit neu
            if GPIO.input(gpioausgang) is 1:
                sperrzeittimestamp = jetzt + sperrzeit
            GPIO.output(gpioausgang, GPIO.LOW)
            luefter = 0

        # Speichere Statistik im Plugin MQTTGateway / Stats4Lox
        os.system('curl -s "http://localhost/admin/plugins/mqttgateway/mqtt.php?topic=Lüftersteuerung/Humidity_Innen&value=' + str(humidityinnen) + '&retain=1" > /dev/null')
        os.system('curl -s "http://localhost/admin/plugins/mqttgateway/mqtt.php?topic=Lüftersteuerung/Humidity_Aussen&value=' + str(humidityaussen) + '&retain=1" > /dev/null')
        os.system('curl -s "http://localhost/admin/plugins/mqttgateway/mqtt.php?topic=Lüftersteuerung/Temperature_Innen&value=' + str(temperatureinnen) + '&retain=1" > /dev/null')
        os.system('curl -s "http://localhost/admin/plugins/mqttgateway/mqtt.php?topic=Lüftersteuerung/Temperature_Aussen&value=' + str(temperatureaussen) + '&retain=1" > /dev/null')
        os.system('curl -s "http://localhost/admin/plugins/mqttgateway/mqtt.php?topic=Lüftersteuerung/Lüfterausgang&value=' + str(luefter) + '&retain=1" > /dev/null')

    # Wartezeit
    time.sleep(loopzeit)
