from PyPDF2 import PdfFileReader, PdfFileWriter
from tika import parser
import re

class QuestionExtractor:
    def __init__(self, additionalQuestionNumberFormList = None, additionalBlackList = None, additionalIgnoreList = None):
        self.minLineSizeToAdd = 2
        self.minQuestionLength = 30
        self.maxQuestionLength = 300
        self.questionNumberFormList = [r"^\d{1,}[.]?", r"^\d{1,}[.]?\s?[[]?\d{1,}[]]?[.]?", r"^\d{1,}[-]\d{1,}\s\d{1,}[.]"]
        self.blackList = ["①", "②", "③", "④", "⑤", "ㄱ.", "ㄴ.", "ㄷ.", "ㄹ.", "ㅁ.", "∴", r"해\s?설", r"출\s?처", "답", r"노\s?하/s?우", r"단\s?계", r"1\s?등\s?급", r"출\s?제", r"문\s?항", r"유\s?형", r"서\s?술\s?형"]
        self.ignoreItemList = [r"교\s?육\s?청", r"수\s?능", r"평\s?가\s?원", r"사\s?관\s?학\s?교", r"기\s?출", r"[[]\s?\d점\s?[]]"]
    
    def getQuestionsInPDF(self, PDFPath):
        pdf = PdfFileReader(open(PDFPath, 'rb'))
        pageFileName = "tmp.pdf"
        questions = list()
        for page in range(pdf.getNumPages()):   
            self.makePageFile(pageFileName, pdf, page)
            questions = questions + self.getQuestionsInPage(pageFileName)
        
        if len(questions) < 10:
            print("재확인 필요: ", PDFPath)
        return questions

    def makePageFile(self, pageFileName, pdfFile, page):
        out = PdfFileWriter()
        out.addPage(pdfFile.getPage(page))
        with open(pageFileName, "wb") as outputStream:
            out.write(outputStream)

    def getQuestionsInPage(self, pageFileName):
        rawData = parser.from_file(pageFileName)
        content = rawData["content"]
        
        if content == None:
            return list()
        content = content.split("\n")
        questions = list()
        currentQuestion = ""
        isReading = False
        
        for line in content:
            filteredLine = self.reduceSpacing(line)
            
            if len(filteredLine) <= self.minLineSizeToAdd or self.isContainsBlackList(filteredLine):
                continue
            
            if self.isStartOfQuestion(filteredLine):
                if isReading:
                    currentQuestion = self.clearifyQuestion(currentQuestion)
                    if self.checkQuestionLength(currentQuestion):
                        questions.append(currentQuestion)
                    currentQuestion = filteredLine
                else:
                    isReading = True
                    currentQuestion = filteredLine
            else:
                if isReading:
                    currentQuestion = currentQuestion + " " + filteredLine

        if self.checkQuestionLength(currentQuestion):
            currentQuestion = self.clearifyQuestion(currentQuestion)
            questions.append(currentQuestion)
        
        return questions

    def checkQuestionLength(self, text):
        return len(text) >= self.minQuestionLength and len(text) <= self.maxQuestionLength

    def isStartOfQuestion(self, text):
        for item in self.questionNumberFormList:
            if re.search(item, text) != None:
                return True
        return False

    def clearifyQuestion(self, text):
        text = self.reduceSpacing(text)
        text = self.removeWord(text)
        text = self.removeQuestionNumber(text)
        return text

    def reduceSpacing(self, text):
        text = text.replace("\t", " ")
        text = text.replace("�", " ")
        splited = text.strip().split(" ")
        result = ""
        for word in splited:
            if word != "":
                result = result + " " + word
        return result.strip()

    def removeQuestionNumber(self, text):
        maxMatchQuestionForm = None
        maxMatchIndex = -1
        for item in self.questionNumberFormList:
            if re.search(item, text) != None:
                currentMatchIndex = re.search(item, text).end()
                if currentMatchIndex > maxMatchIndex:
                    maxMatchQuestionForm = item
                    maxMatchIndex = currentMatchIndex
        
        text = re.sub(maxMatchQuestionForm, "", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text

    def isContainsBlackList(self, text):
        for item in self.blackList:
            if re.search(item, text) != None:
                return True
        return False

    def removeWord(self, text):
        for item in self.ignoreItemList:
            text = re.sub(item, "", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text

if __name__ == "__main__":
    path = "/Users/dev/Desktop/2020년 2학기/딥러닝의 기초/Project/문제집/"
    path = path + "6.도함수의 활용.pdf"
    questionExtractor = QuestionExtractor()
    questions = questionExtractor.getQuestionsInPDF(path)

    for question in questions:
        print(question, "\n")
    print(len(questions), "questions extracted")
