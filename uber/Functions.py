'''
getLocation1, getLocation, getDistance, getLocationDB, isValid_mobileNumber,
isValid_Name, isValid_email, isValid_Location
'''


from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.exc import GeocoderServiceError
from time import sleep
from geopy import distance
import cx_Oracle

def getLocation1(geolocator, lat, lng, attempt=1, max_attempt=15):
    try:
        #print(attempt)
        return geolocator.reverse([lat, lng], timeout=100, language='en')
    except (GeocoderTimedOut, GeocoderServiceError):
        if attempt % 4 == 0:
            sleep(1)

        if attempt <= max_attempt:
            return getLocation1(geolocator, lat, lng, attempt + 1, max_attempt)
        else:
            raise
    except:
        if attempt % 4 == 0:
            sleep(1)

        if attempt <= max_attempt:
            return getLocation1(geolocator, lat, lng, attempt + 1, max_attempt)
        else:
            raise


def getLocation(lat, lon):
    geolocator = Nominatim(user_agent="CAR")
    loc = getLocation1(geolocator, lat, lon)
    return loc.raw['address']


def getDistance(lat1, lon1, lat2, lon2):
    return distance.distance((lat1, lon1), (lat2, lon2)).km


def getLocationDB(lat, lon):
    '''

    :param lat: float
    :param lon: float
    :return: list containing a particular location info
    if location not present in database, first inserted
    '''
    connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM LOCATION WHERE LONGITUDE = :lonn AND LATITUDE = :latt", lonn=lon, latt = lat)
    loc = cursor.fetchall()


    if loc:
        loc = list(loc[0])
        cursor.close()
        connection.close()

        return loc

    location = getLocation(lat, lon)
    Street = ''
    City = ''
    postalCode = ''

    if 'village' in location and len(location['village']) <= 100:
        Street += location['village']
    if 'road' in location and (len(location['road']) + len(Street)) < 100:
        if len(Street) > 0:
            Street += ","
        Street += location['road']
    if 'neighbourhood' in location and (len(location['neighbourhood']) + len(Street)) < 100:
        if len(Street) > 0:
            Street += ","
        Street += location['neighbourhood']

    if 'suburb' in location and (len(location['suburb']) + len(Street)) < 100:
        if len(Street) > 0:
            Street += ","
        Street += location['suburb']

    if ('state_district' in location) and len(location['state_district']) <= 60:
        City = location['state_district']
    if (not City) and ('state' in location) and len(location['state']) <= 60:
        City = location['state']

    if 'postcode' in location:
        if len(location['postcode']) <= 20:
            postalCode = location['postcode']

    cursor.execute("INSERT INTO LOCATION(STREET, CITY, POSTAL_CODE, LONGITUDE, LATITUDE) VALUES ( :street, :city, :postcode, :lonn, :latt)", [Street, City, postalCode, lon, lat])

    connection.commit()

    cursor.execute("SELECT * FROM LOCATION WHERE LONGITUDE = :lonn AND LATITUDE = :latt", lonn=lon, latt=lat)
    loc = cursor.fetchall()

    cursor.close()
    connection.close()

    if loc:
        loc = list(loc[0])
        return loc


def isValid_mobileNumber(numberString):

    '''

    :param numberString: mobile number as string
    :return: True or False
    '''

    if len(numberString) != 11:
        return False
    elif numberString[0] != '0' or numberString[1] != '1':
        return False
    else:
        for i in range(2, 11):
            if not (numberString[i] >= '0' and numberString[i] <= '9'):
                return False

        return True


def isValid_Name(firstName, middleName, lastName):

    '''

    :param firstName: string
    :param middleName: string
    :param lastName: string
    :return: a list containing error message
    '''

    inputLst = [firstName, middleName, lastName]

    errorLst = []

    for i in range(3):
        flag = False
        if i == 0:
            name = "First Name"
        elif i == 1:
            name = "Middle Name"
        else:
            name = "Last Name"

        if inputLst[i] and len(inputLst[i]) > 40:
            errorLst.append(name + " too long!")
        elif inputLst[i]:
            for ch in inputLst[i]:
                if not ((ch >= 'a' and ch <= 'z') or (ch >= 'A' and ch <= 'Z')):
                    flag = True
                    break

            if flag:
                errorLst.append( "Invalid " + name)

    return errorLst


def isValid_email(email):
    '''

    :param email: Email string
    :return: a list containing error message if any
    '''

    emailOk = 0

    if len(email) > 50:
        return ["Email too long!"]
    else:
        for i in range(0, len(email)):
            if email[i] == '@':
                emailOk = emailOk + 1
                if i == 0:
                    return ["Invalide email"]
                else:
                    for j in range(i + 1, len(email)):
                        if email[j] == '.':
                            emailOk = emailOk + 1
                            if j == i + 1:
                                return ["Invalid email"]
                            else:
                                if j == len(email) - 1:
                                    return ["Invalid email"]
                                for k in range(j + 1, len(email)):
                                    if email[k] == '@' or email[k] == '.':
                                        return ["Invalid email"]

                            break

                break

        if emailOk == 2:
            return []
        else:
            return ["Invalid email"]


def isValid_Location(lat, lon):
    '''

    :param lat: float
    :param lon: float
    :return: list of error message
    '''

    errorLst = []
    if lat < -90 or lat > 90:
        errorLst.append("Invalid Latitude!")
    if lon < -180 or lon > 180:
        errorLst.append("Invalid longitude!")

    return errorLst


def isValid_image(image):
    """

    :param image: string location in media
    :return: list of error
    """

    formatLst = ['bmp', 'dib', 'jpg', 'jpeg', 'jpe', 'jfif', 'tif', 'tiff', 'png']

    if len(image) > 50:
        return ["Image file name too long!"]
    else:
        pos = image.rfind('.')
        if pos != -1:
            ext = image[pos + 1 : len(image)]
            for i in range(len(formatLst)):
                if formatLst[i] == ext:
                    return []
            return ["Unsupported file!"]

        else:
            return ["Invalid file!"]



def user_mobileNumbers(user_id):
    connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
    cursor = connection.cursor()

    cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE USER_ID = :userId", userId = user_id)

    numbers = cursor.fetchall()
    num = []
    if numbers:
        for i in range(len(numbers)):
            num.append(numbers[i][0])

    return num


def driver_mobileNumbers(user_id):
    connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
    cursor = connection.cursor()

    cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE DRIVER_ID = :userId", userId=user_id)

    numbers = cursor.fetchall()
    num = []
    if numbers:
        for i in range(len(numbers)):
            num.append(numbers[i][0])

    return num


def admin_mobileNumbers(user_id):
    connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
    cursor = connection.cursor()

    cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE ADMIN_ID = :userId", userId=user_id)

    numbers = cursor.fetchall()
    num = []
    if numbers:
        for i in range(len(numbers)):
            num.append(numbers[i][0])

    return num