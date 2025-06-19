import sqlite3
import PhoneNumberExtraction

class SqlManager:
    def __init__(self):
        self.phoneNumberExtractor = PhoneNumberExtraction.PhoneNumberExtraction()
        
    def registerCustomer(conn, name, phone, date, time, service, specialistID, notes = 'None'):
        cursor = conn.cursor()
        # Insert data into the 'customerInfo' table
        cursor.execute('''
        INSERT INTO customerInfo (Name, PhoneNumber, State, ReservedDate,ReservedTime, Services, PerferedSpecialistID, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, 'confirm', date, time, service, specialistID, notes))

        # Commit the transaction to save the changes
        conn.commit()

        # Close the connection
        conn.close()

        print("Your reservation has been complete.")

    def checkIfTimeSlotAvaliable(conn, self, date, time):

        cursor = conn.cursor()
        # check the value
        cursor.execute(f"SELECT {date} FROM Teanna_Schedule WHERE Time_Slots = ?", (time,))
        currentValue = cursor.fetchone()

        #optional print
        print(f"Value {date} at {time}: {currentValue[0]} \n")
        
        conn.close()
        
        if(currentValue[0] is None):
            print("Yes, you can book this time!\n")
            return True
        else:
            print("sorry, this time slot is unavaliable!")
            return False


    #date is Column name Monday-Sunday
    def updateDb(self, date, time, customerInfo):
        # Connect to the SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('data/shopData/TestingData.db')

        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        # Update data in the table
        sql = f"UPDATE Teanna_Schedule SET {date} = ? WHERE Time_Slots = ?"
        cursor.execute(sql, (customerInfo, time))

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()


    def cancelSchedule(self, date, time, phoneNumber):
        # Connect to the SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect('data/shopData/TestingData.db')

        # Create a cursor object to interact with the database
        cursor = conn.cursor()
        
        #confirm phoneNumber
        cursor.execute(f"SELECT {date} FROM Teanna_Schedule WHERE Time_Slots = ?", (time,))
        currentValue = cursor.fetchone()
        
        if(phoneNumber == self.phoneNumberExtractor.extract_phone_number(currentValue[0])):
            #Cancel reservation by wiping the info
            self.updateDb(self, date,time,None)
            print('Your reservation has been canceled!')
        else:
            print('Wrong number, please try again')


    #testing code
    #updateDb('Monday', '09:00-10:00','Lux, Delux pedicure 4756874436')
    #checkIfSlotAvaliable('Wensday', '09:00-10:00')


