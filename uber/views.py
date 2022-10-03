"""
This view file contains
userSignUp, userLogin, driverSignUp, driverLogin, acceptRequest, newRequest
index, userHomePage, driverHomePage, userCancelRequest, driverCancelRequest, userDeleteAccount view functions
#index,adminSignUp,adminLogin
"""

from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render, get_object_or_404
from django.urls import reverse
import cx_Oracle
from datetime import datetime, timedelta
import time
from . import Functions
from django.core.files.storage import FileSystemStorage

#index,adminSignUp,adminLogin

def index(request):
	'''

	:return: loads UBER Home page
	'''

	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT ADMIN_ID FROM ADMIN")
	data = cursor.fetchall()

	context= {}

	if data:
		context['admin'] = True

	cursor.close()
	connection.close()
	return render(request, 'uber/index.html', context)

#index,adminSignUp,adminLogin

def adminSignUp(request):
	if request.method == 'POST':
		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		# ===============if add admin====================
		adminId1 = ''

		if 'adminId' in request.POST:
			adminId1 = request.POST['adminId']
			if 'firstName' not in request.POST:
				return render(request, 'uber/adminSignUp.html', {
					'adminId': adminId1,
				})

		updateId  = ''

		if 'updateId' in request.POST:
			updateId = request.POST['updateId']
			updateId = int(updateId)

			if 'firstName' not in request.POST:
				cursor.execute("SELECT FIRST_NAME, MIDDLE_NAME, LAST_NAME, USERNAME, PASSWORD, EMAIL, DATE_OF_BIRTH, LATITUDE, LONGITUDE, PHOTO FROM ADMIN A, LOCATION L WHERE A.ADMIN_ID = :admin_id AND A.LOCATION_ID = L.LOCATION_ID", admin_id = updateId)



				inputLst = cursor.fetchall()
				if inputLst:
					inputLst = list(inputLst[0])
					inputLst.insert(5, '')

				if not inputLst[1]:
					inputLst[1] = ''
				if not inputLst[2]:
					inputLst[2] = ''
				if not inputLst[10]:
					inputLst[10] = ''

				errorLst = []
				errorLst.append("OK")

				return render(request, 'uber/adminSignUp.html', {
					'inputLst': inputLst,
					'updateId': updateId,
					'errorLst': errorLst,
					'noError': "OK",
				})




		#if add admin==================================
		inputLst = []  # contains the received data from sing up form
		inputLst.append(request.POST['firstName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['middleName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['lastName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()

		inputLst.append(request.POST['userName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['passWord'])
		inputLst.append(request.POST['mobileNumber'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()

		inputLst.append(request.POST['email'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['birthDay'])
		inputLst.append(request.POST['lat'])
		inputLst.append(request.POST['lon'])

		hasImage = False

		if 'document' in request.FILES:
			hasImage = True

		if hasImage:
			image_file = request.FILES['document']
		#this has been used later, just before inserting into db

		errorLst = []

		# for first, middle and last name

		errorLst.extend(Functions.isValid_Name(inputLst[0], inputLst[1], inputLst[2]))

		#for username - 3      =================================

		errorLst.append('')

		if updateId:
			cursor.execute("SELECT USERNAME FROM ADMIN WHERE ADMIN_ID != :admin_id AND USERNAME = :username", admin_id = updateId, username=inputLst[3])
		else:
			cursor.execute("SELECT USERNAME FROM ADMIN WHERE USERNAME = :username", username=inputLst[3])

		checkLst= cursor.fetchall()

		if checkLst:
			errorLst[len(errorLst) - 1] = 'Username already taken!'
		elif len(inputLst[3]) > 40:
			errorLst[len(errorLst) - 1] = 'User Name too long!'

		# ================================== for passowrd - 4

		errorLst.append('')
		if len(inputLst[4]) > 40:
			errorLst[len(errorLst) - 1] = 'Password too long!'
		elif len(inputLst[4]) <= 3:
			errorLst[len(errorLst) - 1] = 'Password too short!'

		#=================================== for mobile number - 5
		mobNumExist = False
		sameMob = False

		mobNumOk = Functions.isValid_mobileNumber(inputLst[5])

		if mobNumOk:

			cursor.execute("SELECT * FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mob_num", mob_num=inputLst[5])
			checkLst = cursor.fetchall()

			if not checkLst or not checkLst[0][3]:
				if checkLst:
					mobNumExist = True
			elif checkLst[0][3] == updateId:
				sameMob = True
			else:
				errorLst.append("Mobile number already taken!")
		else:
			errorLst.append("Invalide Mobile Number")

		#=================================for email - 6

		retLst = Functions.isValid_email(inputLst[6])
		if retLst:
			errorLst.extend(retLst)
		else:
			if updateId:
				cursor.execute("SELECT EMAIL FROM ADMIN WHERE EMAIL = :email AND ADMIN_ID != :admin_id", email=inputLst[6], admin_id = updateId)
			else:
				cursor.execute("SELECT EMAIL FROM ADMIN WHERE EMAIL = :email", email=inputLst[6])

			tempEmail = cursor.fetchall()
			if tempEmail:
				errorLst.append("Email ID is already taken by another user!")


		#=================================for birthday - 7

		if datetime.strptime(inputLst[7], "%Y-%m-%d") > datetime.now() - timedelta(days=365 * 20):
			errorLst.append("age must be more than 20 years!")

		#=================================for location: latitude - 8, longitude - 9

		errorLst.extend(Functions.isValid_Location(float(inputLst[8]), float(inputLst[9])))

		#===============================image - error check ================

		if hasImage:
			errorLst.extend(Functions.isValid_image(image_file.name))

		isOK = True
		for val in errorLst:
			if val:
				isOK = False
				break

		if not isOK:
			return render(request, 'uber/adminSignUp.html', {
				'inputLst': inputLst,
				'errorLst': errorLst,
				'adminId' : adminId1,
				'updateId': updateId,
			})

		#All data verified now - now we will update data in database
		#================now saving image - 10 ===================================
		if hasImage:
			fs = FileSystemStorage()
			image_file_name = fs.save('images/' + image_file.name, image_file)
			url = fs.url(image_file_name)
			urlDB = '../../../..' + url
			inputLst.append(urlDB)  # at index 10
		else:
			inputLst.append('')

		if updateId and (not inputLst[10]):
			if 'image' in request.POST:
				inputLst[10] = request.POST['image']

		# for location ID - 11

		cursor.close()
		connection.close()

		inputLst.append(Functions.getLocationDB(float(inputLst[8]), float(inputLst[9]))[0])

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		if updateId:
			cursor.execute("UPDATE ADMIN SET FIRST_NAME = :firstName, MIDDLE_NAME =:middleName, LAST_NAME = :lastName, USERNAME = :username, PASSWORD = :passWord, EMAIL = :email, PHOTO = :photo, DATE_OF_BIRTH = TO_DATE(:date_of_birth, 'YYYY-MM-DD'), LOCATION_ID = :loc_id WHERE ADMIN_ID = :admin_id", [inputLst[0], inputLst[1], inputLst[2], inputLst[3], inputLst[4], inputLst[6], inputLst[10], inputLst[7], inputLst[11], updateId])
		else:
			cursor.execute("INSERT INTO ADMIN(FIRST_NAME, MIDDLE_NAME, LAST_NAME, USERNAME, PASSWORD, EMAIL,JOIN_DATE, SALARY, PHOTO, DATE_OF_BIRTH, LOCATION_ID ) VALUES(:firstName, :middleName, :lastName, :userName, :passWord, :email, :join_date, :salary, :photo, TO_DATE(:date_of_birth, 'YYYY-MM-DD'), :location_id)",[inputLst[0], inputLst[1], inputLst[2], inputLst[3], inputLst[4], inputLst[6], datetime.now(), 50000,
				 inputLst[10], inputLst[7], inputLst[11]])

		connection.commit()

		cursor.execute("SELECT ADMIN_ID FROM ADMIN WHERE USERNAME = :userName", userName=inputLst[3])

		checkLst = cursor.fetchall()

		adminId = checkLst[0][0]

		if mobNumExist:
			cursor.execute("UPDATE MOBILE_NUMBERS SET ADMIN_ID = :admin_id WHERE MOBILE_NUMBER = : mobNum", [adminId, inputLst[5]])
			connection.commit()
		elif sameMob:
			pass
		else:
			cursor.execute("INSERT INTO MOBILE_NUMBERS(MOBILE_NUMBER, ADMIN_ID) VALUES (:mobNum, :user_id)", [inputLst[5], adminId])
			connection.commit()

		cursor.close()
		connection.close()

		if adminId1:
			return HttpResponseRedirect(reverse('uber:adminHomePage', args=(adminId1,)))
		elif updateId:
			return HttpResponseRedirect(reverse('uber:adminHomePage', args=(updateId,)))

		return HttpResponseRedirect(reverse('uber:adminLogin'))


	else:
		return render(request, 'uber/adminSignUp.html')

#index,adminSignUp,adminLogin, adminHomePage

def adminLogin(request):
	if request.method == 'POST':
		inputLst = []
		inputLst.append(request.POST['userName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['passWord'])

		errorLst = []

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT ADMIN_ID FROM ADMIN WHERE USERNAME = :userName", userName = inputLst[0])
		checkLst = cursor.fetchall()

		if not checkLst:
			cursor.execute("SELECT ADMIN_ID FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mob_num", mob_num=inputLst[0])
			checkLst = cursor.fetchall()

			if not checkLst:
				cursor.execute("SELECT ADMIN_ID FROM ADMIN WHERE EMAIL = :email", email=inputLst[0])
				checkLst = cursor.fetchall()

		if checkLst:
			cursor.execute("SELECT PASSWORD FROM ADMIN WHERE ADMIN_ID = :adminId", adminId = checkLst[0][0])
			passWord = cursor.fetchall()
			adminId = checkLst[0][0]

			if passWord:
				passWord = passWord[0][0]
			if passWord != inputLst[1]:
				errorLst.append("Invalid Password")
			else:
				return HttpResponseRedirect(reverse('uber:adminHomePage', args=(adminId,)))
		else:
			errorLst.append("Invalid username/mobile number/email")

		cursor.close()
		connection.close()

		return render(request, 'uber/adminLogin.html', {
			'inputLst': inputLst,
			'errorLst': errorLst,
		})

	else:
		return render(request, 'uber/adminLogin.html')

#index,adminSignUp,adminLogin, adminHomePage, userSignUp

def adminHomePage(request, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM ADMIN WHERE ADMIN_ID = :adminId", adminId=admin_id)

	checkLst = cursor.fetchall()

	if not checkLst:
		return render(request, 'uber/adminLogin.html')

	# add for showing admin info =====================
	userInfo = list(checkLst[0])

	if not userInfo[9]:
		userInfo[9] = "../../../../media/images/dummy.jpg"

	cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE ADMIN_ID = :adminId", adminId=admin_id)
	nums = []
	for line in cursor:
		nums.append(line[0])

	userInfo.append(nums)
	# ======================================================================= change ======================================================
	##only the next line
	cursor.execute(
		"SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id",
		loc_id=userInfo[11])

	line = cursor.fetchall()
	userInfo.append(list(line[0]))
	# ========end of add for showing admin info==========

	cursor.execute(
		"SELECT * FROM CAR WHERE NVL(INS_END_DATE, SYSDATE - INTERVAL '2' MONTH) > : now AND NVL(LAST_PAYMENT_DATE, SYSDATE) <= :last_payment_date AND OWNER_USER_ID IS NOT NULL",
		now=datetime.now(), last_payment_date=datetime.now() - timedelta(days=30))
	# last_payment_date should be = datetime.now() - timedelta(days=30)
	# we have done that to only to see data at development time

	carLst = cursor.fetchall()

	if carLst:

		for i in range(len(carLst)):
			carLst[i] = list(carLst[i])
			if carLst[i][9]:
				if carLst[i][6] == 'Annual':
					monthlyRent = 10000
				elif carLst[i][6] == 'Biennial':
					monthlyRent = 12000
				else:
					monthlyRent = 15000

				today = datetime.today()
				last_payment_day = carLst[i][9]
				dif = today - last_payment_day
				carLst[i][9] = round(float(monthlyRent) * dif.days / 30)
				carLst[i].append(last_payment_day)

				cursor.execute("SELECT USER_NAME(USER_ID), USERNAME, EMAIL, NVL(PHOTO, :dummy), DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID) FROM APP_USER WHERE USER_ID = :userId", dummy='../../../../media/images/dummy.jpg', userId=carLst[i][4])

				data = cursor.fetchall()

				if data:
					data = list(data[0])
					data.append(Functions.user_mobileNumbers(carLst[i][4]))
					carLst[i].append(data)

	return render(request, 'uber/adminHomePage.html', {
		'userInfo': userInfo,
		'carLst': carLst,
	})


#index,adminSignUp,adminLogin,
# adminHomePage, userSignUp,driverSignUp

def userSignUp(request):
	if request.method == 'POST':

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		updateId = ''
		#updateId will contain the user_id if update request
		# for info update of an existing driver

		if 'updateId' in request.POST:
			updateId = request.POST['updateId']
			updateId = int(updateId)

			if 'firstName' not in request.POST:
				cursor.execute("SELECT FIRST_NAME, MIDDLE_NAME, LAST_NAME, USERNAME, PASSWORD, EMAIL, DATE_OF_BIRTH, LATITUDE, LONGITUDE, PHOTO FROM APP_USER U, LOCATION L WHERE U.USER_ID = :user_id AND U.LOCATION_ID = L.LOCATION_ID", user_id=updateId)

				inputLst = cursor.fetchall()
				if inputLst:
					inputLst = list(inputLst[0])
					inputLst.insert(5, '')

				if not inputLst[1]:
					inputLst[1] = ''
				if not inputLst[2]:
					inputLst[2] = ''
				if not inputLst[10]:
					inputLst[10] = ''

				errorLst = []
				errorLst.append("OK")

				return render(request, 'uber/userSignUp.html', {
					'inputLst': inputLst,
					'updateId': updateId,
					'errorLst': errorLst,
					'noError': "OK",
				})

		inputLst = []  # contains the received data from sing up form
		inputLst.append(request.POST['firstName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['middleName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['lastName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()

		inputLst.append(request.POST['userName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['passWord'])
		inputLst.append(request.POST['mobileNumber'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()

		inputLst.append(request.POST['email'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['birthDay'])
		inputLst.append(request.POST['lat'])
		inputLst.append(request.POST['lon'])

		hasImage = False

		if 'document' in request.FILES:
			hasImage = True

		if hasImage:
			image_file = request.FILES['document']
		#this has been used later, just before inserting into db

		errorLst = []

		# for first, middle and last name

		errorLst.extend(Functions.isValid_Name(inputLst[0], inputLst[1], inputLst[2]))

		#for username - 3      =================================

		errorLst.append('')

		if updateId:
			cursor.execute("SELECT USERNAME FROM APP_USER WHERE USER_ID != :user_id AND USERNAME = :username", user_id=updateId, username=inputLst[3])
		else:
			cursor.execute("SELECT USERNAME FROM APP_USER WHERE USERNAME = :username", username=inputLst[3])

		checkLst= cursor.fetchall()

		if checkLst:
			errorLst[len(errorLst) - 1] = 'Username already taken!'
		elif len(inputLst[3]) > 40:
			errorLst[len(errorLst) - 1] = 'User Name too long!'

		# ================================== for passowrd - 4

		errorLst.append('')
		if len(inputLst[4]) > 40:
			errorLst[len(errorLst) - 1] = 'Password too long!'
		elif len(inputLst[4]) <= 3:
			errorLst[len(errorLst) - 1] = 'Password too short!'

		#=================================== for mobile number - 5
		mobNumExist = False

		mobNumOk = Functions.isValid_mobileNumber(inputLst[5])
		sameMob = False

		if mobNumOk:
			cursor.execute("SELECT * FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mob_num", mob_num=inputLst[5])
			checkLst = cursor.fetchall()

			if not checkLst or not checkLst[0][1]:
				if checkLst:
					mobNumExist = True
			elif checkLst[0][1] == updateId:
				sameMob = True
			else:
				errorLst.append("Mobile number already taken!")
		else:
			errorLst.append("Invalid Mobile Number")

		#=================================for email - 6

		retLst = Functions.isValid_email(inputLst[6])
		if retLst:
			errorLst.extend(retLst)
		else:
			if updateId:
				cursor.execute("SELECT EMAIL FROM APP_USER WHERE EMAIL = :email AND USER_ID != :user_id", email=inputLst[6], user_id=updateId)
			else:
				cursor.execute("SELECT EMAIL FROM APP_USER WHERE EMAIL = :email", email=inputLst[6])

			tempEmail = cursor.fetchall()
			if tempEmail:
				errorLst.append("Email ID is already taken by another user!")


		#=================================for birthday - 7

		if datetime.strptime(inputLst[7], "%Y-%m-%d") > datetime.now() - timedelta(days=365 * 10):
			errorLst.append("Your age must be more than 10 years!")

		#=================================for location: latitude - 8, longitude - 9

		errorLst.extend(Functions.isValid_Location(float(inputLst[8]), float(inputLst[9])))

		#===============================image - error check ================

		if hasImage:
			errorLst.extend(Functions.isValid_image(image_file.name))

		isOK = True
		for val in errorLst:
			if val:
				isOK = False
				break

		if not isOK:
			return render(request, 'uber/userSignUp.html', {
				'inputLst': inputLst,
				'errorLst': errorLst,
				'updateId': updateId,
			})

		#All data verified now - now we will update data in database
		#================now saving image - 10 ===================================
		if hasImage:
			fs = FileSystemStorage()
			image_file_name = fs.save('images/' + image_file.name, image_file)
			url = fs.url(image_file_name)
			urlDB = '../../../..' + url
			inputLst.append(urlDB)  # at index 10
		else:
			inputLst.append('')

		if updateId and (not inputLst[10]):
			if 'image' in request.POST:
				inputLst[10] = request.POST['image']

		# for location ID - 11

		cursor.close()
		connection.close()

		inputLst.append(Functions.getLocationDB(float(inputLst[8]), float(inputLst[9]))[0])

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		if updateId:
			cursor.execute("UPDATE APP_USER SET FIRST_NAME = :firstName, MIDDLE_NAME =:middleName, LAST_NAME = :lastName, USERNAME = :username, PASSWORD = :passWord, EMAIL = :email, PHOTO = :photo, DATE_OF_BIRTH = TO_DATE(:date_of_birth, 'YYYY-MM-DD'), LOCATION_ID = :loc_id WHERE USER_ID = :user_id", [inputLst[0], inputLst[1], inputLst[2], inputLst[3], inputLst[4], inputLst[6], inputLst[10], inputLst[7], inputLst[11], updateId])
		else:
			cursor.execute("INSERT INTO APP_USER(FIRST_NAME, MIDDLE_NAME, LAST_NAME, USERNAME, PASSWORD, EMAIL, PHOTO, DATE_OF_BIRTH, LOCATION_ID ) VALUES(:firstName, :middleName, :lastName, :userName, :passWord, :email, :photo, TO_DATE(:date_of_birth, 'YYYY-MM-DD'), :location_id)", [inputLst[0], inputLst[1], inputLst[2], inputLst[3], inputLst[4], inputLst[6], inputLst[10], inputLst[7], inputLst[11]])

		connection.commit()

		cursor.execute("SELECT USER_ID FROM APP_USER WHERE USERNAME = :userName", userName=inputLst[3])

		checkLst = cursor.fetchall()

		userId = checkLst[0][0]

		if mobNumExist:
			cursor.execute("UPDATE MOBILE_NUMBERS SET USER_ID = :user_id WHERE MOBILE_NUMBER = : mobNum", [userId, inputLst[5]])
			connection.commit()
		elif sameMob:
			pass
		else:
			cursor.execute("INSERT INTO MOBILE_NUMBERS(MOBILE_NUMBER, USER_ID) VALUES (:mobNum, :user_id)", [inputLst[5], userId])
			connection.commit()

		cursor.close()
		connection.close()

		if updateId:
			return HttpResponseRedirect(reverse('uber:userHomePage', args=(updateId,)))

		return HttpResponseRedirect(reverse('uber:userLogin'))


	else:
		return render(request, 'uber/userSignUp.html')

#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin

def driverSignUp(request):
	if request.method == 'POST':

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		updateId = ''
		# for info update of an existing driver

		if 'updateId' in request.POST:
			updateId = request.POST['updateId']
			updateId = int(updateId)

			if 'firstName' not in request.POST:
				cursor.execute("SELECT FIRST_NAME, MIDDLE_NAME, LAST_NAME, USERNAME, PASSWORD, EMAIL, DATE_OF_BIRTH, LATITUDE, LONGITUDE, PHOTO FROM DRIVER D, LOCATION L WHERE D.DRIVER_ID = :driver_id AND D.LOCATION_ID = L.LOCATION_ID", driver_id=updateId)

				inputLst = cursor.fetchall()
				if inputLst:
					inputLst = list(inputLst[0])
					inputLst.insert(5, '')

				if not inputLst[1]:
					inputLst[1] = ''
				if not inputLst[2]:
					inputLst[2] = ''
				if not inputLst[10]:
					inputLst[10] = ''

				errorLst = []
				errorLst.append("OK")

				return render(request, 'uber/driverSignUp.html', {
					'inputLst': inputLst,
					'updateId': updateId,
					'errorLst': errorLst,
					'noError': "OK",
				})


		inputLst = []  # contains the received data from sing up form
		inputLst.append(request.POST['firstName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['middleName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['lastName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()

		inputLst.append(request.POST['userName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['passWord'])
		inputLst.append(request.POST['mobileNumber'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()

		inputLst.append(request.POST['email'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['birthDay'])
		inputLst.append(request.POST['lat'])
		inputLst.append(request.POST['lon'])

		hasImage = False

		if 'document' in request.FILES:
			hasImage = True

		if hasImage:
			image_file = request.FILES['document']
		#this has been used later, just before inserting into db

		errorLst = []

		# for first, middle and last name

		errorLst.extend(Functions.isValid_Name(inputLst[0], inputLst[1], inputLst[2]))

		#for username - 3      =================================

		errorLst.append('')

		if updateId:
			cursor.execute("SELECT USERNAME FROM DRIVER WHERE DRIVER_ID != :driver_id AND USERNAME = :username", driver_id=updateId, username=inputLst[3])
		else:
			cursor.execute("SELECT USERNAME FROM DRIVER WHERE USERNAME = :username", username=inputLst[3])

		checkLst= cursor.fetchall()

		if checkLst:
			errorLst[len(errorLst) - 1] = 'Username already taken!'
		elif len(inputLst[3]) > 40:
			errorLst[len(errorLst) - 1] = 'User Name too long!'

		# ================================== for passowrd - 4

		errorLst.append('')
		if len(inputLst[4]) > 40:
			errorLst[len(errorLst) - 1] = 'Password too long!'
		elif len(inputLst[4]) <= 3:
			errorLst[len(errorLst) - 1] = 'Password too short!'

		#=================================== for mobile number - 5
		mobNumExist = False

		mobNumOk = Functions.isValid_mobileNumber(inputLst[5])
		sameMob = False

		if mobNumOk:
			cursor.execute("SELECT * FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mob_num", mob_num=inputLst[5])
			checkLst = cursor.fetchall()

			if not checkLst or not checkLst[0][2]:
				if checkLst:
					mobNumExist = True
			elif checkLst[0][2] == updateId:
				sameMob = True
			else:
				errorLst.append("Mobile number already taken!")
		else:
			errorLst.append("Invalid Mobile Number")

		#=================================for email - 6

		retLst = Functions.isValid_email(inputLst[6])
		if retLst:
			errorLst.extend(retLst)
		else:
			if updateId:
				cursor.execute("SELECT EMAIL FROM DRIVER WHERE EMAIL = :email AND DRIVER_ID != :driver_id", email=inputLst[6], driver_id=updateId)
			else:
				cursor.execute("SELECT EMAIL FROM DRIVER WHERE EMAIL = :email", email=inputLst[6])


			tempEmail = cursor.fetchall()
			if tempEmail:
				errorLst.append("Email ID is already taken by another user!")


		#=================================for birthday - 7

		if datetime.strptime(inputLst[7], "%Y-%m-%d") > datetime.now() - timedelta(days=365 * 18):
			errorLst.append("Your age must be more than 18 years!")

		#=================================for location: latitude - 8, longitude - 9

		errorLst.extend(Functions.isValid_Location(float(inputLst[8]), float(inputLst[9])))

		#===============================image - error check ================

		if hasImage:
			errorLst.extend(Functions.isValid_image(image_file.name))

		isOK = True
		for val in errorLst:
			if val:
				isOK = False
				break

		if not isOK:
			return render(request, 'uber/driverSignUp.html', {
				'inputLst': inputLst,
				'errorLst': errorLst,
				'updateId': updateId,
			})

		#All data verified now - now we will update data in database
		#================now saving image - 10 ===================================
		if hasImage:
			fs = FileSystemStorage()
			image_file_name = fs.save('images/' + image_file.name, image_file)
			url = fs.url(image_file_name)
			urlDB = '../../../..' + url
			inputLst.append(urlDB)  # at index 10
		else:
			inputLst.append('')

		if updateId and (not inputLst[10]):
			if 'image' in request.POST:
				inputLst[10] = request.POST['image']

		# for location ID - 11

		cursor.close()
		connection.close()

		inputLst.append(Functions.getLocationDB(float(inputLst[8]), float(inputLst[9]))[0])

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		if updateId:
			cursor.execute("UPDATE DRIVER SET FIRST_NAME = :firstName, MIDDLE_NAME =:middleName, LAST_NAME = :lastName, USERNAME = :username, PASSWORD = :passWord, EMAIL = :email, PHOTO = :photo, DATE_OF_BIRTH = TO_DATE(:date_of_birth, 'YYYY-MM-DD'), LOCATION_ID = :loc_id WHERE DRIVER_ID = :driver_id", [inputLst[0], inputLst[1], inputLst[2], inputLst[3], inputLst[4], inputLst[6], inputLst[10],
				 inputLst[7], inputLst[11], updateId])
		else:
			cursor.execute("INSERT INTO DRIVER(FIRST_NAME, MIDDLE_NAME, LAST_NAME, USERNAME, PASSWORD, EMAIL, PHOTO, DATE_OF_BIRTH, LOCATION_ID ) VALUES(:firstName, :middleName, :lastName, :userName, :passWord, :email, :photo, TO_DATE(:date_of_birth, 'YYYY-MM-DD'), :location_id)", [inputLst[0], inputLst[1], inputLst[2], inputLst[3], inputLst[4], inputLst[6], inputLst[10],
				 inputLst[7], inputLst[11]])

		connection.commit()

		cursor.execute("SELECT DRIVER_ID FROM DRIVER WHERE USERNAME = :userName", userName=inputLst[3])

		checkLst = cursor.fetchall()

		driverId = checkLst[0][0]

		if mobNumExist:
			cursor.execute("UPDATE MOBILE_NUMBERS SET DRIVER_ID = :driver_id WHERE MOBILE_NUMBER = : mobNum", [driverId, inputLst[5]])
			connection.commit()
		elif sameMob:
			pass
		else:
			cursor.execute("INSERT INTO MOBILE_NUMBERS(MOBILE_NUMBER, DRIVER_ID) VALUES (:mobNum, :driver_id)", [inputLst[5], driverId])
			connection.commit()

		cursor.close()
		connection.close()

		if updateId:
			return HttpResponseRedirect(reverse('uber:driverHomePage', args=(updateId,)))

		return HttpResponseRedirect(reverse('uber:driverLogin'))


	else:
		return render(request, 'uber/driverSignUp.html')

#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin

def userLogin(request):
	if request.method == 'POST':
		inputLst = []
		inputLst.append(request.POST['userName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['passWord'])

		errorLst = []

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT USER_ID FROM APP_USER WHERE USERNAME = :userName", userName = inputLst[0])
		checkLst = cursor.fetchall()

		if not checkLst:
			cursor.execute("SELECT USER_ID FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mob_num", mob_num=inputLst[0])
			checkLst = cursor.fetchall()

			if not checkLst:
				cursor.execute("SELECT USER_ID FROM APP_USER WHERE EMAIL = :email", email=inputLst[0])
				checkLst = cursor.fetchall()

		if checkLst:
			cursor.execute("SELECT PASSWORD FROM APP_USER WHERE USER_ID = :userId", userId = checkLst[0][0])
			passWord = cursor.fetchall()
			userId = checkLst[0][0]
			if passWord:
				passWord = passWord[0][0]
			if passWord != inputLst[1]:
				errorLst.append("Invalid Password")
			else:
				return HttpResponseRedirect(reverse('uber:userHomePage', args=(userId,)))
		else:
			errorLst.append("Invalid username/mobile number/email")

		cursor.close()
		connection.close()

		return render(request, 'uber/userLogin.html', {
			'inputLst': inputLst,
			'errorLst': errorLst,
		})

	else:
		return render(request, 'uber/userLogin.html')

#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage,

def driverLogin(request):
	if request.method == 'POST':
		inputLst = []
		inputLst.append(request.POST['userName'])
		inputLst[len(inputLst) - 1] = inputLst[len(inputLst) - 1].strip()
		inputLst.append(request.POST['passWord'])

		errorLst = []

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT DRIVER_ID FROM DRIVER WHERE USERNAME = :userName", userName = inputLst[0])
		checkLst = cursor.fetchall()

		if not checkLst:
			cursor.execute("SELECT DRIVER_ID FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mob_num", mob_num=inputLst[0])
			checkLst = cursor.fetchall()

			if not checkLst:
				cursor.execute("SELECT DRIVER_ID FROM DRIVER WHERE EMAIL = :email", email=inputLst[0])
				checkLst = cursor.fetchall()

		if checkLst:
			cursor.execute("SELECT PASSWORD FROM DRIVER WHERE DRIVER_ID = :driverId", driverId = checkLst[0][0])
			passWord = cursor.fetchall()
			driverId = checkLst[0][0]
			if passWord:
				passWord = passWord[0][0]
			if passWord != inputLst[1]:
				errorLst.append("Invalid Password")
			else:
				return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driverId,)))
		else:
			errorLst.append("Invalid username/mobile number/email")

		cursor.close()
		connection.close()

		return render(request, 'uber/driverLogin.html', {
			'inputLst': inputLst,
			'errorLst': errorLst,
		})

	else:
		return render(request, 'uber/driverLogin.html')
#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage

def userHomePage(request, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM APP_USER WHERE USER_ID = :userId", userId=user_id)
	messages = ''

	checkLst = cursor.fetchall()

	if not checkLst:
		return render(request, 'uber/userLogin.html')

	# add for showing user info =====================
	userInfo = list(checkLst[0])

	if not userInfo[9]:
		userInfo[9] = "../../../media/images/dummy.jpg"

	cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE USER_ID = :userId", userId=user_id)
	nums = []
	for line in cursor:
		nums.append(line[0])

	userInfo.append(nums)
#======================================================================= change ======================================================
	##only the next line
	cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id",
				   loc_id=userInfo[11])

	line = cursor.fetchall()
	userInfo.append(list(line[0]))

	cursor.execute("SELECT * FROM REQUEST WHERE USER_ID = :userID AND NVL(STATUS, 'dummy') = :status AND END_TIME >= :endTime AND DRIVER_ID IS NOT NULL", userID = user_id, status="Complete", endTime = datetime.now() - timedelta(days=3))

	unratedData = cursor.fetchall()

	if unratedData:
		for i in range(len(unratedData)):
			unratedData[i] = list(unratedData[i])

			cursor.execute("SELECT * FROM DRIVER WHERE DRIVER_ID = :driverId", driverId=unratedData[i][8])

			driverData = cursor.fetchall()
			if driverData:
				driverData = list(driverData[0])
				if driverData[7]:
					driverData[7] = round(float(driverData[7]) / driverData[8], 0)

			unratedData[i][8] = driverData

	# ========end of add for showing user info==========

	#Checking if there is a new request for this user

	cursor.execute("SELECT * FROM REQUEST WHERE USER_ID = :userId  AND END_TIME >= :end_time AND STATUS IS NULL", userId = user_id, end_time=datetime.now())
	requestData = cursor.fetchall()
	riderInfo = []
	for_js = 100

	if not requestData:
		cursor.execute("SELECT * FROM REQUEST WHERE USER_ID = :userId AND NVL(STATUS, 'dummy') = :status", userId = user_id, status = 'Incomplete')
		requestData = cursor.fetchall()

	carInfo = ''

	if requestData:
		requestData = list(requestData[0])

		for_js = int(time.mktime(requestData[2].timetuple())) * 1000


		if requestData[8]:#if there is a rider found
			cursor.execute("SELECT * FROM DRIVER WHERE DRIVER_ID = :driver_id", driver_id = requestData[8])

			for line in cursor:
				riderInfo = list(line)

			cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE DRIVER_ID = :driver_id", driver_id = requestData[8])
			#from index 12 in riderInfo

			nums = []
			for line in cursor:
				nums.append(line[0])

			riderInfo.append(nums)

			cursor.execute("SELECT * FROM CAR WHERE DRIVER_ID = :driver_id", driver_id = requestData[8])
			carInfo = cursor.fetchall()
			if carInfo:
				carInfo = list(carInfo[0])


			cursor.execute("SELECT MESSAGE_TEXT, SENDER, SENDING_TIME FROM MESSAGES WHERE USER_ID = :userId AND DRIVER_ID = :driverId ORDER BY SENDING_TIME DESC FETCH NEXT 50 ROWS ONLY", userId = user_id, driverId = requestData[8])

			messages = cursor.fetchall()

			if messages:
				for i in range(len(messages)):
					messages[i] = list(messages[i])

					if messages[i][1] == 'user':
						messages[i][1] = ''

			messages.reverse()

# ======================================================================= change ======================================================
		##only the next line

		cursor.execute("SELECT LONGITUDE, LATITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id", loc_id = requestData[3])
		for line in cursor:
			requestData.append(list(line))

# ======================================================================= change ======================================================
		##only the next line
		cursor.execute("SELECT LONGITUDE, LATITUDE,  (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id", loc_id = requestData[4])
		for line in cursor:
			requestData.append(list(line))


	cursor.close()
	connection.close()

	return render(request, 'uber/userHomePage.html', {
		'userInfo': userInfo,
		'requestData': requestData,
		'riderInfo' : riderInfo,
		'for_js': for_js,
		'car': carInfo,
        'unratedData': unratedData,
		'messages': messages,
	})

#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,

def driverHomePage(request, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM DRIVER WHERE DRIVER_ID = :driverId", driverId=driver_id)

	checkLst = cursor.fetchall()


	if not checkLst:
		return render(request, 'uber/driverLogin.html')

	#add for showing driver info =====================
	driverInfo = list(checkLst[0])

	if driverInfo[7]:
		driverInfo[7] = round(float(driverInfo[7]) / driverInfo[8], 2)

	if not driverInfo[9]:
		driverInfo[9] = "../../../media/images/dummy.jpg"

	cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE DRIVER_ID = :userId", userId=driver_id)
	nums = []
	for line in cursor:
		nums.append(line[0])

	driverInfo.append(nums)

# ======================================================================= change ======================================================
	##only the next line

	cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id", loc_id = driverInfo[11])

	line = cursor.fetchall()
	driverInfo.append(list(line[0]))

	cursor.execute("SELECT * FROM CAR WHERE DRIVER_ID = :driverId", driverId = driverInfo[0])

	carInfo = cursor.fetchall()
	if carInfo:
		carInfo = list(carInfo[0])
		if carInfo[8] < datetime.now():
			carInfo[8] = ''



	#========end of add for showing driver info==========

	cursor.execute("SELECT * FROM REQUEST WHERE DRIVER_ID = :driverId AND STATUS = :incomp", driverId = driver_id, incomp = 'Incomplete')
	checkLst1 = cursor.fetchall()


	if checkLst1:#accepted request
		requestData = []
		for data in checkLst1:
			requestData = list(data)

		cursor.execute("SELECT * FROM APP_USER WHERE USER_ID = :userId", userId=requestData[7])

		tempData = []  # USER Data
		for line in cursor:
			tempData = (list(line))

		cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE USER_ID = :userId", userId=requestData[7])
		nums = []
		for line in cursor:
			nums.append(line[0])  # adding mobile number to userData

		tempData.append(nums)

		if tempData[7]:
			tempData[7] = round(float(tempData[7]) / tempData[8], 2)

		requestData.append(tempData)  # keeping user Info in request Data
		# at index 9 userInfo and from index 12 of requestData[9] user phone numbers present

		# for pickUP location at index 10 and 11 and destination location

# ======================================================================= change ======================================================
		##only the next line

		cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id",
					   loc_id=requestData[3])
		for line in cursor:
			requestData.append(list(line))

# ======================================================================= change ======================================================
		##only the next line
		cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id",
					   loc_id=requestData[4])
		for line in cursor:
			requestData.append(list(line))

		cursor.execute("SELECT MESSAGE_TEXT, SENDER, SENDING_TIME FROM MESSAGES WHERE USER_ID = :userId AND DRIVER_ID = :driverId ORDER BY SENDING_TIME DESC FETCH NEXT 50 ROWS ONLY",
			userId=requestData[9][0], driverId=driver_id)

		messages = cursor.fetchall()

		if messages:
			for i in range(len(messages)):
				messages[i] = list(messages[i])

				if messages[i][1] == 'driver':
					messages[i][1] = ''

		messages.reverse()


		cursor.close()
		connection.close()

		return render(request, 'uber/driverHomePage.html', {
		'driverInfo': driverInfo,
		'data': requestData,
		'car' : carInfo,
		'messages': messages,
		})

	else:
		# checking for request

		cursor.execute("SELECT * FROM REQUEST WHERE END_TIME >= :end_time AND (DRIVER_ID IS NULL) AND NVL(STATUS, 'dummy') != :status FETCH NEXT 100 ROWS ONLY", end_time=datetime.now(), status = 'Cancelled')
		requestDataTemp = cursor.fetchall()
		requestData = []

		if requestDataTemp:  # requests that are not approved yet
			for data in requestDataTemp:
				requestData.append(list(data))

			i = 0
			for data in requestData:
				cursor.execute("SELECT * FROM APP_USER WHERE USER_ID = :userId", userId=data[7])

				tempData = []  # USER Data
				for line in cursor:
					tempData = (list(line))

				cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE USER_ID = :userId", userId=data[7])
				nums = []
				for line in cursor:
					nums.append(line[0])  # adding mobile number to userData

				tempData.append(nums)

				if tempData[7]:
					tempData[7] = round(float(tempData[7]) / tempData[8], 2)

				requestData[i].append(tempData)  # keeping user Info in request Data
				# at index 9 userInfo and from index 12 of requestData[9] user phone numbers present
				i = i + 1

				# for pickUP location at index 10 and 11 and destination location

# ======================================================================= change ======================================================
				##only the next line

				cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id", loc_id=requestData[i - 1][3])
				for line in cursor:
					requestData[i - 1].append(list(line))

# ======================================================================= change ======================================================
				##only the next line

				cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id", loc_id=requestData[i - 1][4])
				for line in cursor:
					requestData[i - 1].append(list(line))

		cursor.close()
		connection.close()

		return render(request, 'uber/driverHomePage.html', {
			'driverInfo': driverInfo,
			'requestData': requestData,
			'car': carInfo,
		})


#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,

def newRequest(request, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM APP_USER WHERE USER_ID = :userId", userId=user_id)

	checkLst = cursor.fetchall()

	pickupLoc = []
	destLoc = []
	pickupLoc.append(request.POST['lat'])
	pickupLoc.append(request.POST['lon'])
	destLoc.append(request.POST['destlat'])
	destLoc.append(request.POST['destlon'])

	errorLst = []
	dis = Functions.getDistance(float(pickupLoc[0]), float(pickupLoc[1]), float(destLoc[0]), float(destLoc[1]))

	if dis < 1.5:
		errorLst.append("Distance must be greater than 1.5km!")

	for error in errorLst:
		if error:
			return render(request, 'uber/userHomePage.html', {
				'userInfo': checkLst[0],
				'errorLst': errorLst,
				'pickupLoc': pickupLoc,
				'destLoc': destLoc,
			})

	cursor.close()
	connection.close()
	#search locations


	pickupLoc.append(Functions.getLocationDB(float(pickupLoc[0]), float(pickupLoc[1]))[0])
	destLoc.append(Functions.getLocationDB(float(destLoc[0]), float(destLoc[1]))[0])

	# now add a request

	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("INSERT INTO REQUEST (START_TIME, END_TIME, PICK_UP_LOCATION_ID, DESTINATION_LOCATION_ID, APPROX_FARE, USER_ID) VALUES (:start_time, :end_time, :pickup_loc_id, :dest_loc_id, ROUND(:approx_fare, 0), :user_id)", [datetime.now(), datetime.now() + timedelta(minutes = 10), pickupLoc[2], destLoc[2], dis * 30, checkLst[0][0]])

	connection.commit()

	return HttpResponseRedirect(reverse('uber:userHomePage', args=(checkLst[0][0],)))

#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,userCancelRequest


def acceptRequest(request, request_id, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT REQUEST_ID FROM REQUEST WHERE REQUEST_ID = :req_id AND END_TIME >= :end_time AND STATUS IS NULL", req_id = request_id, end_time=datetime.now())

	checkLst = cursor.fetchall()

	if checkLst:
		cursor.execute("UPDATE REQUEST SET DRIVER_ID = :driverId, STATUS = :incomp WHERE REQUEST_ID = :req_id", driverId=driver_id, incomp = 'Incomplete', req_id = request_id)
		connection.commit()


	return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driver_id,)))


#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,userCancelRequest, driverCancelRequest,

def userCancelRequest(request, request_id, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT REQUEST_ID FROM REQUEST WHERE REQUEST_ID = :req_id", req_id = request_id)
	data = cursor.fetchall()

	if data:
		cursor.execute("UPDATE REQUEST SET STATUS = :status WHERE REQUEST_ID = :req_id", status = 'Cancelled', req_id = request_id)
		connection.commit()

	cursor.close()
	connection.close()

	return HttpResponseRedirect(reverse('uber:userHomePage', args=(user_id,)))


#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,userCancelRequest, driverCancelRequest,userDeleteAccount,


def driverCancelRequest(request, request_id, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT REQUEST_ID FROM REQUEST WHERE REQUEST_ID = :req_id", req_id=request_id)
	data = cursor.fetchall()

	if data:
		cursor.execute("UPDATE REQUEST SET STATUS = :status WHERE REQUEST_ID = :req_id", status='Cancelled', req_id=request_id)
		connection.commit()

	cursor.close()
	connection.close()

	return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driver_id,)))

#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,userCancelRequest, driverCancelRequest,userDeleteAccount, rentCar

def userDeleteAccount(request, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM APP_USER WHERE USER_ID = :userId", userId = user_id)
	connection.commit()

	cursor.close()
	connection.close()

	return HttpResponseRedirect(reverse('uber:index'))


def driverDeleteAccount(request, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM DRIVER WHERE DRIVER_ID = :driverId", driverId = driver_id)
	connection.commit()

	cursor.close()
	connection.close()

	return HttpResponseRedirect(reverse('uber:index'))


def adminDeleteAccount(request, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM ADMIN WHERE ADMIN_ID = :adminId", adminId = admin_id)
	connection.commit()

	cursor.close()
	connection.close()

	return HttpResponseRedirect(reverse('uber:index'))


#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,userCancelRequest, driverCancelRequest,userDeleteAccount, rentCar, userCarInfo

def rentCar(request, user_id):
	'''a user place a rent car request here,,, redirects to userHomePage after completion

	:param request:
	:param user_id:
	:return: rentCar.html, userHomePage.html
	'''

	if request.method == "POST":

		admin = ''

		if 'admin' in request.POST:
			admin = request.POST['admin']
			admin = int(admin)
			#print('admin', admin)
			if 'namePlate' not in request.POST:
				return render(request, 'uber/rentCar.html', {'admin': admin,})

		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		inputLst = []
		errorLst = []
		inputLst.append(request.POST['namePlate'])
		inputLst.append(request.POST['model'])
		inputLst.append(request.POST['color'])

		for i in range(3):
			inputLst[i] = inputLst[i].strip()

		inputLst.append(request.POST['ins_type'])

		if len(inputLst[0]) > 30 or len(inputLst[0]) < 1:
			errorLst.append("Name Plate too long or too short!")
		else:
			cursor.execute("SELECT NAME_PLATE FROM CAR WHERE NAME_PLATE = :namePlate", namePlate = inputLst[0])
			carData = cursor.fetchall()
			if carData:
				errorLst.append("Name Plate already exists for another car!")

		if len(inputLst[1]) > 40:
			errorLst.append("Car model too long!")
		if len(inputLst[2]) > 30:
			errorLst.append("Color Name too long!")

		hasImage = False

		if 'document' in request.FILES:
			hasImage = True

		if hasImage:
			image_file = request.FILES['document']

		if hasImage:
			errorLst.extend(Functions.isValid_image(image_file.name))

		isOK = True
		for val in errorLst:
			if val:
				isOK = False
				break

		if not isOK:
			return render(request, 'uber/rentCar.html', {
				'inputLst': inputLst,
				'errorLst': errorLst,
				'userId' : user_id,
				'admin' : admin,
			})

		if hasImage:
			fs = FileSystemStorage()
			image_file_name = fs.save('images/' + image_file.name, image_file)
			url = fs.url(image_file_name)
			urlDB = '../../../..' + url
			inputLst.append(urlDB)  # at index 4
		else:
			inputLst.append('')

        #initially last_payment_date would be null
        #we have added that to see info on admin site at development time, but it won't affect anything

		years = 0
		if inputLst[3] == 'Annual':
			years = 1
		elif inputLst[3] == 'Biennial':
			years = 2
		else:
			years = 5

		if admin:
			cursor.execute("INSERT INTO CAR (NAME_PLATE, MODEL, COLOR, PHOTO, INS_TYPE, INS_START_DATE, INS_END_DATE) VALUES (:name_plate, :model, :color, :photo, :ins_type, :ins_start_date, :ins_end_date)",[inputLst[0], inputLst[1], inputLst[2], inputLst[4], inputLst[3], datetime.now(), datetime.now() + timedelta(days= 365 * years)])
		else:
			cursor.execute("INSERT INTO CAR (NAME_PLATE, MODEL, COLOR, PHOTO, OWNER_USER_ID, INS_TYPE) VALUES (:name_plate, :model, :color, :photo, :owner_id, :ins_type)",[inputLst[0], inputLst[1], inputLst[2], inputLst[4], user_id, inputLst[3]])

		connection.commit()

		if admin:
			return HttpResponseRedirect(reverse('uber:adminHomePage', args=(admin,)))
		else:
			return HttpResponseRedirect(reverse('uber:userHomePage', args=(user_id,)))



	return render(request, 'uber/rentCar.html', {'userId': user_id,})


#index,adminSignUp,adminLogin, adminHomePage, userSignUp,driverSignUp, userLogin, driverLogin, userHomePage, driverHomePage, newRequest,
#acceptRequest,userCancelRequest, driverCancelRequest,userDeleteAccount, rentCar, userCarInfo, userDeleteCar

def userCarInfo(request, user_id):

	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT * FROM CAR WHERE OWNER_USER_ID = :owner",owner = user_id)

	carLst = cursor.fetchall()

	if carLst:

		for i in range(len(carLst)):
			carLst[i] = list(carLst[i])
			if carLst[i][9]:
				if carLst[i][6] == 'Annual':
					monthlyRent = 10000
				elif carLst[i][6] == 'Biennial':
					monthlyRent = 12000
				else:
					monthlyRent = 15000

				today = datetime.today()
				last_payment_day = carLst[i][9]
				dif = today - last_payment_day
				carLst[i][9] = round(monthlyRent * dif.days * 1.0/ 30)
				if carLst[i][8] < datetime.now():
					carLst[i][8] = ''

	return render(request, 'uber/userCarInfo.html', {
		'inputLst' : carLst,
		'userId' : user_id,
	})


def userDeleteCar(request, nameplate, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT NAME_PLATE FROM CAR WHERE OWNER_USER_ID = :owner AND NAME_PLATE = :name_plate", owner = user_id, name_plate = nameplate)

	lst = cursor.fetchall()

	if lst:
		cursor.execute("DELETE FROM CAR WHERE OWNER_USER_ID = :owner AND NAME_PLATE = :name_plate", owner = user_id, name_plate = nameplate)
		connection.commit()

	return HttpResponseRedirect(reverse('uber:userCarInfo', args=(user_id,)))


def carRentRequest(request, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT * FROM CAR WHERE INS_START_DATE IS NULL AND OWNER_USER_ID IS NOT NULL")

	carLst = cursor.fetchall()

	if carLst:
		for i in range(len(carLst)):
			carLst[i] = list(carLst[i])
			cursor.execute("SELECT * FROM APP_USER WHERE USER_ID = :user_id", user_id=carLst[i][4])
			userInfo = cursor.fetchall()

			if userInfo:
				# add for showing user info =====================
				userInfo = list(userInfo[0])

				if not userInfo[9]:
					userInfo[9] = "../../../media/images/dummy.jpg"

				cursor.execute("SELECT MOBILE_NUMBER FROM MOBILE_NUMBERS WHERE USER_ID = :userId", userId=userInfo[0])
				nums = []
				for line in cursor:
					nums.append(line[0])

				userInfo.append(nums) #mobile numbers at index 12
				# ======================================================================= change ======================================================
				##only the next line
				cursor.execute("SELECT LATITUDE, LONGITUDE, (STREET || ' ' || CITY) AS LOC FROM LOCATION WHERE LOCATION_ID = :loc_id",loc_id=userInfo[11])

				line = cursor.fetchall()
				userInfo.append(list(line[0])) #at index 13 location info

				carLst[i].append(userInfo) #at index 10 of carLst

				# ========end of add for showing user info==========

	return render(request, 'uber/carRentRequest.html', {
		'carLst': carLst,
		'userId': admin_id,
	})


def adminApproveCar(request, nameplate, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT NAME_PLATE, INS_START_DATE, INS_TYPE FROM CAR WHERE NAME_PLATE = :name_plate", name_plate = nameplate)

	carData = cursor.fetchall()

	if carData:
		carData = list(carData[0])

		if not carData[1]:
			insEndDate = datetime.now()

			if carData[2] == 'Annual':
				insEndDate = insEndDate + timedelta(days=365)
			elif carData[2] == 'Biennial':
				insEndDate = insEndDate + timedelta(days=365 * 2)
			else:
				insEndDate = insEndDate + timedelta(days=365 * 5)

			cursor.execute("UPDATE CAR SET INS_START_DATE = :insStartDate, INS_END_DATE = :ins_end_date, LAST_PAYMENT_DATE = :lastPaymentDate WHERE NAME_PLATE = :name_plate", [datetime.now(), insEndDate, datetime.now(), nameplate])
			connection.commit()


	return HttpResponseRedirect(reverse('uber:carRentRequest', args=(admin_id,)))


def adminDeleteRequest(request, nameplate, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT NAME_PLATE FROM CAR WHERE NAME_PLATE = :name_plate",
				   name_plate=nameplate)

	carData = cursor.fetchall()

	if carData:
		carData = list(carData[0])
		cursor.execute("DELETE FROM CAR WHERE NAME_PLATE = :namePlate", namePlate = nameplate)
		connection.commit()

	return HttpResponseRedirect(reverse('uber:carRentRequest', args=(admin_id,)))


def driverPickCar(request, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	if request.method == "POST":
		nameplate = request.POST['namePlate']
		cursor.execute("SELECT DRIVER_ID, NAME_PLATE FROM CAR WHERE NAME_PLATE = :name_plate", name_plate = nameplate)

		carData = cursor.fetchall()
		if carData and not carData[0][0]:

			cursor.execute("SELECT NAME_PLATE FROM CAR WHERE DRIVER_ID = :driverId", driverId = driver_id)
			carData = cursor.fetchall()
			if carData:
				cursor.execute("UPDATE CAR SET DRIVER_ID = NULL WHERE DRIVER_ID = :driverId", driverId = driver_id)

			cursor.execute("UPDATE CAR SET DRIVER_ID = :driverId WHERE NAME_PLATE = :name_plate", driverId = driver_id, name_plate = nameplate)
			connection.commit()

		return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driver_id,)))

	else:
		cursor.execute("SELECT * FROM CAR WHERE DRIVER_ID IS NULL AND NVL(INS_END_DATE, SYSDATE - INTERVAL '10' YEAR) > :now", now = datetime.now())

		carLst = cursor.fetchall()
		if carLst:
			for i in range(len(carLst)):
				carLst[i] = list(carLst[i])

		return render(request, 'uber/driverPickCar.html', {
			'driverId': driver_id,
			'carLst': carLst,
		})


def driverRateUser(request, request_id, driver_id):
	return render(request, 'uber/driverRateUser.html', {
		'requestId': request_id,
		'driverId': driver_id,
	})

def completeJourney(request, request_id, driver_id):
	if request.method == "POST":
		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		if 'rating' in request.POST:
			rating = request.POST["rating"]

			if not(rating == "0"):
				cursor.execute("SELECT USER_ID FROM REQUEST WHERE REQUEST_ID = :req_id", req_id = request_id)
				userData = cursor.fetchall()

				if userData:
					cursor.execute("UPDATE APP_USER SET TOTAL_RATING = NVL(TOTAL_RATING, 0) + (:newRating), NUM_OF_RATING = NVL(NUM_OF_RATING, 0) + 1 WHERE USER_ID = :userID", newRating = rating, userID = userData[0][0])
					connection.commit()

		else:
			cursor.execute("UPDATE REQUEST SET STATUS = :status, END_TIME = :endTime WHERE REQUEST_ID = :req_id",
						   status='Complete', endTime=datetime.now(), req_id=request_id)
			connection.commit()

			return render(request, 'uber/driverRateUser.html', {
				'requestId': request_id,
				'driverId': driver_id,
			})


	return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driver_id,)))


def userCancelRate(request, user_id, request_id):
	connection= cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT REQUEST_ID FROM REQUEST WHERE USER_ID = :userID AND REQUEST_ID = :req_id", userID = user_id, req_id = request_id)

	data = cursor.fetchall()

	if data:
		cursor.execute("UPDATE REQUEST SET STATUS = :status WHERE REQUEST_ID = :req_id", status = "Rated",req_id = request_id)
		connection.commit()

	return HttpResponseRedirect(reverse('uber:userHomePage', args=(user_id,)))


def userRateDriver(request, user_id, request_id, driver_id):
	if request.method == "POST":
		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT REQUEST_ID FROM REQUEST WHERE USER_ID = :userID AND REQUEST_ID = :req_id",
					   userID=user_id, req_id=request_id)

		data = cursor.fetchall()

		if data:
			cursor.execute("UPDATE REQUEST SET STATUS = :status WHERE REQUEST_ID = :req_id", status="Rated",
						   req_id=request_id)
			connection.commit()

		if 'rating' in request.POST:
			rating = request.POST["rating"]



			if not(rating == "0"):
				cursor.execute("SELECT DRIVER_ID FROM REQUEST WHERE REQUEST_ID = :req_id", req_id = request_id)
				userData = cursor.fetchall()

				if userData:
					cursor.execute("UPDATE DRIVER SET TOTAL_RATING = NVL(TOTAL_RATING, 0) + (:newRating), NUM_OF_RATING = NVL(NUM_OF_RATING, 0) + 1 WHERE DRIVER_ID = :userID", newRating = rating, userID = driver_id)
					connection.commit()

		else:
			return render(request, 'uber/userRateDriver.html', {
				'requestId': request_id,
				'driverId': driver_id,
				'userId': user_id,
			})


	return HttpResponseRedirect(reverse('uber:userHomePage', args=(user_id,)))


def adminPayCar(request, nameplate, admin_id):
	if request.method == "POST":
		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT ADMIN_ID FROM ADMIN WHERE ADMIN_ID = :adminId", adminId = admin_id)

		data = cursor.fetchall()
		if data:

			cursor.execute("SELECT NAME_PLATE FROM CAR WHERE NAME_PLATE = :name_plate AND LAST_PAYMENT_DATE < :last_payment_date", name_plate = nameplate, last_payment_date = datetime.now() - timedelta(days=30))

			data = cursor.fetchall()

			if data:
				cursor.execute("UPDATE CAR SET LAST_PAYMENT_DATE = :last_payment_date WHERE NAME_PLATE = :name_plate", last_payment_date = datetime.now(), name_plate=nameplate)
				connection.commit()


			return  HttpResponseRedirect(reverse('uber:adminHomePage', args=(admin_id,)))



		return HttpResponseRedirect(reverse('uber:adminLogin'))



def userMessageDriver(request, user_id, driver_id):
	if request.method == "POST":
		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT DRIVER_ID FROM DRIVER WHERE DRIVER_ID = :driverId", driverId = driver_id)

		data = cursor.fetchall()

		if data:
			message = request.POST["message"]
			message = message.strip()

			if message:
				cursor.execute("INSERT INTO MESSAGES (MESSAGE_TEXT, USER_ID, DRIVER_ID, SENDER, SENDING_TIME) VALUES(:text, :userId, :driverId, :sender, :sending_time)", [message, user_id, driver_id, 'user', datetime.now()])
				connection.commit()

	return HttpResponseRedirect(reverse('uber:userHomePage', args=(user_id,)))


def driverMessageUser(request, driver_id, user_id):
	if request.method == "POST":
		connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
		cursor = connection.cursor()

		cursor.execute("SELECT USER_ID FROM APP_USER WHERE USER_ID = :userId", userId = user_id)

		data = cursor.fetchall()

		if data:
			message = request.POST["message"]
			message = message.strip()

			if message:
				cursor.execute("INSERT INTO MESSAGES (MESSAGE_TEXT, USER_ID, DRIVER_ID, SENDER, SENDING_TIME) VALUES(:text, :userId, :driverId, :sender, :sending_time)", [message, user_id, driver_id, 'driver', datetime.now()])
				connection.commit()

	return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driver_id,)))



def userRideHistory(request, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	rows = 0
	More = 0
	Ended = ''

	if request.method == "POST":
		if 'More' in request.POST:
			rows = request.POST['More']
			rows = int(rows)
			More = rows + 1

	rows = rows + 1
	rows = rows * 10

	cursor.execute("SELECT END_TIME, LOCATION_STRING(PICK_UP_LOCATION_ID), LOCATION_STRING(DESTINATION_LOCATION_ID), APPROX_FARE, DRIVER_ID, DRIVER_NAME(DRIVER_ID) FROM REQUEST WHERE USER_ID = :userId AND STATUS IN ('Complete', 'Rated') ORDER BY END_TIME DESC FETCH NEXT :row_num ROWS ONLY", userId = user_id, row_num = rows)

	data = cursor.fetchall()
	if len(data) < rows:
		Ended = "YES"

	cursor.execute("SELECT USER_ID FROM APP_USER WHERE USER_ID = :userId", userId = user_id)

	userData = cursor.fetchall()
	if userData:
		return render(request, 'uber/userRideHistory.html', {
			'userId': user_id,
			'rides': data,
			'More': More,
			'Ended': Ended,
		})
	else:
		return render(request, 'uber/userLogin.html')


def userDriverInfo(request, user_id, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT NVL(PHOTO, :dummy), DRIVER_NAME(DRIVER_ID), USERNAME, EMAIL, DRIVER_RATING(DRIVER_ID), NUM_OF_RATING, DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID) FROM DRIVER WHERE DRIVER_ID = :driverId", dummy = '../../../../media/images/dummy.jpg', driverId = driver_id)
	data = cursor.fetchall()

	if data:

		data = list(data[0])
		data.append(Functions.driver_mobileNumbers(driver_id))

		return render(request, 'uber/userDriverInfo.html', {
			'userId': user_id,
			'driverInfo': data,
		})

	return HttpResponseRedirect(reverse('uber:userRideHistory', args=(user_id,)))


def driverRideHistory(request, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	rows = 0
	More = 0
	Ended = ''

	if request.method == "POST":
		if 'More' in request.POST:
			rows = request.POST['More']
			rows = int(rows)
			More = rows + 1

	rows = rows + 1
	rows = rows * 10

	cursor.execute("SELECT END_TIME, LOCATION_STRING(PICK_UP_LOCATION_ID), LOCATION_STRING(DESTINATION_LOCATION_ID), APPROX_FARE, USER_ID, USER_NAME(USER_ID) FROM REQUEST WHERE DRIVER_ID = :userId AND STATUS IN ('Complete', 'Rated') ORDER BY END_TIME DESC FETCH NEXT :row_num ROWS ONLY", userId = driver_id, row_num = rows)

	data = cursor.fetchall()
	if len(data) < rows:
		Ended = "YES"

	cursor.execute("SELECT DRIVER_ID FROM DRIVER WHERE DRIVER_ID = :userId", userId = driver_id)

	userData = cursor.fetchall()
	if userData:
		return render(request, 'uber/driverRideHistory.html', {
			'driverId': driver_id,
			'rides': data,
			'More': More,
			'Ended': Ended,
		})
	else:
		return render(request, 'uber/driverLogin.html')


def driverUserInfo(request, driver_id, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT NVL(PHOTO, :dummy), USER_NAME(USER_ID), USERNAME, EMAIL, USER_RATING(USER_ID), NUM_OF_RATING, DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID) FROM APP_USER WHERE USER_ID = :driverId", dummy = '../../../../media/images/dummy.jpg', driverId = user_id)
	data = cursor.fetchall()

	if data:

		data = list(data[0])
		data.append(Functions.user_mobileNumbers(user_id))

		return render(request, 'uber/driverUserInfo.html', {
			'driverId': driver_id,
			'driverInfo': data,
		})
	#driverInfo contains userInfo

	return HttpResponseRedirect(reverse('uber:driverRideHistory', args=(driver_id,)))


def updateInsurance(request, nameplate, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("SELECT NAME_PLATE FROM CAR WHERE NAME_PLATE = :name_plate AND OWNER_USER_ID = :userId", name_plate = nameplate, userId = user_id)

	data = cursor.fetchall()

	if data:
		cursor.execute("UPDATE CAR SET INS_START_DATE = NULL WHERE NAME_PLATE = :name_plate", name_plate = nameplate)
		connection.commit()

	return HttpResponseRedirect(reverse('uber:userCarInfo', args=(user_id,)))


def adminDeleteMobile(request, mob_num, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mobNum AND ADMIN_ID = :adminId AND DRIVER_ID IS NULL AND USER_ID IS NULL", mobNum = mob_num, adminId = admin_id)
	connection.commit()
	cursor.execute("UPDATE MOBILE_NUMBERS SET ADMIN_ID = NULL WHERE ADMIN_ID = :adminId AND MOBILE_NUMBER = :mobNum", adminId = admin_id, mobNum = mob_num)
	connection.commit()

	return HttpResponseRedirect(reverse('uber:adminHomePage', args=(admin_id,)))


def userDeleteMobile(request, mob_num, user_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute(
		"DELETE FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mobNum AND USER_ID = :adminId AND DRIVER_ID IS NULL AND ADMIN_ID IS NULL",
		mobNum=mob_num, adminId=user_id)
	connection.commit()
	cursor.execute("UPDATE MOBILE_NUMBERS SET USER_ID = NULL WHERE USER_ID = :adminId AND MOBILE_NUMBER = :mobNum",
				   adminId=user_id, mobNum=mob_num)
	connection.commit()

	return HttpResponseRedirect(reverse('uber:userHomePage', args=(user_id,)))


def driverDeleteMobile(request, mob_num, driver_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute(
		"DELETE FROM MOBILE_NUMBERS WHERE MOBILE_NUMBER = :mobNum AND DRIVER_ID = :adminId AND ADMIN_ID IS NULL AND USER_ID IS NULL",
		mobNum=mob_num, adminId=driver_id)
	connection.commit()
	cursor.execute("UPDATE MOBILE_NUMBERS SET DRIVER_ID = NULL WHERE DRIVER_ID = :adminId AND MOBILE_NUMBER = :mobNum",
				   adminId=driver_id, mobNum=mob_num)
	connection.commit()

	return HttpResponseRedirect(reverse('uber:driverHomePage', args=(driver_id,)))


def carInfoAdmin(request, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	search = ''

	if 'namePlate' in request.POST:
		namePlate = request.POST['namePlate']
		namePlate = namePlate.strip()

		cursor.execute("SELECT NAME_PLATE, MODEL, OWNER_USER_ID, USER_NAME(OWNER_USER_ID), INS_TYPE, INS_END_DATE, LAST_PAYMENT_DATE FROM CAR WHERE NAME_PLATE = :name_plate", name_plate = namePlate)
		data = cursor.fetchall()

		search = "YES"

	More = ''
	rows = 10
	Ended = ''

	if 'More' in request.POST:
		More = request.POST['More']
		More = int(More)
		rows = More + 1
		rows = rows * 10
		More = More + 1

	if not search:
		cursor.execute("SELECT NAME_PLATE, MODEL, OWNER_USER_ID, USER_NAME(OWNER_USER_ID), INS_TYPE, INS_END_DATE, LAST_PAYMENT_DATE FROM CAR FETCH NEXT :row_num ROWS ONLY", row_num = rows)
		data = cursor.fetchall()

	if data:
		for i in range(len(data)):
			data[i] = list(data[i])
			for j in range(len(data[i])):
				if not data[i][j] and j != 2:
					data[i][j] = '-'


	if len(data) < rows:
		Ended = "OK"


	return render(request, 'uber/carInfoAdmin.html', {
		'data': data,
		'More': More,
		'userId': admin_id,
		'search': search,
		'Ended': Ended,
	})


def adminDeleteCar(request, nameplate, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM CAR WHERE NAME_PLATE = :namePlate", namePlate = nameplate)
	connection.commit()

	return HttpResponseRedirect(reverse('uber:carInfoAdmin', args=(admin_id,)))


def userInfoAdmin(request, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	search = ''

	if 'userName' in request.POST:
		userName = request.POST['userName']
		userName = userName.strip()

		cursor.execute("SELECT USER_NAME(USER_ID), USERNAME, EMAIL, USER_RATING(USER_ID), DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID), USER_ID, NUM_OF_RATING FROM APP_USER WHERE USERNAME = :username OR FIRST_NAME = :firstName", username=userName, firstName = userName)
		data = cursor.fetchall()

		search = "YES"

	More = ''
	rows = 10
	Ended = ''

	if 'More' in request.POST:
		More = request.POST['More']
		More = int(More)
		rows = More + 1
		rows = rows * 10
		More = More + 1

	if not search:
		cursor.execute("SELECT USER_NAME(USER_ID), USERNAME, EMAIL, USER_RATING(USER_ID), DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID), USER_ID, NUM_OF_RATING FROM APP_USER FETCH NEXT :row_num ROWS ONLY", row_num = rows)

		data = cursor.fetchall()

	if data:
		for i in range(len(data)):
			data[i] = list(data[i])


	if len(data) < rows:
		Ended = "OK"


	return render(request, 'uber/userInfoAdmin.html', {
		'data': data,
		'More': More,
		'userId': admin_id,
		'search': search,
		'Ended': Ended,
	})


def adminDeleteUser(request, user_id, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM APP_USER WHERE USER_ID = :userId", userId = user_id)
	connection.commit()

	return HttpResponseRedirect(reverse('uber:userInfoAdmin', args=(admin_id,)))


def driverInfoAdmin(request, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	search = ''

	if 'userName' in request.POST:
		userName = request.POST['userName']
		userName = userName.strip()

		cursor.execute("SELECT DRIVER_NAME(DRIVER_ID), USERNAME, EMAIL, DRIVER_RATING(DRIVER_ID), DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID), DRIVER_ID, NUM_OF_RATING FROM DRIVER WHERE USERNAME = :username OR FIRST_NAME = :firstName", username=userName, firstName = userName)
		data = cursor.fetchall()

		search = "YES"

	More = ''
	rows = 10
	Ended = ''

	if 'More' in request.POST:
		More = request.POST['More']
		More = int(More)
		rows = More + 1
		rows = rows * 10
		More = More + 1

	if not search:
		cursor.execute("SELECT DRIVER_NAME(DRIVER_ID), USERNAME, EMAIL, DRIVER_RATING(DRIVER_ID), DATE_OF_BIRTH, LOCATION_STRING(LOCATION_ID), DRIVER_ID, NUM_OF_RATING FROM DRIVER FETCH NEXT :row_num ROWS ONLY", row_num = rows)

		data = cursor.fetchall()

	if data:
		for i in range(len(data)):
			data[i] = list(data[i])


	if len(data) < rows:
		Ended = "OK"


	return render(request, 'uber/driverInfoAdmin.html', {
		'data': data,
		'More': More,
		'userId': admin_id,
		'search': search,
		'Ended': Ended,
	})


def adminDeleteDriver(request, driver_id, admin_id):
	connection = cx_Oracle.connect("SYSTEM/oracle@localhost/orcl")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM DRIVER WHERE DRIVER_ID = :userId", userId = driver_id)
	connection.commit()

	return HttpResponseRedirect(reverse('uber:driverInfoAdmin', args=(admin_id,)))