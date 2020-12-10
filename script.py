import sys
import json
import requests
from bs4 import BeautifulSoup

class resultLeecher():
    def __init__(self):
        self.postData = {
            "ToolkitScriptManager1_HiddenField":"",
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":"/wEPDwULLTE5MTk3NDAxNjkPZBYCAgEPZBYCAicPZBYEAhIPFCsAAmRkZAIUD2QWAgIDDxQrAAJkZGQYAwUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgQFCmJ0bmltZ1Nob3cFEGJ0bmltZ1Nob3dSZXN1bHQFC2J0bkltZ1ByaW50BQxidG5pbWdDYW5jZWwFCWx2QmFja2xvZw9nZAUQbHZTdWJqZWN0RGV0YWlscw9nZEM0w+4vgN3bILbO4Zuep/+vlVWU",
            "txtRegno":"",
            "btnimgShow.x":23,
            "btnimgShow.y":8,
            "ddlSemester":0,
            "hfIdno":"",
            "hdfidno":""
        }

    def extractRollLimit(self,lastRollNumber):
        for i in range(5,len(lastRollNumber)):
            if(lastRollNumber[i].isnumeric()==True):
                return i
        
    def getSemesterResult(self,url,studentData,semester):
        self.postData["ddlSemester"] = semester
        result = {
                "SGPA":0
        }
        responseData = requests.post(url, data = self.postData).text
        soup = BeautifulSoup(responseData, "lxml")
        # Getting father's name
        if studentData["fathersName"]=="":
            studentData["fathersName"] = soup.find("span", attrs={"id":"lblFatherName"}).text
        # Getting SGPA and updating CGPA
        result["SGPA"] = soup.find("span", attrs={"id":"lblSPI"}).text
        studentData["finalCGPA"] = soup.find("span", attrs={"id":"lblCPI"}).text
        # Getting subject data, marks, grades and marks
        resultTableRows = soup.find("table", border=1, cellspacing=0, cellpadding=0).find_all("tr")
        for i in range(1,len(resultTableRows)):
            columns = resultTableRows[i].find_all("td")
            if len(columns)==10:
                result[columns[0].text.strip()] = {
                            "subjectName":  columns[1].text.strip(),
                            "totalMarks": columns[8].text.strip(),
                            "grade": columns[9].text.strip()
                        }
        return result


    def collectResult(self,studentData):
        for semester in range(1,studentData["lastSemester"]+1):
            studentData["result"][str(semester)] = self.getSemesterResult("http://122.252.250.250/StudentPortal/Default.aspx",studentData, semester)

    def getStudentData(self,rollNo):
        self.postData["txtRegno"] = rollNo
        studentData = {
            "rollNo":rollNo,
            "nameOfStudent": "",
            "fathersName":"",
            "departmentName":"",
            "finalCGPA":"",
            "lastSemester":0,
            "collegeID":0,
            "gradeCardURL":"",
            "result":{}
            }
        responseData = requests.post("http://122.252.250.250/StudentPortal/Default.aspx", data=self.postData).text
        soup = BeautifulSoup(responseData,"lxml")
        studentData["nameOfStudent"] = soup.find("span", attrs={"id":"lblSName"}).text
        if len(studentData["nameOfStudent"])==0:
            return -1
        studentData["lastSemester"] = int(soup.find_all("option")[-1]["value"])
        studentData["departmentName"] = soup.find("span", attrs={"id":"lblSBranch"}).text
        studentData["collegeID"] = int(soup.find("input", attrs={"id":"hfIdno"})["value"])
        studentData["gradeCardURL"] = "http://122.252.250.250/StudentPortal/commanreport.aspx?pagetitle=gradecarde&path=crptNewGradecard.rpt&param=@P_IDNO="+str(studentData["collegeID"])+",@P_SEMESTERNO=4,@P_COLLEGE_CODE=11"

        # getting data ready for advance extraction
        self.postData["ddlSemester"] = studentData["lastSemester"]
        self.postData["hfIdno"] = studentData["collegeID"]
        self.postData["btnimgShowResult.x"] = 50
        self.postData["btnimgShowResult.y"] = 4 
        self.postData["__VIEWSTATE"] = soup.find("input", attrs={"id":"__VIEWSTATE"})["value"]
        
        del self.postData["btnimgShow.x"]
        del self.postData["btnimgShow.y"]
        
        self.collectResult(studentData)
        
        self.postData["btnimgShow.x"] = 23
        self.postData["btnimgShow.y"] = 8
        del self.postData["btnimgShowResult.x"]
        del self.postData["btnimgShowResult.y"] 
        return studentData

    def classData(self,lastRollNumber):
        classResult = {}
        rollPrefix = lastRollNumber[ :self.extractRollLimit(lastRollNumber)]
        lastRollNumber = int(lastRollNumber[self.extractRollLimit(lastRollNumber):])
        numOfZeros = len(str(lastRollNumber)) - 1
        for rollNumber in range(1,lastRollNumber+1):
            currentRollNumber = rollPrefix+ "0"*(numOfZeros-len(str(rollNumber))+1) +str(rollNumber)
            print("Checking result for " + currentRollNumber)
            data = self.getStudentData(currentRollNumber)
            if data!=-1:
                classResult[currentRollNumber] = data
        with open(rollPrefix + ".json", "w") as file:
            json.dump(classResult, file)

if __name__ == "__main__":
    leecher = resultLeecher()
    if sys.argv[1] == "-s":
        data = leecher.getStudentData(sys.argv[2])
        if data==-1:
            print("Student Doesn't exit")
        else:
            with open(sys.argv[2]+".json", "w") as file:
                json.dump(data, file)
    elif sys.argv[1] == '-c':
        leecher.classData(sys.argv[2])
    else:
        print("Use only given flags\n-s for single student\n-c for batch of students")