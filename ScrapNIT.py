'''
Author:     Deepak Chauhan
Github:     https://github.com/royaleagle73
Linkedin :  https://www.linkedin.com/in/deepakchauhan878
'''
import sys
import json
import requests
from bs4 import BeautifulSoup
from configparser import ConfigParser

class resultLeecher():
    def __init__(self):
        self.parser = ConfigParser()
        self.parser.read('config.ini')
        self.url = self.parser.get('Connection','url')
        self.departmentName = ""
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
        self.studentData = {
            "classRank":-1,
            "rollNo":"",
            "nameOfStudent": "",
            "fathersName":"",
            "departmentName":"",
            "finalCGPA":"",
            "lastSemester":0,
            "collegeID":0,
            "gradeCardURL":"",
            "result":{}
            }
        
    def extractRollLimit(self,lastRollNumber):
        for i in range(5,len(lastRollNumber)):
            if(lastRollNumber[i].isnumeric()==True):
                return i
        
    def getSemesterResult(self,url,semester):
        self.postData["ddlSemester"] = semester
        result = {
                "SGPA":0
        }
        responseData = requests.post(url, data = self.postData).text
        soup = BeautifulSoup(responseData, "lxml")
        # Getting father's name
        if self.studentData["fathersName"]=="":
            self.studentData["fathersName"] = soup.find("span", attrs={"id":"lblFatherName"}).text
        # Getting SGPA and updating CGPA
        result["SGPA"] = soup.find("span", attrs={"id":"lblSPI"}).text
        self.studentData["finalCGPA"] = soup.find("span", attrs={"id":"lblCPI"}).text
        # Getting subject data, marks, grades and marks
        resultTableRows = soup.find("table", border=1, cellspacing=0, cellpadding=0).find_all("tr")
        for i in range(1,len(resultTableRows)):
            columns = resultTableRows[i].find_all("td")
            if len(columns)==10:
                result[columns[1].text.strip()] = {
                            "subjectCode":  columns[0].text.strip(),
                            "totalMarks": columns[8].text.strip(),
                            "grade": columns[9].text.strip()
                        }
        return result


    def collectResult(self):
        for semester in range(1,self.studentData["lastSemester"]+1):
            self.studentData["result"][str(semester)] = self.getSemesterResult(self.url,semester)

    def getStudentData(self,rollNo):
        self.studentData["fathersName"]=""
        self.studentData["rollNo"] = rollNo
        self.postData["txtRegno"] = rollNo
        responseData = requests.post(self.url, data=self.postData).text
        soup = BeautifulSoup(responseData,"lxml")
        self.studentData["nameOfStudent"] = soup.find("span", attrs={"id":"lblSName"}).text
        if len(self.studentData["nameOfStudent"])==0:
            return -1
        self.studentData["lastSemester"] = int(soup.find_all("option")[-1]["value"])
        self.studentData["departmentName"] = soup.find("span", attrs={"id":"lblSBranch"}).text
        self.studentData["collegeID"] = int(soup.find("input", attrs={"id":"hfIdno"})["value"])
        self.studentData["gradeCardURL"] = "http://122.252.250.250/StudentPortal/commanreport.aspx?pagetitle=gradecarde&path=crptNewGradecard.rpt&param=@P_IDNO="+str(self.studentData["collegeID"])+",@P_SEMESTERNO=4,@P_COLLEGE_CODE=11"

        # getting data ready for advance extraction
        self.postData["ddlSemester"] = self.studentData["lastSemester"]
        self.postData["hfIdno"] = self.studentData["collegeID"]
        self.postData["btnimgShowResult.x"] = 50
        self.postData["btnimgShowResult.y"] = 4 
        self.postData["__VIEWSTATE"] = soup.find("input", attrs={"id":"__VIEWSTATE"})["value"]
        
        del self.postData["btnimgShow.x"]
        del self.postData["btnimgShow.y"]
        
        self.collectResult()
        
        self.postData["btnimgShow.x"] = 23
        self.postData["btnimgShow.y"] = 8
        del self.postData["btnimgShowResult.x"]
        del self.postData["btnimgShowResult.y"]
        if(self.departmentName==""):
            self.departmentName = self.studentData["departmentName"]
        return self.studentData

    def classData(self,lastRollNumber):
        classResult = dict()
        rollPrefix = lastRollNumber[ :self.extractRollLimit(lastRollNumber)]
        lastRollNumber = int(lastRollNumber[self.extractRollLimit(lastRollNumber):])
        numOfZeros = len(str(lastRollNumber)) - 1
        for rollNumber in range(1,lastRollNumber+1):
            currentRollNumber = rollPrefix+ "0"*(numOfZeros-len(str(rollNumber))+1) +str(rollNumber)
            print("Checking result for " + currentRollNumber)
            data = self.getStudentData(currentRollNumber)
            if data!=-1:
                classResult[str(currentRollNumber)] = data.copy()
        rank_chart_data = self.classRankGenerator(classResult)
        # Writing Rank Chart
        with open( "(Rank Chart) " + rollPrefix[:4]+ " - " + self.departmentName + ".csv", "w") as file:
            file.write(rank_chart_data)
        # Writing Data roll no wise
        with open( rollPrefix[:4]+ " - " + self.departmentName + ".json", "w") as file:
            json.dump(classResult, file,indent=4)
        # Writing Data rank wise
        with open( "(CGPA Sorted) " + rollPrefix[:4]+ " - " + self.departmentName + ".json", "w") as file:
            classResult ={x:classResult[x] for x in sorted(classResult,key=lambda e: classResult[e]['finalCGPA'], reverse=True)}
            json.dump(classResult, file,indent=4)

    def classRankGenerator(self,classResult):
        rank_chart_data = "Class Rank,Roll No,Name,CGPA\n"
        applied_rank = 0
        real_rank = 0
        last_cgpa = 0
        sorted_keys = sorted(classResult,key=lambda e: classResult[e]['finalCGPA'],reverse=True)
        for key in sorted_keys:
            if classResult[key]['finalCGPA'] != last_cgpa:
                applied_rank = real_rank+1
                last_cgpa = classResult[key]['finalCGPA']
            classResult[key]['classRank'] = applied_rank
            rank_chart_data += ','.join([str(applied_rank),key,classResult[key]['nameOfStudent'],str(classResult[key]['finalCGPA'])])+"\n"
            real_rank+=1
        return rank_chart_data

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