import RPi.GPIO as GPIO
import time
import serial
import LCD1602 as LCD
import DHT11
import PCF8591 as ADC
import urllib.request
from flask import Flask
from flask import send_file
from flask import render_template
from datetime import datetime
from picamera import PiCamera
import threading

#camera setup
Mycamera = PiCamera()
Mycamera.resolution = (720, 720)

GPIO.setmode(GPIO.BCM) #set to BCM mode
GPIO.setwarnings(False)

#adc SETUP
ADC.setup(0x48)

#LCD setup
LCD.init(0x27, 1)

RLED = 17 #Red LED if temp too high while measuring
GLED = 5 #Green LED for patient calling nurse
BUTTON = 13 #blue push button
BUZZER = 4 #buzzer
TRIG = 16 #output of ultrasonic sensor
ECHO = 6 #input of ultrasoni256c sensor
MOTION = 18 #green push button to simulate motion sensor
HTSENSOR = 9 #humidity and temperature sensor

#Set LEDs, buzzer and ultrasonic sensor trigger to output
GPIO.setup(RLED, GPIO.OUT)
GPIO.setup(GLED, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(TRIG, GPIO.OUT)

#Set button, ultrasonic sensor echo, and motion sensor to input
GPIO.setup(BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) #the pull down is internal not an external connection
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(MOTION, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) #pull down resistor as push buttons are physically connected to Vcc

#Set up Buzzer to 0.1Hz and 50% duty cycle at first
Buzz = GPIO.PWM(BUZZER, 0.1)
Buzz.start(50)

#Flask Setup
myapp = Flask(__name__)

#ThingSpeak Setup
CH_ID = 2519603 #Channel ID from ThingSpeak
API_KEY = "ZFVBPHNFI0MNA676" #write API Key

#flask default route which displays a welcome statement
@myapp.route('/')
def index():
    return render_template('index.html') #uses html for format

#flask static route to display all logged in patients' details
@myapp.route('/Patient_Info')
def Patient_Info():
    return render_template('Patient_Info.html', patients=patients) #uses html for format

#flask static route to inform us if the patients are in bed 
@myapp.route('/In_Bed')
def In_Bed():
    in_bed = ""	#initialize empty string
    for p in patients:
        if p.inBed:
            in_bed += p.name + " is in bed.\n" 
        else:
            in_bed += p.name + " is not in bed.\n" #concatenate string with each patient's in_bed detail
    return render_template('In_Bed.html', in_bed=in_bed)

#flask dynamic route to display a specific patient's (with index (patientNo-1)) heart rate
@myapp.route('/HeartRate/<patientNo>')
def heartRate(patientNo):
    if(int(patientNo) > len(patients)):
        return "Invalid patient number"
    values = "Readings: " #initialize empty string
    Field_No = int(patientNo) +1	#fields 1-4 are heart rate for corresponding patient
    Numberofreadings = 10      #Number of values to read
    #read a certain number of element from a specific field in a specific ThingSpeak channel
    y = urllib.request.urlopen("https://api.thingspeak.com/channels/{}/fields/{}.csv?results={}".format(CH_ID,Field_No, Numberofreadings))
    data = y.read().decode('ascii')  #Decode the read values to ascii i.e. read the imported date and convert it to ASCII 
    data=",".join(data.split("\n"))      #Convert the imported data (ASCII) to a comma separated string
    # join the table data into comma separated string
    #create a list of only the field values (Temperatures)
    for i in range (5, Numberofreadings*3+3, 3):
    #(start at comma number #5 with step of 3
        values += data.split(",")[i] + ", " #concatenate string with heartrate value
    return render_template('HeartRate.html', values=values)
   

#flask dynamic route to display a specific patient's (with index (patientNo-1)) spo2 level
@myapp.route('/SPO2/<patientNo>')
def SPO2(patientNo):
    if(int(patientNo) > len(patients)):
        return "Invalid patient number"
    values = "Readings: "   #initialize empty string
    #read a certain number of element from a specific field in a specific ThingSpeak channel
    Field_No = int(patientNo) + 4	#fields 5-8 are SPO2 for corresponding patient
    Numberofreadings = 1      #Number of values to read
    y = urllib.request.urlopen("https://api.thingspeak.com/channels/{}/fields/{}.csv?results={}".format(CH_ID,Field_No, Numberofreadings))
    data = y.read().decode('ascii')  #Decode the read values to ascii i.e. read the imported date and convert it to ASCII
    data=",".join(data.split("\n"))      #Convert the imported data (ASCII) to a comma separated string
    # join the table data into comma separated string
    #create a list of only the field values (Temperatures)
    for i in range (5, Numberofreadings*3+3,3):
    #(start at comma number #5 with step of 3
        values += data.split(",")[i] + ", " #concatenate string with spo2 value
    return render_template('SPO2.html', values=values)


#function declaration must be before the interrupt callback function as python executes sequentially
#function to execute when interrupt for falling patient occurs
def warningMotion(self):
        GPIO.output(RLED, GPIO.HIGH) #turn red LED on for 5s
        print('Patient Fallen!')
        Mycamera.start_recording("/home/pi/fallingvideo.h264") #take a 5s video of falling patient
        Buzz.ChangeFrequency(1000) #buzzer sounds on for 5s
        time.sleep(7.5)
        GPIO.output(RLED, GPIO.LOW) #turn red LED off
        Buzz.ChangeFrequency(0.1) #buzzer goes quiet
        Mycamera.stop_recording() #stop recording video

#interrupt callback function
GPIO.add_event_detect(MOTION, GPIO.RISING, callback=warningMotion, bouncetime=2000)

#function to execute when interrupt for calling nurse
def callingNurse(self):
    GPIO.output(GLED, GPIO.HIGH) #turn green LED on for 7.5s
    Buzz.ChangeDutyCycle(50)
    for x in range(5): #simulates alarm sound
        Buzz.ChangeFrequency(1000) #buzzer sounds on for 7.5s
        time.sleep(1)
        Buzz.ChangeFrequency(0.5)
        time.sleep(0.5)
        
    GPIO.output(GLED, GPIO.LOW) #turn green LED off
    Buzz.ChangeFrequency(0.1) #buzzer goes quiet

#interrupt callback function
GPIO.add_event_detect(BUTTON, GPIO.RISING, callback=callingNurse, bouncetime=1000) #rising edge when button is pressed

#from keypadfunc
GPIO.setup(19, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(21, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down = GPIO.PUD_UP)

GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)

GPIO.setup(6, GPIO.IN)

def keypad():
    while(True):

        GPIO.output(26, GPIO.LOW)
        GPIO.output(25, GPIO.HIGH)
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(23, GPIO.HIGH)

        if (GPIO.input(22)==0):
            return(1, '!')
            break

        if (GPIO.input(21)==0):
            return(4, '$')
            break

        if (GPIO.input(20)==0):
            return(7, '&')
            break

        if (GPIO.input(19)==0):
            return(0xE)
            break

        GPIO.output(26, GPIO.HIGH)
        GPIO.output(25, GPIO.LOW)
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(23, GPIO.HIGH)

        if (GPIO.input(22)==0):
            return(2, '@')
            break

        if (GPIO.input(21)==0):
            return(5, '%')
            break

        if (GPIO.input(20)==0):
            return(8, '*')
            break

        if (GPIO.input(19)==0):
            return(0, ')')
            break


        GPIO.output(26, GPIO.HIGH)
        GPIO.output(25, GPIO.HIGH)
        GPIO.output(24, GPIO.LOW)
        GPIO.output(23, GPIO.HIGH)

        if (GPIO.input(22)==0):
            return(3, '#')
            break

        if (GPIO.input(21)==0):
            return(6, '^')
            break
        #Scan row 2
        if (GPIO.input(20)==0):
            return(9, '(')
            break

        if (GPIO.input(19)==0):
            return(0xF)
            break

        GPIO.output(26, GPIO.HIGH)
        GPIO.output(25, GPIO.HIGH)
        GPIO.output(24, GPIO.HIGH)
        GPIO.output(23, GPIO.LOW)

        if (GPIO.input(22)==0):
            return(0xA)
            break

        if (GPIO.input(21)==0):
            return(0xB)
            break

        if (GPIO.input(20)==0):
            return(0xC)
            break

        if (GPIO.input(19)==0):
            return(0xD)
            break

#define Patient class which stores patient's details
class Patient:
  def __init__(self, name, id, height, weight, spo2, temp, heartrate, inBed):
        self.name = name
        self.id = id
        self.height = height
        self.weight = weight
        self.spo2 = spo2
        self.temp = temp
        self.heartrate = heartrate
        self.inBed = inBed

  #function to print patient's details to console
  def printDetails(self):
      print(self.patientDetails())

  #function to return patient's details as a string	
  def patientDetails(self):
      return ("Name: {}\nID: {}\nHeight: {}\nWeight: {}\nSPO2: {}\nTemperature: {}\nHeart Rate: {}\nIn Bed: {}".format(self.name, self.id, self.height, self.weight, self.spo2, self.temp, self.heartrate, self.inBed))

#initialize empty array of patients which will later store the patients in the system
patients = []

#RFID set up
SERIAL_PORT = '/dev/ttyS0' 
ser = serial.Serial(baudrate = 2400,  bytesize = serial.EIGHTBITS,  parity = serial.PARITY_NONE,  port = SERIAL_PORT, stopbits = serial.STOPBITS_ONE,  timeout = 1)

#function to check the RFID read is valid (correct length and format)
def validate_rfid():
          time.sleep(1)
          ser.flushInput()
          ser.flushOutput()
          data=ser.read(12)
          s = data.decode("ascii")
          if (len(s) == 12) and (s[0] == "\n") and (s[11] == "\r"): #if the length of ID is as wanted
                return s[1:-1]
          return False

#function to read RFID and check if any of the current patients have that ID
def check_rfid():
  ID = validate_rfid()
  while not ID: #if the ID is not correct/not swiped, wait for user to swipe the correct ID
        print("Swipe the ID again.")
        ID = validate_rfid()
  for x in range(len(patients)):
    if(ID == patients[x].id):
       return x #return index of patient with that RFID if it exists in the array
  return -1 #return -1 (invalid index) id RFID currently belongs to no patient

#function to read the character pressed on keypad
def readkey():
    key, keys = keypad() #key is without shift and keys is for the shifted character
    if(GPIO.input(BUTTON) == 1): #if shift button is pressed
        keyf = keys
    else:
        keyf = key
    return(keyf)

#function to read and return the height (3 numbers) pressed on keypad
def readHeight():
    key1 = readkey() #read first digit
    print(key1, end = "") #print digits as you go to console so user can see what they are inputting
    time.sleep(1) #give user time to enter second digit
    key2 = readkey() #read second digit
    print(key2, end = "")
    time.sleep(1)
    key3 = readkey() #read third digit
    print(key3)
    time.sleep(1)
    height = (key1) * 100 + (key2) * 10 + key3 #concatenate the weighted digits to return the height
    return height

#function to read and return the weight (2 numbers) pressed on keypad
def readWeight():
    key1 = readkey() #read first digit
    print(key1, end = "")
    time.sleep(1) #give user time to enter second digit
    key2 = readkey() #read second digit
    print(key2)
    time.sleep(1)
    weight = (key1) * 10 + (key2) #concatenate the weighted digits to return the weight
    return weight

#function to get and return the spo2 of patients[idx] from the ADC and return it in %
def get_spo2(idx):
    print("Measure the patient's SPO2: ") #prompt user to use ADC to measure the spo2
    time.sleep(15) #allow the user time to measure the spo2
    LCD.clear()
    ADC_units= ADC.read(1) #reads from channel AIN1
    ADC.write(ADC_units)
    spo2 = (ADC_units * 100) / 256 #convert to %
    x = urllib.request.urlopen("http://api.thingspeak.com/update?api_key={}&field{}={}".format(API_KEY, idx+5, spo2)) #writes read value to appropriate ThingSpeak field
    if(spo2 < 80): #if SPO2 too low, say so on LCD
      LCD.write(0, 0, "      SPO2      ")
      LCD.write(0, 1, "    TOO LOW!    ")
    print(spo2) 
    return spo2

#function to get and return the heart rate of patients[idx] from the ADC and return it in bps
def get_heartrate(idx):
    print("Measure the patient's heart rate: ") #prompt user to use ADC to measure the heart rate
    time.sleep(15) #allow the user time to measure the heart rate
    LCD.clear()
    ADC_units= ADC.read(2) #reads from channel AIN2
    ADC.write(ADC_units)
    heartrate = (ADC_units * 200) / 256 #convert to bpm
    x = urllib.request.urlopen("http://api.thingspeak.com/update?api_key={}&field{}={}".format(API_KEY, idx+1, heartrate)) #writes read value to appropriate ThingSpeak field
    if(heartrate > 120): #if heart rate too high, say so on LCD
      LCD.write(0, 0, "   Heart Rate   ")
      LCD.write(0, 1, "   TOO HIGH!    ")
    elif(heartrate < 60): #if heart rate too low, say so on LCD
      LCD.write(0, 0, "   Heart Rate   ")
      LCD.write(0, 1, "    TOO LOW!    ")
    print(heartrate)
    return heartrate

#function to get and return temperature from DHT sensor
def get_temp():
      print("Measure the patient's temperature: ") #prompt user to use sensor to measure the temperature
      time.sleep(10) #allow the user time to measure the temperature
      result=""
      while (not result): #keep reading until humidity and temp are read
         result = DHT11.readDht11(9)
      if result:
         humidity, temperature = result
      print(temperature)
      return temperature

#function to check if patient is in bed based on distance from ultrasonic sensor
def get_inBed():
    print("Check if the patient is in bed: ") 
    time.sleep(5) #allow time for getting close/far from ultrasonic sensor (testing purposes)
    dis = distance() #read the distance from ultrasonic sensor
    if (dis<30): #if less than 30cm away from ultrasonic sensor
        print("Patient in bed")
        return True
    else:
        print("Patient not in bed")
        return False

#function to calculate the distance from the ultrasonic sensor
def distance():
    GPIO.output(TRIG, 0)
    time.sleep(0.000002)
    GPIO.output(TRIG, 1) #make trig pin high for 10us
    time.sleep(0.000001)
    GPIO.output(TRIG, 0)
    while GPIO.input(ECHO) == 0:
        a = 0
    time1 = time.time() #time signal becomes high
    while GPIO.input(ECHO) == 1:
        a = 0
    time2 = time.time() #time signal goes back to low
    duration = time2 - time1
    return duration*1000000/58 #sensor equation to calculate the distance in cm

#create and initialize a patient0 to represent an existing patient
patient0 = Patient("Zunaira", "5300C7E99B", 160, 50, 98, 36, 100, True) #plain rectangular
patients.append(patient0) #add patient0 to list of patients

#define target function for running flask on a thread to allow for parallelism
def flaskthread():
    if __name__ == '__main__':
        myapp.run(host = '0.0.0.0', port = 5040)
#Create flask thread
flask_t = threading.Thread(target =flaskthread)
flask_t.start() #start flask thread
time.sleep(5)

while True:
      choice = input("Type 1 for existing patient.\nType 2 for adding new patient.\n") #ask user if they want to swipe the ID of an existing or new patient
      if(choice=='1'): #existing patient
        print("Swipe your ID") #prompt user to swipe the ID and check that it is correct and existing
        idx = check_rfid()
        while idx == -1: #keep swiping ID until it is valid
            print("This is not an existing ID. Swipe again.")
            idx = check_rfid()
        print("Access Granted") #grant access to system when correct ID is swiped
        LCD.write(0, 0, "     ACCESS     ")
        LCD.write(0, 1, "    GRANTED!    ")
        patients[idx].printDetails() #print details of patient
        selection = input("Type u to update patient's details.\nType m to monitor the patient's details.\nType anything else to exit.")
        if selection == 'u': #to upload/overwrite data
          update = input("Type 1 for height.\nType 2 for weight.\nType 3 for spo2.\nType 4 for heart rate.\nType 5 for temperature.\nType n to leave.")
          while update != 'n': #user enter 'n' to leave uploading menu
            if(update == '1'): #height
              print("Enter the patient's height (three digits in cm): ") #prompt user
              height = readHeight() #read the height through keypad
              patients[idx].height = height #overwrite patient's height with new read height
            elif(update == '2'): #weight
              print("Enter the patient's weight (two digits in kg): ") #prompt user
              weight = readWeight() #read the weight through keypad
              patients[idx].weight = weight #overwrite patient's weight with new read weight
            elif(update == '3'): #spo2
              patients[idx].spo2 = get_spo2(idx) #read new spo2 and store in patient's details and upload to ThingSpeak
            elif(update == '4'): #heart rate
              patients[idx].heartrate = get_heartrate(idx) #read new heart rate and store in patient's details and upload to ThingSpeak
            elif(update == '5'): #temperature
              patients[idx].temp = get_temp() #overwrite patient's temp with new read temp
            update = input("Type 1 for height.\nType 2 for weight.\nType 3 for spo2.\nType 4 for heart rate.\nType 5 for temperature.\nType n to leave")
        elif selection == 'm': #monitor patient through flask
          print("Go to url: 10.25.32.112:5040/<desired route>")
          time.sleep(1)
      elif(choice=='2'): #new patient
        idx = len(patients) #index of new patient in the array 
        print("Swipe your new ID") #prompt user to swipe the ID and check that it is correct and not existing
        flag = check_rfid()
        while flag != -1:
          print("This ID is already in use. Swipe another ID.")
          flag = check_rfid()
        newID = validate_rfid() #new patient ID = RFID id 
        while not newID: #if the ID is not correct/not swiped, wait for user to swipe the correct ID
            print("Swipe the ID again.")
            newID = validate_rfid()
        name = input("Enter the patient's name: ") #prompt user to enter patient's name and store it
        print("Take patient's image.") 
        Mycamera.annotate_text = name + newID #annotate image with patient's name and ID
        Mycamera.start_preview() #preview of camera for 5s
        time.sleep(5)
        Mycamera.stop_preview()
        Mycamera.capture("/home/pi/PatientImage.jpg") #capture image and store in that path
        print("Enter the patient's height (three digits in cm): ")
        height = readHeight() #read and store patient's height
        print("Enter the patient's weight (two digits in kg): ")
        weight = readWeight() #read and store patient's weight
        heartrate = get_heartrate(idx) #read, store and upload patient's heart rate (checks if it is abnormal)
        spo2 = get_spo2(idx) #read, store and upload patient's spo2 (checks if it is too low)
        temp = get_temp() #read and store patient's temperature
        inBed = get_inBed() #check if patient is in bed
        p = Patient(name, newID, height, weight, spo2, temp, heartrate, inBed) #create patient variable with new parameters
        patients.append(p) #add patient to the array (database)
        